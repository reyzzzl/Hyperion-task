from typing import Dict, Type
from .base import BaseAgent

class AgentRegistry:
    _agents: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, name: str, agent_class: Type[BaseAgent]):
        cls._agents[name] = agent_class

    @classmethod
    def get(cls, name: str) -> Type[BaseAgent]:
        return cls._agents.get(name)

    @classmethod
    def list(cls) -> Dict[str, Type[BaseAgent]]:
        return cls._agents.copy()