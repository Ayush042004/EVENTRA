"""Abstract LLM Provider Interface"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class LLMProvider(ABC):
    @abstractmethod
    async def structured_output(self, prompt: str, schema: Any) -> Any:
        pass

    @abstractmethod
    async def tool_call(self, prompt: str, tools: List[Any]) -> Any:
        pass
