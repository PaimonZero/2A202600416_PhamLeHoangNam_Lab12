#!/usr/bin/env python3
"""
Phase 4: Manual API Testing Script

Simulates realistic API usage patterns:
1. Health check
2. Ask a travel question
3. View conversation history
4. Check metrics
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_response(response, title="Response"):
    """Pretty print HTTP response."""
    print(f"\n{title}:")
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        print(f"  Body:\n{json.dumps(data, indent=4, ensure_ascii=False)}")
    except:
        print(f"  Body: {response.text}")

def test_health_check():
    """Test 1: Health check endpoint."""
    print_section("Test 1: Health Check")
    print("GET /health")
    
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("\n✅ Health check passed")
    return True

def test_readiness_check():
    """Test 2: Readiness check."""
    print_section("Test 2: Readiness Check")
    print("GET /ready")
    
    response = requests.get(f"{BASE_URL}/ready")
    print_response(response)
    
    assert response.status_code == 200
    assert response.json()["ready"] is True
    print("\n✅ Readiness check passed")
    return True

def test_ask_travel_question():
    """Test 3: Ask a travel question."""
    print_section("Test 3: Ask Travel Question")
    print("POST /ask")
    
    payload = {
        "question": "Tôi muốn đi du lịch từ Hà Nội đến Đà Nẵng với ngân sách 5 triệu đồng. Bạn có thể giúp tôi tìm chuyến bay và khách sạn không?"
    }
    print(f"  Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/ask",
        json=payload,
        headers=HEADERS
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "cost_usd" in data
    
    session_id = data["session_id"]
    print(f"\n✅ Question asked successfully")
    print(f"   Session ID: {session_id}")
    print(f"   Cost: ${data['cost_usd']:.6f}")
    print(f"   Budget Remaining: ${data['budget_remaining_usd']:.6f}")
    
    return session_id

def test_follow_up_question(session_id):
    """Test 4: Follow-up question in same session."""
    print_section("Test 4: Follow-up Question (Same Session)")
    print("POST /ask (with session_id)")
    
    payload = {
        "question": "Khách sạn nào rẻ nhất trong khoảng 500,000 - 1,000,000 đồng/đêm?",
        "session_id": session_id
    }
    print(f"  Session ID: {session_id}")
    print(f"  Payload: {json.dumps(payload, indent=4, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/ask",
        json=payload,
        headers=HEADERS
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    
    print(f"\n✅ Follow-up question answered")
    print(f"   Cost: ${data['cost_usd']:.6f}")
    print(f"   Budget Remaining: ${data['budget_remaining_usd']:.6f}")
    return True

def test_get_chat_history(session_id):
    """Test 5: Get conversation history."""
    print_section("Test 5: Get Chat History")
    print(f"GET /chat/{session_id}/history")
    
    response = requests.get(
        f"{BASE_URL}/chat/{session_id}/history",
        headers=HEADERS
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "messages" in data
    assert len(data["messages"]) > 0
    
    print(f"\n✅ Chat history retrieved")
    print(f"   Total messages: {data['message_count']}")
    print(f"   Created: {data['created_at']}")
    print(f"   Last activity: {data['last_activity']}")
    
    # Print message summary
    print(f"\n   Message Summary:")
    for i, msg in enumerate(data["messages"][:4], 1):  # Show first 4
        role = msg["role"].upper()
        content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        print(f"   {i}. [{role}] {content}")
    
    if len(data["messages"]) > 4:
        print(f"   ... and {len(data['messages']) - 4} more messages")
    
    return True

def test_get_metrics():
    """Test 6: Get metrics."""
    print_section("Test 6: Get Metrics")
    print("GET /metrics")
    
    response = requests.get(
        f"{BASE_URL}/metrics",
        headers=HEADERS
    )
    print_response(response)
    
    assert response.status_code == 200
    data = response.json()
    assert "daily_cost_usd" in data
    assert "daily_budget_usd" in data
    
    print(f"\n✅ Metrics retrieved")
    print(f"   Uptime: {data['uptime_seconds']}s")
    print(f"   Total requests: {data['total_requests']}")
    print(f"   Daily cost: ${data['daily_cost_usd']:.6f}")
    print(f"   Daily budget: ${data['daily_budget_usd']:.2f}")
    print(f"   Budget used: {data['budget_used_pct']:.2f}%")
    
    return True

def test_error_missing_api_key():
    """Test 7: Error handling - missing API key."""
    print_section("Test 7: Error Handling - Missing API Key")
    print("GET /metrics (no X-API-Key header)")
    
    response = requests.get(f"{BASE_URL}/metrics")
    print_response(response)
    
    assert response.status_code == 401
    print("\n✅ Correctly rejected request without API key")
    return True

def test_error_invalid_api_key():
    """Test 8: Error handling - invalid API key."""
    print_section("Test 8: Error Handling - Invalid API Key")
    print("GET /metrics (with invalid X-API-Key)")
    
    bad_headers = {"X-API-Key": "invalid-key"}
    response = requests.get(
        f"{BASE_URL}/metrics",
        headers=bad_headers
    )
    print_response(response)
    
    assert response.status_code == 403
    print("\n✅ Correctly rejected request with invalid API key")
    return True

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 4: MANUAL API TESTING" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    print(f"\nConnecting to server...")
    
    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy\n")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure the server is running: python -m uvicorn app.main:app --reload")
        return False
    
    # Run tests
    try:
        test_health_check()
        time.sleep(0.5)
        
        test_readiness_check()
        time.sleep(0.5)
        
        session_id = test_ask_travel_question()
        time.sleep(0.5)
        
        test_follow_up_question(session_id)
        time.sleep(0.5)
        
        test_get_chat_history(session_id)
        time.sleep(0.5)
        
        test_get_metrics()
        time.sleep(0.5)
        
        test_error_missing_api_key()
        time.sleep(0.5)
        
        test_error_invalid_api_key()
        
        print_section("✅ ALL TESTS PASSED")
        print("\nSummary:")
        print("  ✅ Health check")
        print("  ✅ Readiness check")
        print("  ✅ Ask travel question")
        print("  ✅ Follow-up question with session")
        print("  ✅ Get chat history")
        print("  ✅ Get metrics")
        print("  ✅ Error handling (missing API key)")
        print("  ✅ Error handling (invalid API key)")
        print("\n" + "=" * 70 + "\n")
        
        return True
    
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
