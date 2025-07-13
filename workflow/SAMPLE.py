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
indexer = MilvusIndexer(collection_name="company1", faq_file="src/data/mock_data/HR_FAQ.xlsx")
indexer.run()
# Initialize model and provider
provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel('gemini-2.5-flash', provider=provider)

# Initialize your tool 
#---------------------------------------------
faq_tool = create_faq_tool(collection_name="company1")
#---------------------------------------------

# Initialize agent with tools
agent = AgentClient(
    model=model,
    system_prompt="You are an intelligent virtual assistant. Please use `faq_tool` to search user question and answer.",  # Replace with your system prompt
    tools=[faq_tool] # Replace with your tools if any, e.g., [faq_tool]
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
            label="Liệt kê những môn mà tôi còn yếu",
            message="Tôi đang còn yếu những môn gì vậy?",
            icon="https://help.chainlit.io/public/learn.svg",
            ),

        cl.Starter(
            label="Lộ trình học tuần sắp tới",
            message="Hãy thiết kế lộ trình học những môn tôi còn yếu cho tuần tới và thêm vào Google Calander cá nhân giúp tôi.",
            icon="https://help.chainlit.io/public/learn.svg",
            ),
        cl.Starter(
            label="",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="https://help.chainlit.io/public/learn.svg",
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