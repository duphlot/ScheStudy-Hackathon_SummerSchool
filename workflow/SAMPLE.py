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

import chainlit as cl

from utils.basetools import *
from utils.basetools.google_calendar import (create_calendar_event_simple,read_calendar_events
)
from utils.basetools.search_student import (get_latest_test_tool_func)
from utils.safe_calendar import safe_agent_run

# Initialize model and provider
provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel('gemini-2.5-flash', provider=provider)
#---------------------------------------------
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

agent_send_email = AgentClient(
    model=model,
    system_prompt=SEND_EMAIL_PROMPT,
    tools=[send_email]
).create_agent()


agent_create_calendar_by_search_student_info = AgentClient(
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
    await cl.Message(content="🎓 **Chào mừng đến với Hệ thống hỗ trợ truy vấn NHÂN SỰ !**").send()
    

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
                schedule_response = await agent_create_calendar_by_search_student_info.run((message_with_context))
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
                            try:
                                # Add more specific logging
                                print(f"Passing schedule data to calendar agent: {str(schedule_response.output)[:200]}...")
                                
                                # Try with a simpler prompt to avoid function call issues
                                calendar_prompt = f"""
                                Based on this schedule information: {str(schedule_response.output)}
                                
                                Please first read the current calendar events, then create study events accordingly.
                                Make sure to avoid conflicts with existing events and only schedule between 8:00 AM and 10:00 PM.
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