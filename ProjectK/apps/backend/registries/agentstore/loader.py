"""Agent discovery and loading."""

from pathlib import Path
from typing import Dict
import logging
from .base import UnifiedAgent

logger = logging.getLogger(__name__)


def discover_agents() -> Dict[str, UnifiedAgent]:
    """Discover all agents in agentstore directory."""
    agents = {}
    agent_dir = Path(__file__).parent
    
    # Iterate through subdirectories
    for subdir in agent_dir.iterdir():
        if not subdir.is_dir() or subdir.name.startswith("_"):
            continue
        
        yaml_path = subdir / "agent.yaml"
        if yaml_path.exists():
            try:
                agent = UnifiedAgent.from_yaml(yaml_path)
                agents[agent.name] = agent
                logger.info(f"✅ Loaded agent: {agent.name}")
            except Exception as e:
                logger.error(f"❌ Failed to load agent from {yaml_path}: {e}")
    
    return agents


def get_agent(agents: Dict[str, UnifiedAgent], agent_name: str) -> UnifiedAgent:
    """Get specific agent by name."""
    if agent_name not in agents:
        raise ValueError(f"Agent '{agent_name}' not found. Available: {list(agents.keys())}")
    return agents[agent_name]
