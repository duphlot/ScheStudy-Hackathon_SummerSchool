"""
Safe wrapper for calendar functions to handle Gemini API issues
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional


def get_current_week_dates():
    """
    Get correct dates for the current week starting from July 14, 2025
    Returns dict mapping day names to dates in YYYY-MM-DD format
    """
    # Fixed base date - July 14, 2025 (Monday)
    base_date = datetime(2025, 7, 14)

    return {
        "monday": base_date.strftime("%Y-%m-%d"),
        "tuesday": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "wednesday": (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        "thursday": (base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        "friday": (base_date + timedelta(days=4)).strftime("%Y-%m-%d"),
        "saturday": (base_date + timedelta(days=5)).strftime("%Y-%m-%d"),
        "sunday": (base_date + timedelta(days=6)).strftime("%Y-%m-%d"),
    }


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
                print(
                    f"Attempt {attempt + 1} failed with function call error, retrying..."
                )
                await asyncio.sleep(1)  # Wait before retry
                continue
            else:
                raise e

    # If all retries failed
    raise Exception("All retry attempts failed")
