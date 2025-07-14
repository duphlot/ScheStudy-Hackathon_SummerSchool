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
import chainlit as cl

from utils.basetools import *
from utils.basetools.google_calendar import (create_calendar_event_simple,read_calendar_events)
from utils.basetools.search_student import (get_latest_test_tool_func,)

# Import custom handlers
from message_handlers import handle_calendar_request, handle_web_request, handle_unknown_request
from ui_handlers import start_chat, set_chat_starters

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

memory_handler = MessageMemoryHandler(max_messages=15)

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    await start_chat()
    
@cl.set_starters
async def set_starters(user=None):
    return await set_chat_starters(user)
    

@cl.on_message
async def main(message: cl.Message):    
    try:
        # Get message with context
        message_with_context = memory_handler.get_history_message(message.content)
        
        # Get decision from agent
        decision = await agent_decision.run((message_with_context))
        print(f"Decision output: {decision.output}")
        print(f"Decision output type: {type(decision.output)}")
        print(f"Decision output repr: {repr(decision.output)}")
        
        decision_clean = str(decision.output).strip().lower()
        print(f"Decision clean: '{decision_clean}'")
        
        # Route to appropriate handler
        if decision_clean == "calendar":
            await handle_calendar_request(
                agent_evaluate, agent_evaluate_for_email, agent_send_email, 
                agent_calendar, memory_handler, message_with_context
            )
        elif decision_clean == "web":
            await handle_web_request(agent_knowledge_from_web, memory_handler, message_with_context)
        else:
            print(f"Unknown decision: '{decision_clean}'")
            await handle_unknown_request()
            
    except Exception as main_error:
        print(f"Unexpected error in main: {main_error}")
        error_message = f"❌ Đã có lỗi xảy ra: {str(main_error)}"
        await cl.Message(content=error_message).send()