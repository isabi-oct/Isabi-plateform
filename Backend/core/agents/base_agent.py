"""
Base Agent Class for Agentic AI System

This module provides the foundational agent class that all specialized agents inherit from.
It defines the common interface and shared functionality for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the Agentic AI system.
    
    Provides common functionality and defines the interface that all agents must implement.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name of the agent
            description: Description of the agent's purpose
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.context = {}
        self.memory = []
        
        logger.info(f"Initialized {self.name} agent (ID: {self.agent_id})")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return agent response.
        
        Args:
            input_data: Input data containing user message, context, etc.
            
        Returns:
            Dictionary containing agent response and metadata
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        pass
    
    def update_context(self, context: Dict[str, Any]):
        """
        Update agent context with new information.
        
        Args:
            context: New context information
        """
        self.context.update(context)
        self.last_activity = datetime.now()
        logger.debug(f"Updated context for {self.name}: {context}")
    
    def add_to_memory(self, memory_item: Dict[str, Any]):
        """
        Add item to agent memory.
        
        Args:
            memory_item: Memory item to store
        """
        memory_item['timestamp'] = datetime.now().isoformat()
        memory_item['agent_id'] = self.agent_id
        self.memory.append(memory_item)
        
        # Keep only last 100 memory items
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]
        
        logger.debug(f"Added to {self.name} memory: {memory_item}")
    
    def get_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent memory items.
        
        Args:
            limit: Maximum number of memory items to return
            
        Returns:
            List of recent memory items
        """
        return self.memory[-limit:] if self.memory else []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information.
        
        Returns:
            Dictionary containing agent status
        """
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'context_keys': list(self.context.keys()),
            'memory_count': len(self.memory),
            'capabilities': self.get_capabilities()
        }
    
    def reset_context(self):
        """Reset agent context."""
        self.context = {}
        logger.info(f"Reset context for {self.name}")
    
    def reset_memory(self):
        """Reset agent memory."""
        self.memory = []
        logger.info(f"Reset memory for {self.name}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert agent to dictionary representation.
        
        Returns:
            Dictionary representation of the agent
        """
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'context': self.context,
            'memory': self.memory,
            'capabilities': self.get_capabilities()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """
        Load agent from dictionary representation.
        
        Args:
            data: Dictionary containing agent data
        """
        self.agent_id = data.get('agent_id', self.agent_id)
        self.name = data.get('name', self.name)
        self.description = data.get('description', self.description)
        self.context = data.get('context', {})
        self.memory = data.get('memory', [])
        
        if 'created_at' in data:
            self.created_at = datetime.fromisoformat(data['created_at'])
        if 'last_activity' in data:
            self.last_activity = datetime.fromisoformat(data['last_activity'])
        
        logger.info(f"Loaded {self.name} from dictionary data")
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} (ID: {self.agent_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"BaseAgent(id='{self.agent_id}', name='{self.name}', capabilities={self.get_capabilities()})"
