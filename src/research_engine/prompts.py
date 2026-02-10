"""Prompt management for versioned LLM prompts."""

import yaml
import structlog
from pathlib import Path
from typing import Dict, Any

logger = structlog.get_logger()


class PromptManager:
    """Manages versioned prompt templates.
    
    Prompts are stored in YAML files with version tracking.
    The 'current.yaml' symlink points to the active version.
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt YAML files
        """
        self.prompts_dir = Path(prompts_dir)
        self.logger = logger.bind(service="prompt_manager")
        self.current = self._load_current()
        
        self.logger.info(
            "prompt_loaded",
            version=self.version,
            model=self.config.get('model')
        )
    
    def _load_current(self) -> Dict[str, Any]:
        """Load the current active prompt.
        
        Returns:
            Parsed prompt YAML
        """
        current_path = self.prompts_dir / "current.yaml"
        
        if not current_path.exists():
            raise FileNotFoundError(f"No current prompt found at {current_path}")
        
        with open(current_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def version(self) -> int:
        """Get prompt version number."""
        return self.current.get('version', 0)
    
    @property
    def system_prompt(self) -> str:
        """Get system prompt text."""
        return self.current.get('system_prompt', '')
    
    @property
    def user_template(self) -> str:
        """Get user prompt template."""
        return self.current.get('user_prompt_template', '')
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get model configuration (temperature, etc.)."""
        return self.current.get('config', {})
    
    def format_user_prompt(self, **kwargs) -> str:
        """Format user prompt with provided variables.
        
        Args:
            **kwargs: Variables to interpolate into template
            
        Returns:
            Formatted prompt string
        """
        return self.user_template.format(**kwargs)
