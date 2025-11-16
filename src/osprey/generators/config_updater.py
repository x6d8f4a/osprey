"""Config auto-update helper for MCP capability generation.

Automatically adds mcp_react model configuration to config.yml with user confirmation.
"""

import re
from pathlib import Path
from typing import Optional, Tuple

import yaml


def find_config_file() -> Optional[Path]:
    """Find the config.yml file in current directory.

    Returns:
        Path to config.yml or None if not found
    """
    config_path = Path.cwd() / 'config.yml'
    return config_path if config_path.exists() else None


def has_capability_react_model(config_path: Path, capability_name: str) -> bool:
    """Check if config already has capability-specific react model configured.

    Args:
        config_path: Path to config.yml
        capability_name: Capability name (e.g., 'weather_demo')

    Returns:
        True if {capability_name}_react is already configured
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        model_key = f"{capability_name}_react"
        if 'models' in config and model_key in config['models']:
            return True
    except Exception:
        pass

    return False


def get_orchestrator_model_config(config_path: Path) -> Optional[dict]:
    """Get the orchestrator model configuration to use as template.

    Args:
        config_path: Path to config.yml

    Returns:
        Dict with provider, model_id, max_tokens or None
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if 'models' in config and 'orchestrator' in config['models']:
            orch_config = config['models']['orchestrator']
            return {
                'provider': orch_config.get('provider', 'anthropic'),
                'model_id': orch_config.get('model_id', 'claude-sonnet-4'),
                'max_tokens': orch_config.get('max_tokens', 4096)
            }
    except Exception:
        pass

    return None


def generate_capability_react_yaml(capability_name: str, template_config: Optional[dict] = None) -> str:
    """Generate YAML snippet for capability-specific react model.

    Args:
        capability_name: Capability name (e.g., 'weather_demo')
        template_config: Optional dict with provider, model_id, max_tokens
                        If None, uses sensible defaults

    Returns:
        Formatted YAML string for {capability_name}_react model
    """
    if template_config:
        provider = template_config['provider']
        model_id = template_config['model_id']
        max_tokens = template_config['max_tokens']
    else:
        provider = 'anthropic'
        model_id = 'claude-sonnet-4'
        max_tokens = 4096

    model_key = f"{capability_name}_react"
    return f"""  {model_key}:
    provider: {provider}
    model_id: {model_id}
    max_tokens: {max_tokens}"""


def add_capability_react_to_config(config_path: Path, capability_name: str, template_config: Optional[dict] = None) -> Tuple[str, str]:
    """Add capability-specific react model to config.yml.

    Args:
        config_path: Path to config.yml
        capability_name: Capability name (e.g., 'weather_demo')
        template_config: Optional model config to use as template

    Returns:
        Tuple of (new_content, preview) where preview shows what was added
    """
    content = config_path.read_text()

    # Generate the capability-specific react configuration
    capability_react_yaml = generate_capability_react_yaml(capability_name, template_config)

    # Find the models section and add capability-specific react model
    # Look for pattern: models:\n  <existing_models>
    # We want to add after the last model entry

    # Strategy: Find the models: section, then find where the next top-level key starts
    # Insert capability_react before that next section

    models_pattern = r'(models:\s*\n(?:  \w+:.*\n(?:    .*\n)*)+)'

    def add_capability_react(match):
        models_section = match.group(1)
        # Add capability_react at the end of the models section
        return f"{models_section}{capability_react_yaml}\n"

    new_content = re.sub(models_pattern, add_capability_react, content, count=1)

    # Create preview
    model_key = f"{capability_name}_react"
    preview = f"""
[bold]{capability_name.title()} ReAct Model Configuration:[/bold]
{capability_react_yaml}

[dim]This will be added to the 'models' section of your config.yml[/dim]
"""

    return new_content, preview


def get_config_preview(capability_name: str, template_config: Optional[dict] = None) -> str:
    """Get a preview of what will be added to config.

    Args:
        capability_name: Capability name (e.g., 'weather_demo')
        template_config: Optional model config to use as template

    Returns:
        Formatted preview string
    """
    capability_react_yaml = generate_capability_react_yaml(capability_name, template_config)
    model_key = f"{capability_name}_react"

    return f"""
[bold]{capability_name.title()} ReAct Model Configuration:[/bold]

{capability_react_yaml}

[dim]Note: This model will be used by {capability_name} for autonomous tool selection.
If not configured, the capability falls back to using the 'orchestrator' model.[/dim]
"""

