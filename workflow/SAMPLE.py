from data.milvus.indexing import MilvusIndexer
import os
from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

from data.prompts.decision import DECISION_PROMPT
from data.prompts.search_web import SEARCH_WEB_PROMPT
from data.prompts.send_email import SEND_EMAIL_PROMPT
from data.prompts.calendar import CALENDAR_PROMPT
from data.prompts.scheule import SCHEULE_PROMPT
from data.prompts.evaluate_for_email import EVALUATE_PROMPT
    
from datetime import datetime
import chainlit as cl

from utils.basetools import *
from utils.basetools.google_calendar import (create_calendar_event_simple,read_calendar_events)
from utils.basetools.search_student import (get_latest_test_tool_func,)
from utils.safe_calendar import safe_agent_run, get_current_week_dates

# Initialize model and provider
provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel('gemini-2.5-flash', provider=provider)
#---------------------------------------------
# Debug email configuration
print(f"SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
print(f"SENDER_PASSWORD: {'*' * len(os.getenv('SENDER_PASSWORD', '')) if os.getenv('SENDER_PASSWORD') else 'Not set'}")

send_email = create_send_email_tool(
    to_emails=["dung.phank24@hcmut.edu.vn"],
    sender_email=os.getenv("SENDER_EMAIL"),
    sender_password=os.getenv("SENDER_PASSWORD"),
)

# Initialize agent with tools
agent_decision = AgentClient(
    model=model,
    system_prompt=DECISION_PROMPT,  
).create_agent()

agent_evaluate_for_email = AgentClient(
    model=model,
    system_prompt=EVALUATE_PROMPT,
    tools=[get_latest_test_tool_func]
).create_agent()

agent_send_email = AgentClient(
    model=model,
    system_prompt=SEND_EMAIL_PROMPT,
    tools=[send_email]
).create_agent()


agent_evaluate = AgentClient(
    model=model,
    system_prompt=SCHEULE_PROMPT,
    tools=[get_latest_test_tool_func]
).create_agent()

agent_calendar = AgentClient(
    model=model,
    system_prompt=CALENDAR_PROMPT,
    tools=[read_calendar_events, create_calendar_event_simple]
).create_agent()

agent_knowledge_from_web = AgentClient(
    model=model,
    system_prompt=SEARCH_WEB_PROMPT,
    tools=[search_web]
).create_agent()


# Initialize memory handler
memory_handler = MessageMemoryHandler(max_messages=15)



@cl.on_chat_start
async def start():
    """Initialize chat session"""
    cl.user_session.set("message_count", 0)
    cl.user_session.set("weekend_email_sent", False)  # Flag to track weekend email
    
    # Welcome message with features
    welcome_msg = """🎓 **Xin chào! Tôi là trợ lý học tập AI**

✨ **Tôi có thể giúp bạn:**

🗓️ **Tạo lịch học** - Lập kế hoạch ôn tập cá nhân hóa (Bạn cho tôi biết mã số học sinh, tổ hợp các môn học, ...)
🌐 **Tìm kiếm kiến thức** - Giải đáp câu hỏi học tập (Các câu hỏi về kiến thức)

💌 **Báo cáo cuối tuần** - Tự động gửi email báo cáo tình hình học tập

📧 Hãy cho tôi biết bạn cần hỗ trợ gì nhé!"""
    
    await cl.Message(content=welcome_msg).send()
    
@cl.set_starters
async def set_starters(user=None):
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
            ),

        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="https://help.chainlit.io/public/learn.svg",
            ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
            ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
            )
        ]
    

@cl.on_message
async def main(message: cl.Message):    
    try:
        # Get message with context
        message_with_context = memory_handler.get_history_message(message.content)
        
        decision = await agent_decision.run((message_with_context))
        print(f"Decision output: {decision.output}")
        print(f"Decision output type: {type(decision.output)}")
        print(f"Decision output repr: {repr(decision.output)}")
        
        # Clean the output and compare
        decision_clean = str(decision.output).strip().lower()
        print(f"Decision clean: '{decision_clean}'")
        
        if decision_clean == "calendar":
            print("Running calendar agent...")
            try:
                schedule_response = await agent_evaluate.run((message_with_context))
                await cl.Message(content=str(schedule_response.output)).send()
                
                # Check if the schedule is ready to be added to calendar
                import json
                try:
                    # Try to parse the response as JSON to check for confirm field
                    response_str = str(schedule_response.output)
                    # Look for JSON in the response
                    if "{" in response_str and "}" in response_str:
                        start_idx = response_str.find("{")
                        end_idx = response_str.rfind("}") + 1
                        json_str = response_str[start_idx:end_idx]
                        schedule_data = json.loads(json_str)
                        
                        # Check if confirm field exists and is ready
                        if schedule_data.get("confirm") == "YES":
                            print("Schedule confirmed, adding to calendar...")
                            
                            # Check if it's weekend and send report (only once per session)
                            weekend_email_sent = cl.user_session.get("weekend_email_sent", False)
                            today = datetime.now()
                            is_weekend = today.weekday() >= 5  # Saturday = 5, Sunday = 6
                            print(f"Today: {today}, is_weekend: {is_weekend}, email_sent: {weekend_email_sent}")
                            
                            if is_weekend and not weekend_email_sent:
                                try:
                                    print("Sending weekend report...")
                                    # Run evaluation agent to get student performance report
                                    evaluation_response = await agent_evaluate_for_email.run(f"Tạo báo cáo đánh giá kết quả học tập của học sinh dựa trên các bài kiểm tra gần đây nhất. Context từ cuộc trò chuyện: {message_with_context}")
                                    print(f"Evaluation response: {evaluation_response.output}")
                                    
                                    # Send the evaluation report via email
                                    if evaluation_response and evaluation_response.output:
                                        email_prompt = f"""
                                        Hãy gửi email báo cáo tình hình học tập cuối tuần với nội dung sau:
                                        
                                        {evaluation_response.output}
                                        
                                        Email này sẽ được gửi đến phụ huynh/giáo viên để cập nhật tình hình học tập của học sinh.
                                        """
                                        
                                        email_response = await agent_send_email.run(email_prompt)
                                        print(f"Email response: {email_response.output}")
                                        
                                        # Mark email as sent for this session
                                        cl.user_session.set("weekend_email_sent", True)
                                        
                                        # Notify user about the weekend report
                                        weekend_msg = f"📧 **Báo cáo cuối tuần đã được gửi!**\n\nEmail báo cáo tình hình học tập đã được gửi thành công.\n\n{str(email_response.output)}"
                                        await cl.Message(content=weekend_msg).send()
                                        memory_handler.store_bot_response(weekend_msg)
                                        
                                except Exception as e:
                                    print(f"Error sending weekend report: {e}")
                                    error_msg = f"❌ Lỗi khi gửi báo cáo cuối tuần: {str(e)}"
                                    await cl.Message(content=error_msg).send()
                                    memory_handler.store_bot_response(error_msg)
                            elif is_weekend and weekend_email_sent:
                                print("Weekend email already sent in this session")
                            
                            try:
                                # Add more specific logging
                                print(f"Passing schedule data to calendar agent: {str(schedule_response.output)[:200]}...")
                                
                                # Get correct 2025 dates
                                week_dates = get_current_week_dates()
                                
                                # Create a detailed prompt with the exact schedule structure
                                calendar_prompt = f"""
                                IMPORTANT: Today is July 13, 2025. Create study events based on this EXACT schedule:

                                EXACT SCHEDULE TO CREATE:
                                {str(schedule_response.output)}
                                
                                CRITICAL INSTRUCTIONS:
                                1. FIRST: Read current calendar events using read_calendar_events
                                2. THEN: Create each study session as a separate calendar event using create_calendar_event_simple
                                3. Use EXACT times and subjects from the schedule above
                                4. Use 2025 dates only:
                                   - Monday: 2025-07-14
                                   - Tuesday: 2025-07-15
                                   - Wednesday: 2025-07-16
                                   - Thursday: 2025-07-17
                                   - Friday: 2025-07-18
                                   - Saturday: 2025-07-19
                                   - Sunday: 2025-07-20
                                
                                EXAMPLE FORMAT for each event:
                                - Title: "Study Toán: Hàm số, Logarit"
                                - start_time: "2025-07-14 08:00"
                                - end_time: "2025-07-14 10:00"
                                - description: "Nghiên cứu chuyên sâu về Hàm số và Logarit"
                                
                                CREATE ALL EVENTS exactly as shown in the schedule above.
                                """
                                
                                calendar_response = await safe_agent_run(agent_calendar, calendar_prompt)
                                await cl.Message(content=str(calendar_response.output)).send()
                                memory_handler.store_bot_response(str(calendar_response.output))
                            except Exception as calendar_error:
                                print(f"Error creating calendar events: {calendar_error}")
                                # If it's a function call error, try with a simpler approach
                                if "MALFORMED_FUNCTION_CALL" in str(calendar_error):
                                    print("Attempting simpler calendar creation...")
                                    try:
                                        simple_response = await safe_agent_run(agent_calendar, "Please read my calendar events for the next 7 days")
                                        await cl.Message(content=f"📅 Calendar status: {simple_response.output}").send()
                                        memory_handler.store_bot_response(str(simple_response.output))
                                    except Exception as simple_error:
                                        error_message = f"❌ Lỗi khi tạo lịch học: {str(simple_error)}"
                                        await cl.Message(content=error_message).send()
                                        memory_handler.store_bot_response(error_message)
                                else:
                                    error_message = f"❌ Lỗi khi tạo lịch học: {str(calendar_error)}"
                                    await cl.Message(content=error_message).send()
                                    memory_handler.store_bot_response(error_message)
                        else:
                            print("Schedule not confirmed, skipping calendar creation")
                            memory_handler.store_bot_response(str(schedule_response.output))
                    else:
                        print("No JSON found in response, skipping calendar creation")
                        memory_handler.store_bot_response(str(schedule_response.output))
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing schedule response: {e}")
                    print("Skipping calendar creation")
                    memory_handler.store_bot_response(str(schedule_response.output))
            except Exception as schedule_error:
                print(f"Error creating schedule: {schedule_error}")
                error_message = f"❌ Lỗi khi tạo lịch học: {str(schedule_error)}"
                await cl.Message(content=error_message).send()
                memory_handler.store_bot_response(error_message)
            
        elif decision_clean == "web":
            try:
                response = await agent_knowledge_from_web.run((message_with_context))
                await cl.Message(content=str(response.output)).send()
                memory_handler.store_bot_response(str(response.output))
            except Exception as web_error:
                print(f"Error with web search: {web_error}")
                error_message = f"❌ Lỗi khi tìm kiếm thông tin: {str(web_error)}"
                await cl.Message(content=error_message).send()
                memory_handler.store_bot_response(error_message)
        
        else:
            print(f"Unknown decision: '{decision_clean}'")
            await cl.Message(content="Xin lỗi, tôi không hiểu yêu cầu của bạn. Vui lòng thử lại.").send()
            
    except Exception as main_error:
        print(f"Unexpected error in main: {main_error}")
        error_message = f"❌ Đã có lỗi xảy ra: {str(main_error)}"
        await cl.Message(content=error_message).send()