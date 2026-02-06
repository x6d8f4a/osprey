"""ARIEL search modules.

This module provides keyword and semantic search implementations
for the ARIEL search service.

RAG is now implemented via the Pipeline abstraction:
    SemanticRetriever → ContextWindowAssembler → SingleLLMProcessor → CitationFormatter
"""

from osprey.services.ariel_search.search.keyword import (
    ALLOWED_FIELD_PREFIXES,
    ALLOWED_OPERATORS,
    MAX_QUERY_LENGTH,
    keyword_search,
    parse_query,
)
from osprey.services.ariel_search.search.semantic import (
    semantic_search,
)

__all__ = [
    "ALLOWED_FIELD_PREFIXES",
    "ALLOWED_OPERATORS",
    "MAX_QUERY_LENGTH",
    "keyword_search",
    "parse_query",
    "semantic_search",
]
