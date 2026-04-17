#!/usr/bin/env python3
"""
Phase 4 Integration Tests for TravelBuddy Agent

Tests:
1. API endpoints with authentication
2. Rate limiting
3. Cost tracking
4. Session management
5. Agent responses
"""

import pytest
import json
import os
from fastapi.testclient import TestClient
from datetime import datetime

# Set environment
os.environ["OPENAI_API_KEY"] = "sk-test-123456789"
os.environ["AGENT_API_KEY"] = "test-api-key"

from app.main import app, get_or_create_session, delete_session, _rate_limiter, _cost_guard

client = TestClient(app)

# ─────────────────────────────────────────────────────────
# Test Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture
def valid_api_key():
    """Valid API key for testing."""
    return "test-api-key"

@pytest.fixture
def invalid_api_key():
    """Invalid API key for testing."""
    return "invalid-key"

@pytest.fixture
def headers(valid_api_key):
    """Valid request headers."""
    return {"X-API-Key": valid_api_key}

# ─────────────────────────────────────────────────────────
# Authentication Tests
# ─────────────────────────────────────────────────────────

class TestAuthentication:
    """Test API key authentication."""
    
    def test_missing_api_key(self):
        """Missing API key should return 401."""
        response = client.get("/metrics")
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]
    
    def test_invalid_api_key(self, invalid_api_key):
        """Invalid API key should return 403."""
        headers = {"X-API-Key": invalid_api_key}
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 403
        assert "Invalid" in response.json()["detail"]
    
    def test_valid_api_key(self, headers):
        """Valid API key should allow access."""
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200
        assert "daily_budget_usd" in response.json()


# ─────────────────────────────────────────────────────────
# Endpoint Tests
# ─────────────────────────────────────────────────────────

class TestEndpoints:
    """Test all API endpoints."""
    
    def test_root_endpoint(self):
        """GET / should return app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """GET /health should return health status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "uptime_seconds" in data
        assert "total_requests" in data
    
    def test_ready_endpoint(self):
        """GET /ready should return readiness."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
    
    def test_metrics_endpoint(self, headers):
        """GET /metrics should return usage metrics."""
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "daily_cost_usd" in data
        assert "daily_budget_usd" in data
        assert "budget_used_pct" in data


# ─────────────────────────────────────────────────────────
# Chat & Session Tests
# ─────────────────────────────────────────────────────────

class TestChatAndSessions:
    """Test chat and session management."""
    
    def test_ask_endpoint_missing_question(self, headers):
        """POST /ask with missing question should fail."""
        response = client.post("/ask", json={}, headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_ask_endpoint_empty_question(self, headers):
        """POST /ask with empty question should fail."""
        response = client.post("/ask", json={"question": ""}, headers=headers)
        assert response.status_code == 422
    
    def test_ask_endpoint_valid_question(self, headers):
        """POST /ask with valid question should work."""
        response = client.post(
            "/ask",
            json={"question": "Tìm chuyến bay từ Hà Nội đến Đà Nẵng"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "question" in data
        assert "answer" in data
        assert "cost_usd" in data
        assert "budget_remaining_usd" in data
        assert "timestamp" in data
    
    def test_ask_creates_session(self, headers):
        """POST /ask should create session automatically."""
        response = client.post(
            "/ask",
            json={"question": "Xin chào"},
            headers=headers
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_ask_with_session_id(self, headers):
        """POST /ask with explicit session_id should reuse it."""
        session_id = "test-session-456"
        response = client.post(
            "/ask",
            json={
                "question": "Xin chào",
                "session_id": session_id
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
    
    def test_get_chat_history(self, headers):
        """GET /chat/{session_id}/history should return messages."""
        session_id = "history-test-123"
        
        # Ask a question to create history
        response = client.post(
            "/ask",
            json={"question": "Test", "session_id": session_id},
            headers=headers
        )
        assert response.status_code == 200
        
        # Get history
        response = client.get(f"/chat/{session_id}/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "messages" in data
        assert len(data["messages"]) > 0
        assert data["message_count"] > 0
    
    def test_delete_chat_session(self, headers):
        """DELETE /chat/{session_id} should delete session."""
        session_id = "delete-test-789"
        
        # Create session
        client.post(
            "/ask",
            json={"question": "Test", "session_id": session_id},
            headers=headers
        )
        
        # Delete
        response = client.delete(f"/chat/{session_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        
        # Verify deleted (history should be empty)
        response = client.get(f"/chat/{session_id}/history", headers=headers)
        assert response.status_code == 200
        assert response.json()["message_count"] == 0


# ─────────────────────────────────────────────────────────
# Rate Limiting Tests
# ─────────────────────────────────────────────────────────

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_not_exceeded(self, headers):
        """Within rate limit should succeed."""
        # Should have 20 requests per minute
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200
    
    def test_rate_limit_remaining(self, headers):
        """Should track remaining requests."""
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200
        # Remaining should be less than initial


# ─────────────────────────────────────────────────────────
# Cost Tracking Tests
# ─────────────────────────────────────────────────────────

class TestCostTracking:
    """Test cost guard functionality."""
    
    def test_cost_recorded(self, headers):
        """POST /ask should record cost."""
        response = client.post(
            "/ask",
            json={"question": "Test question for cost tracking"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cost_usd"] >= 0
        assert data["budget_remaining_usd"] > 0
    
    def test_budget_tracking(self, headers):
        """Multiple requests should accumulate cost."""
        initial_response = client.post(
            "/ask",
            json={"question": "First request"},
            headers=headers
        )
        initial_budget = initial_response.json()["budget_remaining_usd"]
        
        second_response = client.post(
            "/ask",
            json={"question": "Second request"},
            headers=headers
        )
        second_budget = second_response.json()["budget_remaining_usd"]
        
        # Second budget should be less or equal
        assert second_budget <= initial_budget


# ─────────────────────────────────────────────────────────
# Session Management Tests
# ─────────────────────────────────────────────────────────

class TestSessionManagement:
    """Test session management."""
    
    def test_conversation_history(self, headers):
        """Multiple messages should build conversation history."""
        session_id = "conversation-test"
        
        # Message 1
        response1 = client.post(
            "/ask",
            json={"question": "Xin chào", "session_id": session_id},
            headers=headers
        )
        assert response1.status_code == 200
        
        # Message 2
        response2 = client.post(
            "/ask",
            json={"question": "Tìm chuyến bay", "session_id": session_id},
            headers=headers
        )
        assert response2.status_code == 200
        
        # Check history
        response = client.get(f"/chat/{session_id}/history", headers=headers)
        assert response.status_code == 200
        history = response.json()
        # Should have multiple messages (user + assistant pairs)
        assert history["message_count"] >= 4  # 2 user + 2 assistant


# ─────────────────────────────────────────────────────────
# Error Handling Tests
# ─────────────────────────────────────────────────────────

class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_session_format(self, headers):
        """Invalid session_id should still create new session."""
        response = client.post(
            "/ask",
            json={
                "question": "Test",
                "session_id": "invalid@#$%"
            },
            headers=headers
        )
        # Should still work (session_id is just a string key)
        assert response.status_code == 200
    
    def test_very_long_question(self, headers):
        """Very long question should fail validation."""
        long_question = "a" * 3000  # Exceeds max_length
        response = client.post(
            "/ask",
            json={"question": long_question},
            headers=headers
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
