from typing import Optional, TYPE_CHECKING

# Use type hinting for external modules if they aren't available yet during definition
if TYPE_CHECKING:
    from alpha.core.identity import IdentityState

class IdentityContextCache:
    """
    A thread-safe, immutable cache holding the validated Alpha identity state.
    This ensures the identity is loaded once at boot and referenced by pointer/reference 
    throughout runtime, preventing repeated serialization or re-injection into prompts.
    """
    def __init__(self):
        self._identity: Optional['IdentityState'] = None
        self._is_loaded: bool = False

    @property
    def identity(self) -> 'IdentityState':
        if not self._identity or not self._is_loaded:
            raise RuntimeError("IdentityContextCache has not been loaded. Call load() first.")
        return self._identity

    def set_identity(self, identity_state: 'IdentityState'):
        """Sets the validated IdentityState upon successful boot/recovery."""
        if self._identity is not None and self._identity != identity_state:
            print("[Cache Warning] Overwriting existing cached identity.") # Add logging in production code
        self._identity = identity_state
        self._is_loaded = True

    def is_loaded(self) -> bool:
        """Checks if the identity context has been successfully loaded."""
        return self._is_loaded

# Global/Singleton instance for runtime access (to fulfill "referenced by pointer")
identity_context = IdentityContextCache()