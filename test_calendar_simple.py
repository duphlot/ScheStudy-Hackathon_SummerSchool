"""
Simple test file for calendar tools
"""
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test import directly
try:
    import sys
    sys.path.append('src')
    
    # Direct import of calendar module
    from utils.basetools.google_calendar import GoogleCalendarTool
    
    print("✅ Successfully imported GoogleCalendarTool")
    
    # Test basic functionality
    def test_basic_functions():
        print("\n🧪 Testing basic calendar functions...")
        
        # Test reading calendar
        print("1. Testing read_calendar_events function...")
        try:
            from utils.basetools.google_calendar import read_calendar_events
            result = read_calendar_events(days_ahead=7)
            print(f"✅ read_calendar_events works: {result[:100]}...")
        except Exception as e:
            print(f"❌ read_calendar_events failed: {e}")
        
        # Test creating event
        print("\n2. Testing create_calendar_event_simple function...")
        try:
            from utils.basetools.google_calendar import create_calendar_event_simple
            
            # Create a test event for tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.strftime("%Y-%m-%d 10:00")
            end_time = tomorrow.strftime("%Y-%m-%d 11:00")
            
            result = create_calendar_event_simple(
                title="Test Event - Simple",
                start_time=start_time,
                end_time=end_time,
                description="Test event",
                location="Test Location"
            )
            print(f"✅ create_calendar_event_simple works: {result[:100]}...")
        except Exception as e:
            print(f"❌ create_calendar_event_simple failed: {e}")
    
    # Run tests
    test_basic_functions()
    
except Exception as e:
    print(f"❌ Failed to import: {e}")
    import traceback
    traceback.print_exc()
