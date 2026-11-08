"""Configurable Cloud & Local LLM Provider service with Official Google Gemini API & OpenAI support."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProviderService:
    """
    Unified LLM Provider abstraction.
    Supports official Google Gemini API (Free Tier), OpenAI, Groq, OpenRouter, DeepSeek,
    and local endpoints (Ollama) via backend environment variables without modifying RAG.
    """

    SUPPORTED_PROVIDERS = {
        "gemini": {
            "name": "Google Gemini (Official Free-Tier SDK)",
            "default_model": "gemini-3.5-flash-lite",
            "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
            "env_key": "GEMINI_API_KEY",
        },
        "openai": {
            "name": "OpenAI",
            "default_model": "gpt-4o-mini",
            "default_base_url": "https://api.openai.com/v1",
            "env_key": "OPENAI_API_KEY",
        },
        "groq": {
            "name": "Groq (Fast Cloud Inference)",
            "default_model": "llama-3.1-8b-instant",
            "default_base_url": "https://api.groq.com/openai/v1",
            "env_key": "GROQ_API_KEY",
        },
        "openrouter": {
            "name": "OpenRouter",
            "default_model": "meta-llama/llama-3.1-8b-instruct:free",
            "default_base_url": "https://openrouter.ai/api/v1",
            "env_key": "OPENROUTER_API_KEY",
        },
        "deepseek": {
            "name": "DeepSeek",
            "default_model": "deepseek-chat",
            "default_base_url": "https://api.deepseek.com/v1",
            "env_key": "DEEPSEEK_API_KEY",
        },
        "custom": {
            "name": "Custom / Local (e.g. Ollama)",
            "default_model": "qwen2.5:0.5b",
            "default_base_url": "http://127.0.0.1:11434/v1",
            "env_key": "CUSTOM_LLM_API_KEY",
        },
    }

    def __init__(self, custom_client: Optional[Any] = None):
        self._custom_client = custom_client

    def get_active_provider_name(self) -> str:
        """Return canonical lowercase provider identifier."""
        llm_p = (getattr(settings, "LLM_PROVIDER", "") or "").strip().lower()
        ai_p = (getattr(settings, "AI_PROVIDER", "") or "").strip().lower()
        if llm_p and llm_p != "gemini" and llm_p in self.SUPPORTED_PROVIDERS:
            return llm_p
        if ai_p and ai_p in self.SUPPORTED_PROVIDERS:
            return ai_p
        if llm_p and llm_p in self.SUPPORTED_PROVIDERS:
            return llm_p
        return "gemini"

    def get_provider_config(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Resolve API key, base URL, and model for requested or active provider."""
        prov = (provider_name or self.get_active_provider_name()).lower()
        meta = self.SUPPORTED_PROVIDERS.get(prov, self.SUPPORTED_PROVIDERS["gemini"])

        if prov == "gemini":
            api_key = getattr(settings, "GEMINI_API_KEY", "")
            base_url = getattr(settings, "GEMINI_BASE_URL", meta["default_base_url"])
            model = getattr(settings, "GEMINI_MODEL", "") or meta["default_model"]
        elif prov == "groq":
            api_key = settings.GROQ_API_KEY
            base_url = settings.GROQ_BASE_URL
            model = settings.GROQ_MODEL or meta["default_model"]
        elif prov == "openrouter":
            api_key = settings.OPENROUTER_API_KEY
            base_url = settings.OPENROUTER_BASE_URL
            model = settings.OPENROUTER_MODEL or meta["default_model"]
        elif prov == "deepseek":
            api_key = settings.DEEPSEEK_API_KEY
            base_url = settings.DEEPSEEK_BASE_URL
            model = settings.DEEPSEEK_MODEL or meta["default_model"]
        elif prov == "custom":
            api_key = settings.CUSTOM_LLM_API_KEY
            base_url = settings.CUSTOM_LLM_BASE_URL
            model = settings.CUSTOM_LLM_MODEL or meta["default_model"]
        else:  # openai
            api_key = settings.OPENAI_API_KEY
            base_url = settings.OPENAI_BASE_URL
            model = settings.OPENAI_MODEL or meta["default_model"]

        # Clean key
        api_key = (api_key or "").strip()
        if api_key in [
            "your-openai-api-key-here",
            "your-gemini-api-key-here",
            "your-groq-api-key-here",
            "your-key-here",
            ""
        ]:
            api_key = ""

        # For custom/local endpoints (e.g. Ollama), key is optional
        if not api_key and prov == "custom":
            api_key = "ollama-local"

        return {
            "provider": prov,
            "display_name": meta["name"],
            "api_key": api_key,
            "base_url": base_url or meta["default_base_url"],
            "model": model,
            "env_key": meta["env_key"],
        }

    def get_client(self, provider_name: Optional[str] = None) -> Tuple[Optional[Any], str, str]:
        """
        Instantiate client for the active or specified provider.
        Returns (client, model_name, provider_name).
        """
        if self._custom_client:
            prov_cfg = self.get_provider_config(provider_name)
            return self._custom_client, prov_cfg["model"], prov_cfg["provider"]

        cfg = self.get_provider_config(provider_name)
        if not cfg["api_key"]:
            return None, cfg["model"], cfg["provider"]

        if cfg["provider"] == "gemini":
            try:
                from google import genai
                client = genai.Client(api_key=cfg["api_key"])
                return client, cfg["model"], cfg["provider"]
            except Exception as e:
                logger.error(f"Failed to instantiate Google GenAI client: {e}")
                return None, cfg["model"], cfg["provider"]
        else:
            try:
                client = OpenAI(
                    api_key=cfg["api_key"],
                    base_url=cfg["base_url"],
                    timeout=25.0,
                    max_retries=1
                )
                return client, cfg["model"], cfg["provider"]
            except Exception as e:
                logger.error(f"Failed to instantiate OpenAI-compatible client for '{cfg['provider']}': {e}")
                return None, cfg["model"], cfg["provider"]

    def mask_key(self, key: str) -> str:
        """Safely mask key for UI diagnostics (first 7 + last 4), never exposing raw key."""
        if not key:
            return "Not Set"
        if len(key) <= 12:
            return "******"
        return f"{key[:7]}...{key[-4:]}"

    def get_provider_status(self) -> Dict[str, Any]:
        """Diagnostic overview of current LLM provider configuration."""
        cfg = self.get_provider_config()
        has_key = bool(cfg["api_key"])

        return {
            "active_provider": cfg["provider"],
            "display_name": cfg["display_name"],
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "has_key": has_key,
            "masked_key": self.mask_key(cfg["api_key"]) if has_key else "Missing",
            "env_variable": cfg["env_key"],
            "available_providers": [
                {"id": k, "name": v["name"], "default_model": v["default_model"]}
                for k, v in self.SUPPORTED_PROVIDERS.items()
            ],
            "low_ram_mode": settings.LOW_RAM_MODE
        }

    def _generate_gemini(
        self,
        cfg: Dict[str, Any],
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Execute text generation via official Google GenAI SDK."""
        api_key = cfg["api_key"]
        if not api_key:
            return None, "unconfigured", "GEMINI_API_KEY is not configured in backend environment."

        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            return None, "sdk_missing", f"google-genai SDK not available: {e}"

        # Extract system prompt and user/assistant messages
        system_instruction = ""
        user_parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_instruction += content + "\n\n"
            else:
                user_parts.append(content)

        combined_contents = "\n\n".join(user_parts)
        t = temperature if temperature is not None else 0.2
        m = max_tokens if max_tokens is not None else 1000
        target_model = cfg["model"] or "gemini-3.5-flash-lite"

        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction.strip() if system_instruction else None,
                temperature=t,
                max_output_tokens=m
            )
            response = client.models.generate_content(
                model=target_model,
                contents=combined_contents,
                config=config
            )
            if response and response.text:
                return response.text.strip(), None, None
            return None, "empty_response", "Gemini returned an empty response."

        except Exception as e:
            err_str = str(e).lower()
            logger.warning(f"Google Gemini generation exception: {e}")

            # Quota or rate limit (Do NOT retry repeatedly)
            if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "high demand" in err_str or "503" in err_str:
                return None, "quota_exceeded", str(e)

            # Invalid API key / Authentication error
            if "401" in err_str or "403" in err_str or "api_key_invalid" in err_str or "permission_denied" in err_str:
                return None, "auth_error", str(e)

            # Connection / Timeout error
            if "timeout" in err_str or "connection" in err_str or "dns" in err_str or "offline" in err_str or "getaddrinfo" in err_str or "network" in err_str:
                return None, "connection_error", str(e)

            # Model unavailable / not found (404) -> Fallback attempt with alternative free-tier model
            if "404" in err_str or "not_found" in err_str:
                if target_model != "gemini-3.5-flash-lite":
                    try:
                        logger.info("Retrying with gemini-3.5-flash-lite fallback...")
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=combined_contents,
                            config=config
                        )
                        if response and response.text:
                            return response.text.strip(), None, None
                    except Exception as sub_e:
                        logger.warning(f"Fallback model failed: {sub_e}")
                return None, "model_unavailable", str(e)

            return None, "api_error", str(e)

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute completion with the active provider (Gemini or OpenAI-compatible).
        Returns:
            (answer_text, error_code, error_detail)
            error_code: None (success), 'unconfigured', 'quota_exceeded', 'auth_error', 'connection_error', 'api_error'
        """
        active_prov = self.get_active_provider_name()
        cfg = self.get_provider_config(active_prov)

        # 1. Google Gemini Native Path
        if active_prov == "gemini":
            return self._generate_gemini(cfg, messages, temperature, max_tokens)

        # 2. OpenAI / Groq / OpenRouter / Custom Path
        client, model_name, provider_name = self.get_client(active_prov)
        if client is None:
            return None, "unconfigured", f"API key for provider '{provider_name}' is not configured in .env."

        t = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        m = max_tokens if max_tokens is not None else settings.OPENAI_MAX_TOKENS

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=t,
                max_tokens=m,
                timeout=25.0
            )
            answer = response.choices[0].message.content or ""
            return answer.strip(), None, None

        except RateLimitError as e:
            logger.warning(f"Provider '{provider_name}' rate limit or quota exceeded: {e}")
            return None, "quota_exceeded", str(e)
        except AuthenticationError as e:
            logger.warning(f"Provider '{provider_name}' authentication failed: {e}")
            return None, "auth_error", str(e)
        except APIConnectionError as e:
            logger.warning(f"Provider '{provider_name}' connection failed: {e}")
            return None, "connection_error", str(e)
        except APIError as e:
            logger.error(f"Provider '{provider_name}' API error: {e}")
            return None, "api_error", str(e)
        except Exception as e:
            logger.error(f"Unexpected generation error on provider '{provider_name}': {e}")
            return None, "api_error", str(e)


llm_provider_service = LLMProviderService()
