"""Tests for ARIEL web API routes."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from osprey.interfaces.ariel.api import routes


@pytest.fixture
def mock_ariel_service():
    """Mock ARIEL service."""
    service = AsyncMock()
    service.health_check = AsyncMock(return_value=(True, "Service healthy"))
    service.repository = AsyncMock()

    # Mock search result
    mock_result = MagicMock()
    mock_result.entries = []
    mock_result.answer = "Test answer"
    mock_result.sources = []
    mock_result.search_modes_used = []
    mock_result.reasoning = ""
    service.search = AsyncMock(return_value=mock_result)

    # Mock status
    mock_status = MagicMock()
    mock_status.healthy = True
    mock_status.database_connected = True
    mock_status.database_uri = "postgresql://localhost/ariel"
    mock_status.entry_count = 100
    mock_status.embedding_tables = []
    mock_status.active_embedding_model = "text-embedding-3-small"
    mock_status.enabled_search_modules = ["keyword", "semantic"]
    mock_status.enabled_enhancement_modules = []
    mock_status.last_ingestion = None
    mock_status.errors = []
    service.get_status = AsyncMock(return_value=mock_status)

    return service


@pytest.fixture
def test_app(mock_ariel_service):
    """Create a test FastAPI app with mocked service."""
    app = FastAPI()

    # Add the router
    app.include_router(routes.router)

    # Mock the service in app state
    app.state.ariel_service = mock_ariel_service

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_search_endpoint_basic(client, mock_ariel_service):
    """Test basic search endpoint."""
    response = client.post(
        "/api/search",
        json={
            "query": "test query",
            "mode": "auto",
            "max_results": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "answer" in data
    assert data["answer"] == "Test answer"
    assert "execution_time_ms" in data

    # Verify service was called
    mock_ariel_service.search.assert_called_once()


def test_search_endpoint_with_time_range(client, mock_ariel_service):
    """Test search with time range filter."""
    response = client.post(
        "/api/search",
        json={
            "query": "test",
            "mode": "keyword",
            "max_results": 5,
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
        },
    )

    assert response.status_code == 200

    # Check that time_range was passed to service
    call_kwargs = mock_ariel_service.search.call_args.kwargs
    assert call_kwargs["time_range"] is not None


def test_search_endpoint_advanced_options(client, mock_ariel_service):
    """Test search with advanced options."""
    response = client.post(
        "/api/search",
        json={
            "query": "test",
            "mode": "semantic",
            "max_results": 10,
            "similarity_threshold": 0.7,
            "include_highlights": True,
            "assembly_max_items": 20,
            "temperature": 0.5,
        },
    )

    assert response.status_code == 200

    # Check that advanced params were passed
    call_kwargs = mock_ariel_service.search.call_args.kwargs
    assert call_kwargs["similarity_threshold"] == 0.7
    assert call_kwargs["include_highlights"] is True
    assert call_kwargs["assembly_max_items"] == 20
    assert call_kwargs["temperature"] == 0.5


def test_list_entries_endpoint(client, mock_ariel_service):
    """Test list entries endpoint."""
    # Mock repository methods
    mock_ariel_service.repository.count_entries = AsyncMock(return_value=100)
    mock_ariel_service.repository.search_by_time_range = AsyncMock(return_value=[])

    response = client.get("/api/entries?page=1&page_size=20")

    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data
    assert data["total"] == 100
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data


def test_get_entry_endpoint(client, mock_ariel_service):
    """Test get single entry endpoint."""
    # Mock entry
    mock_entry = {
        "entry_id": "test-123",
        "source_system": "Test",
        "timestamp": datetime.now(),
        "author": "Test Author",
        "raw_text": "Test entry content",
        "attachments": [],
        "metadata": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "summary": None,
        "keywords": [],
    }
    mock_ariel_service.repository.get_entry = AsyncMock(return_value=mock_entry)

    response = client.get("/api/entries/test-123")

    assert response.status_code == 200
    data = response.json()
    assert data["entry_id"] == "test-123"
    assert data["author"] == "Test Author"


def test_get_entry_not_found(client, mock_ariel_service):
    """Test get entry returns 404 when not found."""
    mock_ariel_service.repository.get_entry = AsyncMock(return_value=None)

    response = client.get("/api/entries/nonexistent")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_entry_endpoint(client, mock_ariel_service):
    """Test create entry endpoint."""
    mock_ariel_service.repository.upsert_entry = AsyncMock()

    response = client.post(
        "/api/entries",
        json={
            "subject": "Test Entry",
            "details": "Test details",
            "author": "Test Author",
            "logbook": "Test Logbook",
            "tags": ["test", "example"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "entry_id" in data
    assert data["entry_id"].startswith("ariel-")
    assert "message" in data

    # Verify repository was called
    mock_ariel_service.repository.upsert_entry.assert_called_once()


def test_status_endpoint(client, mock_ariel_service):
    """Test status endpoint."""
    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert data["database_connected"] is True
    assert data["entry_count"] == 100
    assert data["active_embedding_model"] == "text-embedding-3-small"
    assert "keyword" in data["enabled_search_modules"]


def test_entry_to_response_helper():
    """Test _entry_to_response helper function."""
    entry = {
        "entry_id": "test-123",
        "source_system": "Test",
        "timestamp": datetime(2024, 1, 1, 12, 0, 0),
        "author": "Test Author",
        "raw_text": "Test content",
        "attachments": [],
        "metadata": {"key": "value"},
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
        "summary": "Test summary",
        "keywords": ["test"],
    }

    result = routes._entry_to_response(entry, score=0.95, highlights=["highlight1"])

    assert result.entry_id == "test-123"
    assert result.author == "Test Author"
    assert result.score == 0.95
    assert result.highlights == ["highlight1"]
    assert result.metadata == {"key": "value"}


def test_search_mode_mapping(client, mock_ariel_service):
    """Test that search modes are correctly mapped."""
    from osprey.services.ariel_search.models import SearchMode as ServiceSearchMode

    # Test each mode
    modes = {
        "keyword": ServiceSearchMode.KEYWORD,
        "semantic": ServiceSearchMode.SEMANTIC,
        "rag": ServiceSearchMode.RAG,
        "multi": ServiceSearchMode.MULTI,
        "agent": ServiceSearchMode.AGENT,
    }

    for api_mode, expected_service_mode in modes.items():
        client.post(
            "/api/search",
            json={
                "query": "test",
                "mode": api_mode,
                "max_results": 10,
            },
        )

        # Check that correct mode was passed
        call_kwargs = mock_ariel_service.search.call_args.kwargs
        assert call_kwargs["mode"] == expected_service_mode


def test_search_auto_mode(client, mock_ariel_service):
    """Test that auto mode passes None to service."""
    client.post(
        "/api/search",
        json={
            "query": "test",
            "mode": "auto",
            "max_results": 10,
        },
    )

    # Auto mode should pass None
    call_kwargs = mock_ariel_service.search.call_args.kwargs
    assert call_kwargs["mode"] is None
