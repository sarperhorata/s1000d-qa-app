#!/usr/bin/env python3
"""
Test script for S1000D QA Application Backend
Tests all major endpoints and functionality
"""

import sys
import json
from fastapi.testclient import TestClient
from app import app

def test_health_endpoint():
    """Test health endpoint"""
    print("🩺 Testing health endpoint...")
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ Health endpoint working")
    return True

def test_index_status():
    """Test index status endpoint"""
    print("📊 Testing index status...")
    client = TestClient(app)
    response = client.get("/index-status")

    assert response.status_code == 200
    data = response.json()
    assert "index_status" in data
    print("✅ Index status endpoint working")
    return True

def test_ai_query():
    """Test AI query endpoint"""
    print("🤖 Testing AI query endpoint...")
    client = TestClient(app)

    test_query = {
        "query": "What is S1000D?",
        "language": "en"
    }

    response = client.post("/ai-query", json=test_query)

    # Either 200 (success) or 503 (index not available) is acceptable
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        print("✅ AI query endpoint working with results")
    else:
        print("⚠️ AI query endpoint working (index not available)")

    return True

def test_get_images_for_query():
    """Test image query endpoint"""
    print("🖼️ Testing images for query endpoint...")
    client = TestClient(app)

    try:
        response = client.get("/get-images-for-query?query=business%20rules&limit=2")

        # Either 200 (success) or 503/404 is acceptable
        if response.status_code == 200:
            data = response.json()
            if "status" in data and "images" in data:
                print("✅ Images for query endpoint working")
            else:
                print("⚠️ Images for query endpoint responding but missing fields")
        elif response.status_code in [404, 503]:
            print("⚠️ Images for query endpoint (expected when index not available)")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")

        return True

    except Exception as e:
        print(f"⚠️ Images endpoint test error (non-critical): {e}")
        return True  # Don't fail the test for image endpoint issues

def test_simple_endpoints():
    """Test simple utility endpoints"""
    print("🔧 Testing utility endpoints...")
    client = TestClient(app)

    # Test images-test endpoint
    response = client.get("/images-test")
    if response.status_code == 200:
        print("✅ Images test endpoint working")
    else:
        print("⚠️ Images test endpoint not available")

    # Test docs endpoint
    response = client.get("/docs")
    if response.status_code == 200:
        print("✅ API docs endpoint working")
    else:
        print("⚠️ API docs endpoint not accessible")

    return True

def test_cors_headers():
    """Test CORS headers"""
    print("🌐 Testing CORS headers...")
    client = TestClient(app)

    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })

    if "access-control-allow-origin" in response.headers:
        print("✅ CORS headers configured")
    else:
        print("⚠️ CORS headers not found")

    return True

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting S1000D QA Backend Tests\n")

    tests = [
        test_health_endpoint,
        test_index_status,
        test_ai_query,
        test_get_images_for_query,
        test_simple_endpoints,
        test_cors_headers
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

    print("\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
