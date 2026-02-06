"""ARIEL Search Service.

This module provides the main ARIELSearchService class that orchestrates
the search pipelines and agent executor. The service routes queries to
either a deterministic Pipeline (for KEYWORD, SEMANTIC, RAG, MULTI modes)
or an AgentExecutor (for AGENT mode).

See 04_OSPREY_INTEGRATION.md Section 5 for specification.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from osprey.services.ariel_search.exceptions import (
    ARIELException,
    ConfigurationError,
    SearchExecutionError,
    SearchTimeoutError,
)
from osprey.services.ariel_search.models import (
    ARIELSearchRequest,
    ARIELSearchResult,
    ARIELStatusResult,
    EmbeddingTableInfo,
    SearchMode,
)

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool

    from osprey.models.embeddings.base import BaseEmbeddingProvider
    from osprey.services.ariel_search.config import ARIELConfig
    from osprey.services.ariel_search.database.repository import ARIELRepository
    from osprey.services.ariel_search.pipeline import Pipeline

logger = logging.getLogger(__name__)


class ARIELSearchService:
    """Main service class for ARIEL search functionality.

    This service provides two clean interfaces for search:
    - **Pipelines** (deterministic): For KEYWORD, SEMANTIC, RAG, MULTI modes
    - **Agent** (agentic): For AGENT mode

    The service routes queries based on SearchMode:
    - KEYWORD: KeywordRetriever → TopK → Identity → JSON
    - SEMANTIC: SemanticRetriever → TopK → Identity → JSON
    - RAG: SemanticRetriever → ContextWindow → SingleLLM → Citation
    - MULTI: HybridRetriever(K+S, RRF) → TopK → Identity → JSON
    - AGENT: AgentExecutor (ReAct with search tools)

    Usage:
        config = ARIELConfig.from_dict(config_dict)
        async with create_ariel_service(config) as service:
            result = await service.search("What happened yesterday?")
    """

    def __init__(
        self,
        config: ARIELConfig,
        pool: AsyncConnectionPool,
        repository: ARIELRepository,
    ) -> None:
        """Initialize the service.

        Args:
            config: ARIEL configuration
            pool: Database connection pool
            repository: Database repository
        """
        self.config = config
        self.pool = pool
        self.repository = repository
        self._embedder: BaseEmbeddingProvider | None = None
        self._validated_search_model = False

    def _get_embedder(self) -> BaseEmbeddingProvider:
        """Lazy-load the embedding provider.

        Uses Osprey's provider configuration system to select the appropriate
        embedding provider based on config.embedding.provider.

        Returns:
            Configured embedding provider instance
        """
        if self._embedder is None:
            provider_name = self.config.embedding.provider

            # Dynamic provider selection based on config
            if provider_name == "ollama":
                from osprey.models.embeddings.ollama import OllamaEmbeddingProvider

                self._embedder = OllamaEmbeddingProvider()
            else:
                # For other providers, default to Ollama for now
                # Additional providers can be added here as they are implemented
                logger.warning(
                    f"Embedding provider '{provider_name}' not yet supported, "
                    f"falling back to 'ollama'"
                )
                from osprey.models.embeddings.ollama import OllamaEmbeddingProvider

                self._embedder = OllamaEmbeddingProvider()

        return self._embedder

    # === Validation ===

    async def _validate_search_model(self) -> None:
        """Validate that the configured search model's table exists.

        Called lazily on first semantic search.
        """
        if self._validated_search_model:
            return

        model = self.config.get_search_model()
        if model:
            await self.repository.validate_search_model_table(model)

        self._validated_search_model = True

    # === Pipeline Factory ===

    def _build_pipeline(self, mode: SearchMode) -> Pipeline:
        """Build a pipeline for the given search mode.

        Args:
            mode: Search mode to build pipeline for

        Returns:
            Configured Pipeline instance

        Raises:
            ConfigurationError: If required modules are not enabled
        """
        from osprey.services.ariel_search.pipeline import Pipeline
        from osprey.services.ariel_search.pipeline.assemblers import (
            ContextWindowAssembler,
            TopKAssembler,
        )
        from osprey.services.ariel_search.pipeline.formatters import (
            CitationFormatter,
            JSONFormatter,
        )
        from osprey.services.ariel_search.pipeline.processors import (
            IdentityProcessor,
            SingleLLMProcessor,
        )
        from osprey.services.ariel_search.pipeline.retrievers import (
            HybridRetriever,
            KeywordRetriever,
            RRFFusion,
            SemanticRetriever,
        )

        match mode:
            case SearchMode.KEYWORD:
                if not self.config.is_search_module_enabled("keyword"):
                    raise ConfigurationError(
                        "Keyword search module not enabled",
                        config_key="search_modules.keyword.enabled",
                    )
                return Pipeline(
                    retriever=KeywordRetriever(self.repository, self.config),
                    assembler=TopKAssembler(),
                    processor=IdentityProcessor(),
                    formatter=JSONFormatter(),
                )

            case SearchMode.SEMANTIC:
                if not self.config.is_search_module_enabled("semantic"):
                    raise ConfigurationError(
                        "Semantic search module not enabled",
                        config_key="search_modules.semantic.enabled",
                    )
                return Pipeline(
                    retriever=SemanticRetriever(self.repository, self.config, self._get_embedder()),
                    assembler=TopKAssembler(),
                    processor=IdentityProcessor(),
                    formatter=JSONFormatter(),
                )

            case SearchMode.RAG:
                if not self.config.is_search_module_enabled("semantic"):
                    raise ConfigurationError(
                        "Semantic search module required for RAG mode",
                        config_key="search_modules.semantic.enabled",
                    )
                return Pipeline(
                    retriever=SemanticRetriever(self.repository, self.config, self._get_embedder()),
                    assembler=ContextWindowAssembler(),
                    processor=SingleLLMProcessor(),
                    formatter=CitationFormatter(),
                )

            case SearchMode.MULTI:
                # Build hybrid retriever with available retrievers
                retrievers = []
                if self.config.is_search_module_enabled("keyword"):
                    retrievers.append(KeywordRetriever(self.repository, self.config))
                if self.config.is_search_module_enabled("semantic"):
                    retrievers.append(
                        SemanticRetriever(self.repository, self.config, self._get_embedder())
                    )

                if not retrievers:
                    raise ConfigurationError(
                        "No search modules enabled for MULTI mode",
                        config_key="search_modules",
                    )

                return Pipeline(
                    retriever=HybridRetriever(retrievers, RRFFusion()),
                    assembler=TopKAssembler(),
                    processor=IdentityProcessor(),
                    formatter=JSONFormatter(),
                )

            case _:
                # AGENT and VISION modes are not handled by pipeline
                raise ConfigurationError(
                    f"Mode {mode.value} is not supported by pipeline",
                    config_key="modes",
                )

    # === Main Search Interface ===

    async def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        time_range: tuple[Any, Any] | None = None,
        mode: SearchMode | None = None,
    ) -> ARIELSearchResult:
        """Execute a search using ARIEL pipelines or agent.

        This is the main entry point for searching the logbook.
        Routes to Pipeline (deterministic) or AgentExecutor (agentic)
        based on the search mode.

        Args:
            query: Natural language query
            max_results: Maximum results (default from config)
            time_range: Optional (start, end) datetime tuple
            mode: Optional search mode (default: MULTI)

        Returns:
            ARIELSearchResult with entries, answer, and sources
        """
        # Build the search request
        request = ARIELSearchRequest(
            query=query,
            max_results=max_results or self.config.default_max_results,
            time_range=time_range,
            modes=[mode] if mode else [SearchMode.MULTI],
        )

        return await self.ainvoke(request)

    async def ainvoke(
        self,
        request: ARIELSearchRequest,
    ) -> ARIELSearchResult:
        """Invoke ARIEL with a search request.

        Routes to either Pipeline or AgentExecutor based on mode:
        - KEYWORD, SEMANTIC, RAG, MULTI: Pipeline (deterministic)
        - AGENT: AgentExecutor (agentic orchestration)

        Args:
            request: Search request with query and parameters

        Returns:
            ARIELSearchResult with entries, answer, and sources
        """
        try:
            # Validate search model table on first call (if semantic enabled)
            if self.config.is_search_module_enabled("semantic"):
                await self._validate_search_model()

            # Get the mode (first mode in list, default to MULTI)
            mode = request.modes[0] if request.modes else SearchMode.MULTI

            if mode == SearchMode.AGENT:
                # Route to AgentExecutor for agentic orchestration
                return await self._run_agent_executor(request)
            else:
                # Route to Pipeline for deterministic search
                return await self._run_pipeline(request, mode)

        except SearchTimeoutError as e:
            # Return graceful timeout result instead of propagating exception
            return ARIELSearchResult(
                entries=(),
                answer=None,
                sources=(),
                search_modes_used=(),
                reasoning=(
                    f"Search timed out before completion. "
                    f"{e.operation} timeout ({e.timeout_seconds}s) exceeded"
                ),
            )
        except ARIELException:
            raise
        except Exception as e:
            logger.exception(f"Search failed: {e}")
            mode = request.modes[0] if request.modes else SearchMode.MULTI
            raise SearchExecutionError(
                f"Search execution failed: {e}",
                search_mode=mode.value,
                query=request.query,
            ) from e

    async def _run_pipeline(
        self,
        request: ARIELSearchRequest,
        mode: SearchMode,
    ) -> ARIELSearchResult:
        """Run a search pipeline for the given mode.

        Args:
            request: Search request
            mode: Search mode (KEYWORD, SEMANTIC, RAG, or MULTI)

        Returns:
            ARIELSearchResult
        """
        from osprey.services.ariel_search.pipeline import PipelineConfig
        from osprey.services.ariel_search.pipeline.types import (
            ProcessorConfig,
            RetrievalConfig,
        )

        # Build the pipeline for this mode
        pipeline = self._build_pipeline(mode)

        # Build pipeline config from request
        retrieval_config = RetrievalConfig(
            max_results=request.max_results,
            start_date=request.time_range[0] if request.time_range else None,
            end_date=request.time_range[1] if request.time_range else None,
        )

        # Build processor config for RAG mode
        processor_config = ProcessorConfig(
            provider=self.config.reasoning.provider,
            model_id=self.config.reasoning.model_id,
            temperature=self.config.reasoning.temperature,
        )

        pipeline_config = PipelineConfig(
            retrieval=retrieval_config,
            processor=processor_config,
        )

        # Execute pipeline
        result = await pipeline.execute(request.query, pipeline_config)

        # Convert pipeline result to ARIELSearchResult
        return self._convert_pipeline_result(result, mode)

    def _convert_pipeline_result(
        self,
        result: Any,  # PipelineResult
        mode: SearchMode,
    ) -> ARIELSearchResult:
        """Convert pipeline result to ARIELSearchResult.

        Args:
            result: PipelineResult from pipeline execution
            mode: Search mode used

        Returns:
            ARIELSearchResult
        """
        response = result.response

        # Extract entries from response content
        entries = []
        sources = []
        answer = None

        if response.format_type == "json" and isinstance(response.content, dict):
            # JSON format from IdentityProcessor
            items = response.content.get("items", [])
            for item in items:
                entry = item.get("entry", {})
                entries.append(entry)
                if entry_id := entry.get("entry_id"):
                    sources.append(entry_id)
        elif response.format_type == "citation" and isinstance(response.content, str):
            # Citation format from SingleLLMProcessor (RAG)
            answer = response.content
            # Extract sources from metadata
            sources = response.metadata.get("citations", [])
            # Get entries from metadata if available
            items = response.metadata.get("items", [])
            entries = [item.get("entry", {}) for item in items if item.get("entry")]

        return ARIELSearchResult(
            entries=tuple(entries),
            answer=answer,
            sources=tuple(sources),
            search_modes_used=(mode,),
            reasoning=f"Pipeline execution: {result.processor_type}",
        )

    async def _run_agent_executor(
        self,
        request: ARIELSearchRequest,
    ) -> ARIELSearchResult:
        """Run the AgentExecutor for agentic search.

        Args:
            request: Search request

        Returns:
            ARIELSearchResult
        """
        from osprey.services.ariel_search.agent import AgentExecutor

        # Create agent executor
        executor = AgentExecutor(
            repository=self.repository,
            config=self.config,
            embedder_loader=self._get_embedder,
        )

        # Execute agent
        agent_result = await executor.execute(
            query=request.query,
            max_results=request.max_results,
            time_range=request.time_range,
        )

        # Convert agent result to ARIELSearchResult
        return ARIELSearchResult(
            entries=agent_result.entries,
            answer=agent_result.answer,
            sources=agent_result.sources,
            search_modes_used=agent_result.search_modes_used,
            reasoning=agent_result.reasoning,
        )

    # === Health Check ===

    async def health_check(self) -> tuple[bool, str]:
        """Check service health.

        Returns:
            Tuple of (healthy, message)
        """
        # Check database
        db_healthy, db_msg = await self.repository.health_check()
        if not db_healthy:
            return (False, f"Database: {db_msg}")

        return (True, "ARIEL service healthy")

    async def get_status(self) -> ARIELStatusResult:
        """Get detailed ARIEL service status.

        Returns comprehensive service state including database connectivity,
        entry counts, embedding tables, and enabled modules.

        Returns:
            ARIELStatusResult with comprehensive service state.
        """
        errors: list[str] = []
        database_connected = False
        entry_count = None
        embedding_tables: list[EmbeddingTableInfo] = []
        last_ingestion = None

        # Mask database URI for security
        masked_uri = self._mask_database_uri(self.config.database.uri)

        # Check database connectivity and gather stats
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    database_connected = True

                    # Get entry count
                    await cur.execute("SELECT COUNT(*) FROM enhanced_entries")
                    row = await cur.fetchone()
                    entry_count = row[0] if row else 0

                    # Get embedding tables info
                    embedding_tables = await self.repository.get_embedding_tables()

                    # Get last ingestion time
                    await cur.execute(
                        "SELECT MAX(completed_at) FROM ingestion_runs WHERE status = 'success'"
                    )
                    row = await cur.fetchone()
                    if row and row[0]:
                        last_ingestion = row[0]

        except Exception as e:
            errors.append(f"Database error: {e}")

        # Get active embedding model from config
        active_model = self.config.get_search_model()

        return ARIELStatusResult(
            healthy=database_connected and len(errors) == 0,
            database_connected=database_connected,
            database_uri=masked_uri,
            entry_count=entry_count,
            embedding_tables=embedding_tables,
            active_embedding_model=active_model,
            enabled_search_modules=self.config.get_enabled_search_modules(),
            enabled_enhancement_modules=self.config.get_enabled_enhancement_modules(),
            last_ingestion=last_ingestion,
            errors=errors,
        )

    def _mask_database_uri(self, uri: str) -> str:
        """Mask credentials in database URI for display.

        postgresql://user:password@host:5432/db -> postgresql://***@host:5432/db
        """
        import re

        return re.sub(r"://[^@]+@", "://***@", uri)

    # === Context Manager ===

    async def __aenter__(self) -> ARIELSearchService:
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context and cleanup."""
        # Close the connection pool
        await self.pool.close()


async def create_ariel_service(
    config: ARIELConfig,
) -> ARIELSearchService:
    """Create and initialize an ARIEL search service.

    Factory function that sets up the database pool and repository.

    Args:
        config: ARIEL configuration

    Returns:
        Initialized ARIELSearchService

    Usage:
        async with create_ariel_service(config) as service:
            result = await service.search("What happened?")
    """
    from osprey.services.ariel_search.database.connection import create_connection_pool
    from osprey.services.ariel_search.database.repository import ARIELRepository

    # Create connection pool
    pool = await create_connection_pool(config.database)

    # Create repository
    repository = ARIELRepository(pool, config)

    # Create and return service
    return ARIELSearchService(
        config=config,
        pool=pool,
        repository=repository,
    )


__all__ = [
    "ARIELSearchService",
    "create_ariel_service",
]
