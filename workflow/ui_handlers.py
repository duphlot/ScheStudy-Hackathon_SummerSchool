"""
UI handlers for Chainlit interface
"""
import chainlit as cl


async def start_chat():
    """Initialize chat session"""
    cl.user_session.set("message_count", 0)
    cl.user_session.set("weekend_email_sent", False) 
    
    welcome_msg = """🎓 **Xin chào! Tôi là trợ lý học tập AI**

✨ **Tôi có thể giúp bạn:**

🗓️ **Tạo lịch học** - Lập kế hoạch ôn tập cá nhân hóa (Bạn cho tôi biết mã số học sinh, tổ hợp các môn học, ...)
🌐 **Tìm kiếm kiến thức** - Giải đáp câu hỏi học tập (Các câu hỏi về kiến thức)

💌 **Báo cáo cuối tuần** - Tự động gửi email báo cáo tình hình học tập

📧 Hãy cho tôi biết bạn cần hỗ trợ gì nhé!"""
    
    await cl.Message(content=welcome_msg).send()


async def set_chat_starters(user=None):
    """Set up chat starters"""
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
