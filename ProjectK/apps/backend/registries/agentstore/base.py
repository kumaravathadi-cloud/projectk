"""Agent configuration and base classes."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """LLM model configuration."""
    deployment_id: str
    temperature: float = 0.7
    max_tokens: int = 500
    api_version: str = "2024-08-01-preview"


@dataclass
class VoiceConfig:
    """Voice/TTS configuration."""
    current_voice: str = "en-US-AvaMultilingualNeural"


@dataclass
class HandoffConfig:
    """Agent handoff configuration."""
    trigger: str  # Tool name that triggers handoff
    is_entry_point: bool = False


@dataclass
class UnifiedAgent:
    """Unified agent configuration."""
    name: str
    description: str
    greeting: str
    model: ModelConfig
    voice: VoiceConfig
    handoff: HandoffConfig
    prompt_template: str
    tools: list = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "UnifiedAgent":
        """Load agent from YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Convert nested dicts to dataclass instances
        model = ModelConfig(**data.get("model", {}))
        voice = VoiceConfig(**data.get("voice", {}))
        handoff_data = data.get("handoff", {})
        handoff = HandoffConfig(**handoff_data)
        
        return cls(
            name=data["name"],
            description=data["description"],
            greeting=data.get("greeting", "Hello"),
            model=model,
            voice=voice,
            handoff=handoff,
            prompt_template=data.get("prompt_template", ""),
            tools=data.get("tools", []),
        )
    
    def render_prompt(self, context: Dict[str, Any]) -> str:
        """Render Jinja2 prompt template with context variables."""
        from jinja2 import Template
        template = Template(self.prompt_template)
        return template.render(**context)
