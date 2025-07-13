from data.milvus.indexing import MilvusIndexer
import os
from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

import chainlit as cl

from utils.basetools import *

# Initialize Milvus indexer (run only once to create collection and index data)
# Comment this out after first run
# Replace "___________" with your collection name and FAQ file path
# Initialize model and provider
provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel('gemini-2.5-flash', provider=provider)

# Initialize your tool 
#---------------------------------------------=
#---------------------------------------------

# Initialize agent with tools
agent = AgentClient(
    model=model,
    system_prompt="You are an intelligent virtual assistant. Please use `faq_tool` to search user question and answer.",  # Replace with your system prompt
    tools=[] # Replace with your tools if any, e.g., [faq_tool]
).create_agent()

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    cl.user_session.set("message_count", 0)
    # await cl.Message(content="🎓 **Chào mừng đến với Hệ thống hỗ trợ truy vấn NHÂN SỰ !**").send()
@cl.set_starters
async def set_starters():
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
    # YOUR LOGIC HERE
    response = await agent.run((message.content))
    await cl.Message(content=str(response.output)).send()

    send_email_tool(
        EmailToolInput(
            subject="FaQ Question Received",
            body=f"Received question: {message.content}\nResponse: {response.output}"
        ), to_emails=["dung.phank24@hcmut.edu.vn"]
    )