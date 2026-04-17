#!/usr/bin/env python3
"""List all Phase 3 endpoints"""

from app.main import app

print('=' * 70)
print('PHASE 3 ENDPOINTS - FastAPI Routes')
print('=' * 70)

endpoints = []
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ', '.join(sorted(route.methods - {'OPTIONS', 'HEAD'}))
        endpoints.append((methods, route.path, route.name))

# Sort by path
endpoints.sort(key=lambda x: x[1])

for methods, path, name in endpoints:
    print(f'{methods:15} {path:30} -> {name}')

print()
print('=' * 70)
print(f'Total endpoints: {len(endpoints)}')
print('=' * 70)
