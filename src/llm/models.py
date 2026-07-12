"""
LLM model initialization and configuration.
Supports OpenAI (GPT-4), Anthropic (Claude), and Google Gemini providers.
"""

from typing import Optional, Union
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseLanguageModel

from src.core.config import get_app_settings


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> BaseLanguageModel:
    """
    Get initialized LLM instance.

    Args:
        provider: "openai", "anthropic", or "google" (uses config if not provided)
        model: Model name (uses config if not provided)
        temperature: Sampling temperature (0-1)
        max_tokens: Max output tokens

    Returns:
        Initialized language model instance
    """
    settings = get_app_settings()

    provider = provider or settings.llm_provider

    # Resolve model name based on provider
    if provider == "google":
        model = model or settings.google_model_name
    else:
        model = model or settings.openai_model_name

    if provider == "openai":
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=model or "gpt-4-turbo",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    elif provider == "anthropic":
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=model or "claude-3-sonnet-20240229",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    elif provider == "google":
        return ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=model or "gemini-3.5-flash-lite",
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Choose from: openai, anthropic, google")


class LLMManager:
    """Manager for LLM instances with provider-specific configuration"""

    def __init__(self):
        self.settings = get_app_settings()
        self._llm_instances = {}

    def get_agent_llm(
        self,
        agent_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> BaseLanguageModel:
        """
        Get LLM for specific agent with appropriate settings.

        Args:
            agent_name: Name of agent (planner, writer, critic, etc.)
            temperature: Sampling temperature
            max_tokens: Max output tokens

        Returns:
            Configured LLM instance
        """
        # Cache instances to avoid recreating
        cache_key = f"{agent_name}_{temperature}_{max_tokens}"
        if cache_key in self._llm_instances:
            return self._llm_instances[cache_key]

        # Get max_tokens from config if not provided
        if max_tokens is None:
            max_tokens = self._get_agent_max_tokens(agent_name)

        # Resolve model name based on provider
        if self.settings.llm_provider == "google":
            model_name = self.settings.google_model_name
        else:
            model_name = self.settings.openai_model_name

        llm = get_llm(
            provider=self.settings.llm_provider,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._llm_instances[cache_key] = llm
        return llm

    def _get_agent_max_tokens(self, agent_name: str) -> Optional[int]:
        """Get default max tokens for an agent"""
        from src.core.config import get_app_config

        config = get_app_config()
        agent_tokens = config.get("llm", {}).get("max_tokens_per_agent", {})
        return agent_tokens.get(agent_name, None)

    def get_planner_llm(self) -> BaseLanguageModel:
        """Get LLM for Planner agent"""
        return self.get_agent_llm("planner", temperature=0.7)

    def get_research_llm(self) -> BaseLanguageModel:
        """Get LLM for Research agent"""
        return self.get_agent_llm("research", temperature=0.3)

    def get_outline_llm(self) -> BaseLanguageModel:
        """Get LLM for Outline agent"""
        return self.get_agent_llm("outline", temperature=0.5)

    def get_writer_llm(self) -> BaseLanguageModel:
        """Get LLM for Writer agent"""
        return self.get_agent_llm("writer", temperature=0.8)

    def get_visual_llm(self) -> BaseLanguageModel:
        """Get LLM for Visual agent"""
        return self.get_agent_llm("visual", temperature=0.7)

    def get_seo_llm(self) -> BaseLanguageModel:
        """Get LLM for SEO agent"""
        return self.get_agent_llm("seo", temperature=0.5)

    def get_critic_llm(self) -> BaseLanguageModel:
        """Get LLM for Critic agent"""
        return self.get_agent_llm("critic", temperature=0.3)

    def get_publisher_llm(self) -> BaseLanguageModel:
        """Get LLM for Publisher agent"""
        return self.get_agent_llm("publisher", temperature=0.0)


# Singleton instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get or create LLM manager singleton"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
