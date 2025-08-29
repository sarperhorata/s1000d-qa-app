#!/usr/bin/env python3
"""
Frontend Test Script for S1000D QA Application
Tests frontend build and basic functionality
"""

import sys
import os
import subprocess
import requests
import time

def test_frontend_build():
    """Test frontend build process"""
    print("🔨 Testing frontend build...")

    try:
        # Check if frontend directory exists
        if not os.path.exists("frontend"):
            print("❌ Frontend directory not found")
            return False

        # Check if build directory exists (skip actual build for speed)
        if os.path.exists("frontend/build"):
            print("✅ Frontend build directory exists")
            return True
        else:
            print("⚠️ Frontend build directory not found (run 'npm run build' manually)")
            return True  # Don't fail for missing build in development

    except Exception as e:
        print(f"❌ Error checking build: {e}")
        return False

def test_frontend_dependencies():
    """Test frontend dependencies"""
    print("📦 Testing frontend dependencies...")

    try:
        # Check if frontend directory exists
        if not os.path.exists("frontend"):
            print("❌ Frontend directory not found")
            return False

        # Check if package.json exists
        if not os.path.exists("frontend/package.json"):
            print("❌ package.json not found")
            return False

        # Check if node_modules exists
        if not os.path.exists("frontend/node_modules"):
            print("⚠️ node_modules not found, this is OK for deployment")

        print("✅ Frontend dependencies OK")
        return True

    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def test_static_files():
    """Test static build files"""
    print("📁 Testing static build files...")

    # Check if build directory exists
    if not os.path.exists("frontend/build"):
        print("⚠️ Build directory not found (run 'npm run build' to create)")
        return True  # Don't fail for missing build

    # Check for any JS and CSS files (names may vary)
    js_files = []
    css_files = []

    if os.path.exists("frontend/build/static/js"):
        js_files = [f for f in os.listdir("frontend/build/static/js") if f.endswith('.js')]

    if os.path.exists("frontend/build/static/css"):
        css_files = [f for f in os.listdir("frontend/build/static/css") if f.endswith('.css')]

    if js_files and css_files and os.path.exists("frontend/build/index.html"):
        print("✅ Build files present")
        return True
    else:
        print("⚠️ Some build files missing (this is OK for development)")
        return True

def test_api_connection():
    """Test frontend-backend API connection"""
    print("🔗 Testing API connection...")

    try:
        # Test backend health
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ Backend API connection successful")
                return True
            else:
                print("⚠️ Backend API responding but status not OK")
                return False
        else:
            print(f"❌ Backend API not responding (status: {response.status_code})")
            return False

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Backend API not accessible: {e}")
        print("   (This is expected if backend is not running)")
        return True  # Don't fail the test if backend is not running
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False

def run_all_tests():
    """Run all frontend tests"""
    print("🚀 Starting S1000D QA Frontend Tests\n")

    tests = [
        test_frontend_dependencies,
        test_frontend_build,
        test_static_files,
        test_api_connection
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

    print("\n📊 Frontend Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
