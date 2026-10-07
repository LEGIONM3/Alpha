"""Cross-Domain Framework Package Exports."""

from alpha.research.cross_domain.domains import (
    CANONICAL_DOMAINS,
    SUBDOMAINS_BY_PARENT,
    DomainRegistry,
)
from alpha.research.cross_domain.synthesizer import (
    CrossDomainSynthesizer,
    CrossDomainSynthesisResult,
)

__all__ = [
    "CANONICAL_DOMAINS",
    "SUBDOMAINS_BY_PARENT",
    "DomainRegistry",
    "CrossDomainSynthesizer",
    "CrossDomainSynthesisResult",
]
