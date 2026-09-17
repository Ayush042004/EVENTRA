"""Base Domain Interface"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseEventDomain(ABC):
    @abstractmethod
    def baseline_requirements(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def baseline_tasks(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def baseline_dependencies(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def provider_categories(self) -> List[str]:
        pass
