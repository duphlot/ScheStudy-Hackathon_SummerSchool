"""
Message handlers for different types of user requests
"""
import json
from datetime import datetime
import chainlit as cl
from utils.safe_calendar import safe_agent_run, get_current_week_dates


async def handle_calendar_request(agent_evaluate, agent_evaluate_for_email, agent_send_email, 
                                agent_calendar, memory_handler, message_with_context):
    """Handle calendar-related requests"""
    print("Running calendar agent...")
    try:
        schedule_response = await agent_evaluate.run((message_with_context))
        await cl.Message(content=str(schedule_response.output)).send()
        
        try:
            response_str = str(schedule_response.output)
            if "{" in response_str and "}" in response_str:
                start_idx = response_str.find("{")
                end_idx = response_str.rfind("}") + 1
                json_str = response_str[start_idx:end_idx]
                schedule_data = json.loads(json_str)
                
                if schedule_data.get("confirm") == "YES":
                    print("Schedule confirmed, adding to calendar...")
                    
                    # Handle weekend email
                    await _handle_weekend_email(agent_evaluate_for_email, agent_send_email, 
                                              memory_handler, message_with_context)
                    
                    # Handle calendar creation
                    await _handle_calendar_creation(agent_calendar, memory_handler, schedule_response)
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


async def _handle_weekend_email(agent_evaluate_for_email, agent_send_email, 
                               memory_handler, message_with_context):
    """Handle weekend email sending logic"""
    weekend_email_sent = cl.user_session.get("weekend_email_sent", False)
    today = datetime.now()
    is_weekend = today.weekday() >= 5  # Saturday = 5, Sunday = 6
    print(f"Today: {today}, is_weekend: {is_weekend}, email_sent: {weekend_email_sent}")
    
    if is_weekend and not weekend_email_sent:
        try:
            print("Sending weekend report...")
            evaluation_response = await agent_evaluate_for_email.run(
                f"Tạo báo cáo đánh giá kết quả học tập của học sinh dựa trên các bài kiểm tra gần đây nhất. Context từ cuộc trò chuyện: {message_with_context}"
            )
            print(f"Evaluation response: {evaluation_response.output}")
            
            if evaluation_response and evaluation_response.output:
                email_prompt = f"""
                Hãy gửi email báo cáo tình hình học tập cuối tuần với nội dung sau:
                
                {evaluation_response.output}
                
                Email này sẽ được gửi đến phụ huynh/giáo viên để cập nhật tình hình học tập của học sinh.
                """
                
                email_response = await agent_send_email.run(email_prompt)
                print(f"Email response: {email_response.output}")
                
                cl.user_session.set("weekend_email_sent", True)
                
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


async def _handle_calendar_creation(agent_calendar, memory_handler, schedule_response):
    """Handle calendar event creation"""
    try:
        print(f"Passing schedule data to calendar agent: {str(schedule_response.output)[:200]}...")
        
        week_dates = get_current_week_dates()
        
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


async def handle_web_request(agent_knowledge_from_web, memory_handler, message_with_context):
    """Handle web search requests"""
    try:
        response = await agent_knowledge_from_web.run((message_with_context))
        await cl.Message(content=str(response.output)).send()
        memory_handler.store_bot_response(str(response.output))
    except Exception as web_error:
        print(f"Error with web search: {web_error}")
        error_message = f"❌ Lỗi khi tìm kiếm thông tin: {str(web_error)}"
        await cl.Message(content=error_message).send()
        memory_handler.store_bot_response(error_message)


async def handle_unknown_request():
    """Handle unknown/unrecognized requests"""
    await cl.Message(content="Xin lỗi, tôi không hiểu yêu cầu của bạn. Vui lòng thử lại.").send()
