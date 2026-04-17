#!/usr/bin/env python3
"""
Phase 3 Verification Script

Tests:
1. All imports resolve correctly
2. Module syntax is valid
3. Key classes and functions exist
4. Agent can be initialized
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports."""
    print("=" * 60)
    print("PHASE 3 VERIFICATION - Testing Imports")
    print("=" * 60)
    
    tests = {
        "config": "from app.config import settings",
        "auth": "from app.auth import verify_api_key",
        "rate_limiter": "from app.rate_limiter import get_rate_limiter",
        "cost_guard": "from app.cost_guard import get_cost_guard",
        "agent": "from app.agent import create_agent",
        "tools": "from app.tools import search_flights, search_hotels, calculate_budget",
        "main": "from app.main import app",
    }
    
    results = {}
    for name, import_stmt in tests.items():
        try:
            exec(import_stmt)
            results[name] = "✅ PASS"
            print(f"✅ {name:20} - {import_stmt}")
        except Exception as e:
            results[name] = f"❌ FAIL: {str(e)[:50]}"
            print(f"❌ {name:20} - {import_stmt}")
            print(f"   Error: {e}")
    
    return all(v.startswith("✅") for v in results.values())


def test_modules_syntax():
    """Test syntax of key modules."""
    print("\n" + "=" * 60)
    print("Testing Module Syntax")
    print("=" * 60)
    
    modules = [
        "app.config",
        "app.auth",
        "app.rate_limiter",
        "app.cost_guard",
        "app.tools",
        "app.agent",
        "app.main",
    ]
    
    import py_compile
    results = {}
    
    for module in modules:
        file_path = module.replace(".", "/") + ".py"
        file_path = f"06-lab-complete/{file_path}"
        
        try:
            py_compile.compile(file_path, doraise=True)
            results[module] = "✅ PASS"
            print(f"✅ {module:30} - Syntax valid")
        except py_compile.PyCompileError as e:
            results[module] = f"❌ FAIL"
            print(f"❌ {module:30} - {str(e)[:50]}")
    
    return all(v.startswith("✅") for v in results.values())


def test_classes_exist():
    """Test that key classes and functions exist."""
    print("\n" + "=" * 60)
    print("Testing Classes and Functions")
    print("=" * 60)
    
    tests = {
        "ChatSession": "from app.main import ChatSession",
        "AskRequest": "from app.main import AskRequest",
        "AskResponse": "from app.main import AskResponse",
        "RateLimiter": "from app.rate_limiter import RateLimiter",
        "CostGuard": "from app.cost_guard import CostGuard",
        "UsageRecord": "from app.cost_guard import UsageRecord",
        "create_agent": "from app.agent import create_agent",
        "verify_api_key": "from app.auth import verify_api_key",
        "create_token": "from app.auth import create_token",
        "search_flights": "from app.tools import search_flights",
    }
    
    results = {}
    for name, import_stmt in tests.items():
        try:
            exec(import_stmt)
            results[name] = "✅ PASS"
            print(f"✅ {name:25} exists")
        except Exception as e:
            results[name] = "❌ FAIL"
            print(f"❌ {name:25} - Error: {str(e)[:50]}")
    
    return all(v.startswith("✅") for v in results.values())


def test_agent_init():
    """Test agent initialization."""
    print("\n" + "=" * 60)
    print("Testing Agent Initialization")
    print("=" * 60)
    
    try:
        # Set mock API key
        os.environ["OPENAI_API_KEY"] = "sk-test-123456789"
        
        from app.agent import create_agent
        agent, memory = create_agent()
        print("✅ Agent created successfully")
        print(f"   - Agent type: {type(agent).__name__}")
        print(f"   - Memory saver: {type(memory).__name__}")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    os.chdir("06-lab-complete")
    
    test_results = {
        "Imports": test_imports(),
        "Syntax": test_modules_syntax(),
        "Classes": test_classes_exist(),
        "Agent": test_agent_init(),
    }
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(test_results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL PHASE 3 TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review above for details")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
