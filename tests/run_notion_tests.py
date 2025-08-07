#!/usr/bin/env python3
"""
Master test suite for Notion integration
Runs all Notion-related tests and provides comprehensive reporting
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test(test_name: str, test_file: str) -> tuple:
    """Run a test and return (success, duration, output)"""
    print(f"\n🧪 Running {test_name}...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Set environment for the test
        env = os.environ.copy()
        env['PYTHONPATH'] = '/home/punisher/Documents/automate'
        
        # Run the test
        result = subprocess.run(
            ['/home/punisher/Documents/automate/venv/bin/python', test_file],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env,
            cwd='/home/punisher/Documents/automate'
        )
        
        duration = time.time() - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        return success, duration, result.stdout
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"❌ Test timed out after {duration:.1f} seconds")
        return False, duration, "Test timed out"
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Test failed to run: {e}")
        return False, duration, str(e)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 CHECKING PREREQUISITES")
    print("=" * 50)
    
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 7):
        print("✅ Python version OK")
    else:
        issues.append("Python 3.7+ required")
        print("❌ Python version too old")
    
    # Check if files exist
    required_files = [
        'notion_integration.py',
        'moodle_fetcher.py',
        '.env.example',
        'tests/test_notion_bug_detection.py',
        'tests/test_notion_logic_validation.py',
        'tests/test_notion_stress.py',
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            issues.append(f"{file} not found")
            print(f"❌ {file} not found")
    
    # Check environment variables
    if os.getenv('NOTION_TOKEN'):
        print("✅ NOTION_TOKEN configured")
    else:
        issues.append("NOTION_TOKEN not configured")
        print("❌ NOTION_TOKEN not found in environment")
    
    if os.getenv('NOTION_DATABASE_ID'):
        print("✅ NOTION_DATABASE_ID configured")
    else:
        issues.append("NOTION_DATABASE_ID not configured")
        print("❌ NOTION_DATABASE_ID not found in environment")
    
    # Check optional dependencies
    try:
        import requests
        print("✅ requests available")
    except ImportError:
        issues.append("requests not installed")
        print("❌ requests not available")
    
    try:
        import psutil
        print("✅ psutil available")
    except ImportError:
        print("⚠️ psutil not available (optional)")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv available")
    except ImportError:
        issues.append("python-dotenv not installed")
        print("❌ python-dotenv not available")
    
    if issues:
        print(f"\n❌ {len(issues)} issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("\n✅ All prerequisites met!")
        return True

def main():
    print("🚀 MASTER TEST SUITE FOR NOTION INTEGRATION")
    print("=" * 70)
    print("This will run comprehensive tests to check for bugs, loopholes,")
    print("and performance issues in the Notion integration system.")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        print("\n" + "=" * 70)
        print("🏁 TESTING COMPLETE")
        print("=" * 70)
        return False
    
    print("\n📋 Running 4 test suites...")
    
    # Define test suites
    test_suites = [
        ("Basic Notion Integration Test", "tests/test_notion_sync.py"),
        ("Bug Detection Test", "tests/test_notion_bug_detection.py"),
        ("Logic Validation Test", "tests/test_notion_logic_validation.py"),
        ("Stress Test", "tests/test_notion_stress.py"),
    ]
    
    results = []
    total_duration = 0
    
    # Run each test suite
    for i, (test_name, test_file) in enumerate(test_suites, 1):
        print(f"\n" + "=" * 70)
        print(f"🧪 TEST SUITE {i}/{len(test_suites)}: {test_name}")
        print("=" * 70)
        
        success, duration, output = run_test(test_name, test_file)
        total_duration += duration
        
        status = "✅ PASSED" if success else "❌ FAILED"
        results.append((test_name, status, duration))
        
        print(f"\n⏱️ Completed in {duration:.1f} seconds")
        print(f"{test_name}: {status} ({duration:.1f}s)")
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("=" * 70)
    
    passed_count = sum(1 for _, status, _ in results if "PASSED" in status)
    
    for test_name, status, duration in results:
        print(f"{test_name:<35} {status}")
    
    print(f"\n📈 Overall Success Rate: {passed_count}/{len(test_suites)} ({100*passed_count/len(test_suites):.1f}%)")
    print(f"⏱️ Total Duration: {total_duration:.1f} seconds")
    
    # Generate detailed report file
    report_filename = f"notion_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_filename, 'w') as f:
        f.write("# Notion Integration Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Duration:** {total_duration:.1f} seconds\n\n")
        f.write(f"**Success Rate:** {passed_count}/{len(test_suites)} ({100*passed_count/len(test_suites):.1f}%)\n\n")
        
        f.write("## Test Results\n\n")
        f.write("| Test Suite | Status | Duration |\n")
        f.write("|------------|--------|----------|\n")
        for test_name, status, duration in results:
            f.write(f"| {test_name} | {status} | {duration:.1f}s |\n")
        
        f.write("\n## Test Descriptions\n\n")
        f.write("1. **Basic Notion Integration Test**: Tests connection, database access, and basic sync functionality\n")
        f.write("2. **Bug Detection Test**: Tests edge cases, malformed data, and error handling\n")
        f.write("3. **Logic Validation Test**: Tests business logic, duplicate detection, and data consistency\n")
        f.write("4. **Stress Test**: Tests performance, memory usage, and API rate limits\n")
        
        if passed_count < len(test_suites):
            f.write("\n## Issues Found\n\n")
            f.write("Some tests failed. Please review the detailed output above and:\n\n")
            f.write("1. Fix any failing test cases\n")
            f.write("2. Address performance or logic issues\n")
            f.write("3. Re-run the test suite\n")
            f.write("4. Only deploy after all tests pass\n")
        else:
            f.write("\n## Recommendations\n\n")
            f.write("All tests passed! The Notion integration is ready for production use.\n\n")
            f.write("### Next Steps:\n")
            f.write("1. Deploy to production environment\n")
            f.write("2. Monitor performance and error rates\n")
            f.write("3. Set up regular testing schedule\n")
            f.write("4. Review and update tests as needed\n")
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    
    # Final recommendations
    if passed_count == len(test_suites):
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Notion integration is ready for production use")
    else:
        failed_count = len(test_suites) - passed_count
        print(f"\n⚠️ {failed_count} TEST SUITE(S) FAILED")
        print("❌ System has issues that need to be addressed")
        
        print(f"\n🔧 Required Actions:")
        print(f"1. Review failed test details in the report")
        print(f"2. Fix identified issues")
        print(f"3. Re-run the test suite")
        print(f"4. Only deploy after all tests pass")
        
        failed_tests = [name for name, status, _ in results if "FAILED" in status]
        if failed_tests:
            print(f"\n📋 Failed Tests:")
            for test in failed_tests:
                print(f"  • {test}")
    
    print("\n" + "=" * 70)
    print("🏁 TESTING COMPLETE")
    print("=" * 70)
    
    return passed_count == len(test_suites)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
