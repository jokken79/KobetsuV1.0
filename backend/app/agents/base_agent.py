from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Kobetsu ecosystem.
    Defines the standard interface for agent interaction.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Main processing method for the agent.
        
        Args:
            input_data: The input data to process (format depends on agent type)
            
        Returns:
            Dict containing the results of the processing
        """
        pass

    def log_activity(self, message: str) -> None:
        """
        Log agent activity (placeholder for future centralized logging).
        """
        print(f"[{self.name}] {message}")
