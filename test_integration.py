#!/usr/bin/env python
"""Final integration test for MindHarbor Python 3.14 compatibility"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print('=' * 60)
print('MINDHARBOR FINAL VERIFICATION')
print('=' * 60)
print()

# Test 1: Imports
print('1. Testing module imports...')
try:
    from serve import app
    from db import init_db, get_or_create_user
    from vector_store import get_vector_store
    from utils import contains_crisis
    print('   ✓ All modules import successfully')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    exit(1)

# Test 2: Database
print()
print('2. Testing database operations...')
try:
    user = get_or_create_user('test_final')
    tokens = user.get('tokens_remaining')
    print(f'   ✓ User created/retrieved: tokens={tokens}')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    exit(1)

# Test 3: Vector store
print()
print('3. Testing vector store with RAG...')
try:
    store = get_vector_store()
    results = store.similarity_search('anxiety therapy', k=1)
    if results:
        print(f'   ✓ Retrieved {len(results)} document(s)')
        doc, sim = results[0]
        print(f'   ✓ Similarity score: {sim:.3f}')
    else:
        print('   ✓ Vector store initialized (no documents yet)')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    exit(1)

# Test 4: Crisis detection
print()
print('4. Testing crisis detection...')
try:
    crisis_msg = contains_crisis('I want to kill myself')
    normal_msg = contains_crisis('I feel sad')
    assert crisis_msg == True, "Crisis message not detected"
    assert normal_msg == False, "Normal message false positive"
    print('   ✓ Crisis detection working correctly')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    exit(1)

# Test 5: API
print()
print('5. Testing FastAPI endpoints...')
try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    health = client.get('/health')
    assert health.status_code == 200, f"Health check failed: {health.status_code}"
    print('   ✓ GET /health: 200')
    
    query = client.post('/query', json={'user_id': 'test', 'message': 'help'})
    assert query.status_code == 200, f"Query failed: {query.status_code}"
    print('   ✓ POST /query: 200')
    
    user_status = client.get('/user/test')
    assert user_status.status_code == 200, f"User status failed: {user_status.status_code}"
    print('   ✓ GET /user/{user_id}: 200')
except Exception as e:
    print(f'   ✗ ERROR: {e}')
    exit(1)

print()
print('=' * 60)
print('✓ ALL TESTS PASSED - System Ready for Deployment!')
print('=' * 60)
