"""
Safe wrapper for calendar functions to handle Gemini API issues
"""
import asyncio
from typing import Optional

def safe_calendar_wrapper(func, *args, **kwargs):
    """
    Safely execute calendar functions with error handling
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Calendar function error: {e}")
        return f"❌ Calendar operation failed: {str(e)}"

async def safe_agent_run(agent, prompt: str, max_retries: int = 2):
    """
    Safely run agent with retries for function call errors
    """
    for attempt in range(max_retries):
        try:
            result = await agent.run(prompt)
            return result
        except Exception as e:
            if "MALFORMED_FUNCTION_CALL" in str(e) and attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed with function call error, retrying...")
                await asyncio.sleep(1)  # Wait before retry
                continue
            else:
                raise e
    
    # If all retries failed
    raise Exception("All retry attempts failed")
