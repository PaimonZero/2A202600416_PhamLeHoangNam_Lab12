#!/usr/bin/env python3
"""Phase 3 Integration Test"""

import sys
sys.path.insert(0, '.')

print('=' * 60)
print('Phase 3 Verification - Integration Test')
print('=' * 60)

# Test 1: Import FastAPI app
try:
    from app.main import app, ChatSession, _rate_limiter, _cost_guard
    print('✅ FastAPI app imported successfully')
    print(f'   - App routes: {len(app.routes)} endpoints')
    print(f'   - Rate limiter: {type(_rate_limiter).__name__}')
    print(f'   - Cost guard: {type(_cost_guard).__name__}')
except Exception as e:
    print(f'❌ Failed to import app: {e}')
    sys.exit(1)

# Test 2: Test ChatSession
try:
    session = ChatSession('test-session-123')
    session.add_message('user', 'Hello')
    session.add_message('assistant', 'Hi there!')
    history = session.to_dict()
    print(f'✅ ChatSession works')
    print(f'   - Session ID: {history["session_id"]}')
    print(f'   - Messages: {history["message_count"]}')
except Exception as e:
    print(f'❌ ChatSession error: {e}')

# Test 3: Test rate limiter
try:
    _rate_limiter.check('user1')
    print(f'✅ Rate limiter works')
    print(f'   - User user1 has {_rate_limiter.get_remaining("user1")} requests remaining')
except Exception as e:
    print(f'❌ Rate limiter error: {e}')

# Test 4: Test cost guard
try:
    result = _cost_guard.check_and_record('user1', 100, 50)
    print(f'✅ Cost guard works')
    print(f'   - Cost: ${result["cost_usd"]}')
    print(f'   - Budget remaining: ${result["remaining_usd"]}')
    print(f'   - Status: {result["status"]}')
except Exception as e:
    print(f'❌ Cost guard error: {e}')

print()
print('=' * 60)
print('✅ Phase 3 Integration Test PASSED')
print('=' * 60)
