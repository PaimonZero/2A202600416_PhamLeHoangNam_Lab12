#!/usr/bin/env python3
"""
Phase 5 Production Readiness Verification

Checks:
1. All required files exist
2. Docker configuration valid
3. Environment variables present
4. Security requirements met
5. Deployment configs ready
"""

import os
import sys
import json
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_file_exists(path, description):
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description:45} {path}")
    return exists

def safe_read_file(path):
    """Read file with UTF-8 encoding, fallback to Latin-1."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()

def check_directory_structure():
    """Verify all required directories and files."""
    print_header("1. Directory Structure")
    
    checks = [
        ("app/__init__.py", "App package"),
        ("app/main.py", "Main FastAPI app"),
        ("app/agent.py", "LangGraph agent"),
        ("app/tools.py", "Travel tools"),
        ("app/config.py", "Configuration"),
        ("app/auth.py", "Authentication"),
        ("app/rate_limiter.py", "Rate limiter"),
        ("app/cost_guard.py", "Cost guard"),
        ("app/system_prompt.txt", "Agent system prompt"),
        ("Dockerfile.prod", "Production Dockerfile"),
        ("docker-compose.prod.yml", "Production Docker Compose"),
        ("nginx.conf", "Nginx configuration"),
        ("requirements.txt", "Python requirements"),
        ("test_integration.py", "Integration tests"),
        ("test_manual.py", "Manual API tests"),
        ("DEPLOYMENT.md", "Deployment guide"),
        ("README.md", "Project README"),
        (".env.production", "Production environment template"),
    ]
    
    results = [check_file_exists(path, desc) for path, desc in checks]
    return all(results)

def check_docker_config():
    """Verify Docker configuration."""
    print_header("2. Docker Configuration")
    
    all_ok = True
    
    # Check Dockerfile
    if Path("Dockerfile.prod").exists():
        content = safe_read_file("Dockerfile.prod")
        checks = [
            ("python:3.11-slim" in content, "Python 3.11 base image"),
            ("multi-stage" in content.lower() or "as builder" in content, "Multi-stage build"),
            ("USER" in content, "Non-root user"),
            ("HEALTHCHECK" in content, "Health check configured"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check docker-compose
    if Path("docker-compose.prod.yml").exists():
        content = safe_read_file("docker-compose.prod.yml")
        checks = [
            ("app:" in content, "App service"),
            ("redis:" in content, "Redis service"),
            ("nginx:" in content, "Nginx service"),
            ("environment:" in content, "Environment variables"),
            ("healthcheck:" in content, "Health checks"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def check_security():
    """Verify security configuration."""
    print_header("3. Security Requirements")
    
    all_ok = True
    
    # Check auth.py
    if Path("app/auth.py").exists():
        content = safe_read_file("app/auth.py")
        checks = [
            ("verify_api_key" in content, "API Key verification"),
            ("create_token" in content, "JWT token creation"),
            ("verify_token" in content, "JWT token verification"),
            ("HTTPException" in content, "HTTP exception handling"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check rate_limiter.py
    if Path("app/rate_limiter.py").exists():
        content = safe_read_file("app/rate_limiter.py")
        checks = [
            ("RateLimiter" in content, "Rate limiter class"),
            ("429" in content, "Rate limit HTTP error"),
            ("check" in content, "Rate check method"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check cost_guard.py
    if Path("app/cost_guard.py").exists():
        content = safe_read_file("app/cost_guard.py")
        checks = [
            ("CostGuard" in content, "Cost guard class"),
            ("daily_budget" in content, "Daily budget tracking"),
            ("402" in content, "Budget exceeded HTTP error"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check nginx security headers
    if Path("nginx.conf").exists():
        content = safe_read_file("nginx.conf")
        checks = [
            ("X-Content-Type-Options" in content, "X-Content-Type-Options header"),
            ("X-Frame-Options" in content, "X-Frame-Options header"),
            ("ssl" in content, "SSL/TLS configuration"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def check_environment():
    """Verify environment configuration."""
    print_header("4. Environment Configuration")
    
    all_ok = True
    
    # Check .env.production
    if Path(".env.production").exists():
        content = safe_read_file(".env.production")
        checks = [
            ("OPENAI_API_KEY" in content or "GITHUB_PAT" in content, "LLM API key"),
            ("AGENT_API_KEY" in content, "Agent API key"),
            ("JWT_SECRET" in content, "JWT secret"),
            ("ENVIRONMENT" in content, "Environment variable"),
            ("DEBUG" in content, "Debug flag"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def check_testing():
    """Verify testing configuration."""
    print_header("5. Testing Setup")
    
    all_ok = True
    
    # Check integration tests
    if Path("test_integration.py").exists():
        content = safe_read_file("test_integration.py")
        checks = [
            ("pytest" in content, "Pytest framework"),
            ("TestAuthentication" in content, "Auth tests"),
            ("TestEndpoints" in content, "Endpoint tests"),
            ("TestRateLimiting" in content, "Rate limit tests"),
            ("TestCostTracking" in content, "Cost tracking tests"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check manual tests
    if Path("test_manual.py").exists():
        content = safe_read_file("test_manual.py")
        checks = [
            ("test_health_check" in content, "Health check test"),
            ("test_ask_travel_question" in content, "Travel question test"),
            ("test_get_chat_history" in content, "History test"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def check_deployment():
    """Verify deployment configuration."""
    print_header("6. Deployment Configuration")
    
    all_ok = True
    
    # Check DEPLOYMENT.md
    if Path("DEPLOYMENT.md").exists():
        content = safe_read_file("DEPLOYMENT.md")
        checks = [
            ("Docker" in content, "Docker instructions"),
            ("Railway" in content, "Railway deployment"),
            ("Render" in content, "Render deployment"),
            ("AWS" in content or "ECS" in content, "AWS deployment"),
            ("Google Cloud" in content or "GCP" in content, "GCP deployment"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    # Check README
    if Path("README.md").exists():
        content = safe_read_file("README.md")
        checks = [
            ("Quick Start" in content or "Getting Started" in content, "Getting started guide"),
            ("API" in content, "API documentation"),
            ("Docker" in content, "Docker instructions"),
            ("Deployment" in content, "Deployment info"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def check_dependencies():
    """Verify Python dependencies."""
    print_header("7. Python Dependencies")
    
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    content = safe_read_file("requirements.txt")
    
    required_packages = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("pyjwt", "JWT tokens"),
        ("python-dotenv", "Environment config"),
        ("langchain", "LangChain framework"),
        ("langgraph", "LangGraph agent"),
        ("langchain-openai", "OpenAI integration"),
    ]
    
    all_ok = True
    for package, desc in required_packages:
        check = package in content
        status = "✅" if check else "❌"
        print(f"{status} {desc:30} ({package})")
        all_ok = all_ok and check
    
    return all_ok

def check_app_structure():
    """Verify app internal structure."""
    print_header("8. Application Structure")
    
    all_ok = True
    
    # Check main.py
    if Path("app/main.py").exists():
        content = safe_read_file("app/main.py")
        checks = [
            ("FastAPI" in content, "FastAPI app"),
            ("create_agent" in content, "Agent integration"),
            ("verify_api_key" in content, "API key auth"),
            ("ChatSession" in content, "Session management"),
            ("/ask" in content, "Ask endpoint"),
            ("/chat" in content, "Chat endpoints"),
            ("/health" in content, "Health endpoint"),
        ]
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
            all_ok = all_ok and check
    
    return all_ok

def main():
    """Run all checks."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "PHASE 5: PRODUCTION READINESS VERIFICATION" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = {
        "Directory Structure": check_directory_structure(),
        "Docker Configuration": check_docker_config(),
        "Security Requirements": check_security(),
        "Environment Configuration": check_environment(),
        "Testing Setup": check_testing(),
        "Deployment Configuration": check_deployment(),
        "Python Dependencies": check_dependencies(),
        "Application Structure": check_app_structure(),
    }
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:15} {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - PRODUCTION READY!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Set actual values in .env.production")
        print("  2. Generate SSL certificates")
        print("  3. Deploy: docker-compose -f docker-compose.prod.yml up")
        print("  4. Verify: curl https://localhost/health")
        print("\nSee DEPLOYMENT.md for full deployment guide.")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review above for details")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
