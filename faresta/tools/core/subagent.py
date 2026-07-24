import sys
from ..base import Tool
from faresta.agent import Agent
from faresta.config import load_config, PROVIDER_DEFAULTS
from faresta.llm.openai_provider import OpenAIProvider
from faresta.llm.anthropic_provider import AnthropicProvider
from faresta.llm.google_provider import GoogleProvider
from faresta.llm.openai_compatible import create_provider, COMPATIBLE_PROVIDERS


def _get_provider(config):
    if not config.api_key:
        return None
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
    }
    if config.provider in providers:
        cls = providers[config.provider]
        return cls(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            effort=config.effort,
        )
    if config.provider in COMPATIBLE_PROVIDERS:
        return create_provider(
            name=config.provider,
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            effort=config.effort,
        )
    raise ValueError(f"Unknown provider '{config.provider}'")


class SubAgentTool(Tool):
    name = "subagent"
    description = "Delegate a complex task to a sub-agent. Use for multi-step work like refactoring, debugging, or research that needs its own context."
    parameters = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Detailed task description for the sub-agent. Include what files to read, what changes to make, and expected output format.",
            },
        },
        "required": ["task"],
    }

    def execute(self, task: str) -> str:
        config = load_config()
        llm = _get_provider(config)
        if llm is None:
            return "Error: API key not configured. Run /login first."
        agent = Agent(llm, config)
        agent.add_system_prompt()
        result = agent.run(task)
        cost = agent.cost_tracker.summary()
        messages = len(agent.messages)
        return f"--- Sub-agent Result ---\n{result}\n\n--- Sub-agent Stats ---\n{cost}, messages: {messages}"
