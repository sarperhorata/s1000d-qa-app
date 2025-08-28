#!/usr/bin/env python3
"""
Complete Test Suite for S1000D QA Application
Runs all backend and frontend tests
"""

import sys
import subprocess
import os

def run_backend_tests():
    """Run backend tests"""
    print("🔧 Running Backend Tests...")
    print("=" * 50)

    try:
        # Change to backend directory
        os.chdir("backend")

        # Run backend tests
        result = subprocess.run([sys.executable, "test_app.py"],
                              capture_output=True, text=True, timeout=300)

        print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        # Go back to project root
        os.chdir("..")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Backend tests timed out")
        os.chdir("..")
        return False
    except Exception as e:
        print(f"❌ Error running backend tests: {e}")
        os.chdir("..")
        return False

def run_frontend_tests():
    """Run frontend tests"""
    print("\n🎨 Running Frontend Tests...")
    print("=" * 50)

    try:
        # Change to frontend directory
        os.chdir("frontend")

        # Run frontend tests
        result = subprocess.run([sys.executable, "test_frontend.py"],
                              capture_output=True, text=True, timeout=300)

        print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        # Go back to project root
        os.chdir("..")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Frontend tests timed out")
        os.chdir("..")
        return False
    except Exception as e:
        print(f"❌ Error running frontend tests: {e}")
        os.chdir("..")
        return False

def check_project_structure():
    """Check project structure"""
    print("📁 Checking Project Structure...")
    print("=" * 50)

    required_files = [
        "README.md",
        "backend/app.py",
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/src/App.tsx",
        "Dockerfile",
        "render.yaml"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_git_status():
    """Check git status"""
    print("📋 Checking Git Status...")
    print("=" * 50)

    try:
        # Check if we're in a git repository
        result = subprocess.run(["git", "status"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Git repository found")
            print("Current status:")
            print(result.stdout)
            return True
        else:
            print("❌ Not a git repository")
            return False

    except FileNotFoundError:
        print("⚠️ Git not found (this is OK for deployment)")
        return True
    except Exception as e:
        print(f"❌ Error checking git status: {e}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("🚀 S1000D QA Application - Complete Test Suite")
    print("=" * 60)

    tests = [
        ("Project Structure", check_project_structure),
        ("Git Status", check_git_status),
        ("Backend Tests", run_backend_tests),
        ("Frontend Tests", run_frontend_tests)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")

    if failed == 0:
        print("\n🎉 All tests passed! Ready for deployment.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix before deployment.")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("⚡ Running quick tests (structure only)...")
        tests_passed = check_project_structure() and check_git_status()
    else:
        tests_passed = run_all_tests()

    print("\n" + "=" * 60)
    if tests_passed:
        print("🎯 DEPLOYMENT STATUS: ✅ READY")
        print("\nNext steps:")
        print("1. Commit changes: git add . && git commit -m 'Ready for deployment'")
        print("2. Push to GitHub: git push origin main")
        print("3. Deploy to Render using render.yaml")
    else:
        print("🎯 DEPLOYMENT STATUS: ❌ NOT READY")
        print("\nPlease fix the failed tests before deployment.")

    sys.exit(0 if tests_passed else 1)

if __name__ == "__main__":
    main()
