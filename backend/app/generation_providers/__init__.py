"""
Provider adapter package for generation dispatch.

Adapters are registered under "{provider_key}:{capability}" composite keys.
Call get_adapter(provider_key, capability) to retrieve an instantiated adapter.
"""
from backend.app.generation_providers.openai_adapter import OpenAIVideoAdapter
from backend.app.generation_providers.heygen_adapter import HeyGenAvatarAdapter
from backend.app.generation_providers.minimax_adapter import MiniMaxImageAdapter

# Map used by generation_dispatch._PROVIDER_REGISTRY.
# Also imported by tests and the dispatch module itself.
ADAPTER_REGISTRY = {
    "openai:video": OpenAIVideoAdapter,
    "heygen:avatar_video": HeyGenAvatarAdapter,
    "minimax:image": MiniMaxImageAdapter,
}


class ProviderError(Exception):
    """Raised by adapters when a provider call fails unrecoverably."""

    def __init__(self, message: str, status_code: int = 0, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def get_adapter(provider_key: str, capability: str = ""):
    """
    Return an instantiated adapter for (provider_key, capability).

    For backward compatibility in tests, capability may be omitted when
    provider_key already contains a colon (e.g. "openai:video").
    """
    if ":" in provider_key:
        registry_key = provider_key
    else:
        registry_key = f"{provider_key}:{capability}"
    cls = ADAPTER_REGISTRY.get(registry_key)
    if cls is None:
        raise KeyError(f"no adapter registered for {registry_key!r}")
    return cls()
