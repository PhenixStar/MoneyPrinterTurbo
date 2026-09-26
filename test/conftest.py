import pytest

from app.config import config


@pytest.fixture(autouse=True)
def _disable_llm_fallback_provider():
    """
    Tests exercise single-provider error paths against the live `config.app`.
    A local config.toml with `llm_fallback_provider` set would silently retry
    those calls on a real endpoint, so the fallback is off unless a test passes
    its own app_config.
    """
    had_key = "llm_fallback_provider" in config.app
    previous = config.app.get("llm_fallback_provider")
    config.app["llm_fallback_provider"] = ""
    yield
    if had_key:
        config.app["llm_fallback_provider"] = previous
    else:
        config.app.pop("llm_fallback_provider", None)
