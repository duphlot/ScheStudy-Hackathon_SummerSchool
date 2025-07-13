"""
Test file for calendar tools
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
import sys
sys.path.append('src')

from utils.basetools.google_calendar import read_calendar_events, create_calendar_event_simple

async def test_calendar_tools():
    """Test calendar tools independently"""
    print("🧪 Testing Calendar Tools...")
    
    # Test 1: Read calendar events
    print("\n1. Testing read_calendar_events...")
    try:
        events_result = read_calendar_events(days_ahead=7)
        print(f"✅ Read events successful:")
        print(f"Result: {events_result}")
    except Exception as e:
        print(f"❌ Error reading events: {e}")
    
    # Test 2: Create a simple test event
    print("\n2. Testing create_calendar_event_simple...")
    try:
        # Create a test event for tomorrow at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.strftime("%Y-%m-%d 10:00")
        end_time = tomorrow.strftime("%Y-%m-%d 11:00")
        
        result = create_calendar_event_simple(
            title="Test Event - Calendar Tool",
            start_time=start_time,
            end_time=end_time,
            description="This is a test event created by the calendar tool",
            location="Test Location"
        )
        print(f"✅ Create event successful:")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Error creating event: {e}")
    
    # Test 3: Test with Pydantic AI agent
    print("\n3. Testing with Pydantic AI agent...")
    try:
        from llm.base import AgentClient
        from pydantic_ai.models.gemini import GeminiModel
        from pydantic_ai.providers.google_gla import GoogleGLAProvider
        
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.5-flash', provider=provider)
        
        # Create a simple test agent
        test_agent = AgentClient(
            model=model,
            system_prompt="You are a helpful assistant. Use the calendar tools to read events and create a test event if needed.",
            tools=[read_calendar_events, create_calendar_event_simple]
        ).create_agent()
        
        response = await test_agent.run("Please read my calendar events for the next 7 days")
        print(f"✅ Agent response:")
        print(f"Result: {response.output}")
        
    except Exception as e:
        print(f"❌ Error with agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_calendar_tools())
