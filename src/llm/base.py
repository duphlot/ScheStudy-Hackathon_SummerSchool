from pydantic_ai import Agent
from typing import List, Callable, Optional
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
import os

provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
model = GeminiModel("gemini-2.0-flash", provider=provider)


class AgentClient:
    def __init__(
        self,
        system_prompt: str,
        tools: Optional[List[Callable]] = None,
        model: GeminiModel = model,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools

    def create_agent(self):
        """Creates and returns a PydanticAI Agent instance."""
        return Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools if self.tools is not None else [],
        )
