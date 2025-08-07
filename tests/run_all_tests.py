#!/usr/bin/env python3
"""
Master Test Suite for Todoist Integration

Runs all tests to check for bugs, loopholes, and performance issues.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test_script(script_name, description):
    """Run a test script and capture results"""
    print(f"\n🧪 Running {description}...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Completed in {duration:.1f} seconds")
        
        if result.returncode == 0:
            print("✅ PASSED")
            return True, result.stdout, result.stderr
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
            print("STDERR:", result.stderr[-500:] if result.stderr else "None")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Test took too long")
        return False, "", "Test timed out"
    except Exception as e:
        print(f"💥 ERROR - {e}")
        return False, "", str(e)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 CHECKING PREREQUISITES")
    print("=" * 50)
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        issues.append("Python 3.7+ required")
    else:
        print("✅ Python version OK")
    
    # Check required files exist
    required_files = [
        'todoist_integration.py',
        'notion_integration.py',
        'moodle_fetcher.py',
        '.env.example',
        'tests/test_todoist_sync.py',
        'tests/test_notion_sync.py',
        'tests/test_bug_detection.py',
        'tests/test_notion_bug_detection.py',
        'tests/test_logic_validation.py',
        'tests/test_notion_logic_validation.py',
        'tests/test_stress.py',
        'tests/test_notion_stress.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            issues.append(f"Missing file: {file}")
    
    # Check environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        todoist_token = os.getenv('TODOIST_TOKEN')
        if todoist_token:
            print("✅ TODOIST_TOKEN configured")
        else:
            issues.append("TODOIST_TOKEN not set in .env")
        
        notion_token = os.getenv('NOTION_TOKEN')
        if notion_token:
            print("✅ NOTION_TOKEN configured")
        else:
            print("⚠️ NOTION_TOKEN not set (optional)")
            
        notion_db_id = os.getenv('NOTION_DATABASE_ID')
        if notion_db_id:
            print("✅ NOTION_DATABASE_ID configured")
        else:
            print("⚠️ NOTION_DATABASE_ID not set (optional)")
            
    except ImportError:
        issues.append("python-dotenv not installed")
    
    # Check optional dependencies
    optional_deps = ['psutil', 'requests']
    for dep in optional_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            print(f"⚠️ {dep} not available (optional)")
    
    if issues:
        print(f"\n❌ {len(issues)} issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("\n✅ All prerequisites met!")
        return True

def generate_test_report(results):
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# Todoist Integration Test Report
Generated: {timestamp}

## Test Summary
"""
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result['passed'])
    
    report += f"- Total Test Suites: {total_tests}\n"
    report += f"- Passed: {passed_tests}\n"
    report += f"- Failed: {total_tests - passed_tests}\n"
    report += f"- Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n"
    
    report += "## Detailed Results\n\n"
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        report += f"### {result['name']}\n"
        report += f"Status: {status}\n"
        report += f"Duration: {result['duration']:.1f}s\n"
        
        if not result['passed']:
            report += f"Error: {result['error']}\n"
        
        report += "\n"
    
    report += "## Recommendations\n\n"
    
    if passed_tests == total_tests:
        report += "🎉 **All tests passed!** The system appears to be working correctly.\n\n"
        report += "### Next Steps:\n"
        report += "- Deploy to production\n"
        report += "- Set up monitoring\n"
        report += "- Schedule regular testing\n"
    else:
        report += "⚠️ **Some tests failed.** Please address the issues before production deployment.\n\n"
        report += "### Priority Actions:\n"
        report += "- Fix failing tests\n"
        report += "- Review error messages\n"
        report += "- Re-run tests after fixes\n"
    
    # Save report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return report

def run_master_test_suite():
    """Run the complete test suite"""
    print("🚀 MASTER TEST SUITE FOR TODOIST & NOTION INTEGRATION")
    print("=" * 70)
    print("This will run comprehensive tests to check for bugs, loopholes,")
    print("and performance issues in both Todoist and Notion integrations.")
    print("=" * 70)
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return False
    
    # Test suite configuration
    test_suites = [
        {
            'script': 'tests/test_todoist_sync.py',
            'name': 'Basic Todoist Integration Test',
            'description': 'Basic functionality and connection tests'
        },
        {
            'script': 'tests/test_notion_sync.py',
            'name': 'Basic Notion Integration Test',
            'description': 'Basic Notion functionality and connection tests'
        },
        {
            'script': 'tests/test_bug_detection.py',
            'name': 'Bug Detection Test',
            'description': 'Edge cases and potential bugs'
        },
        {
            'script': 'tests/test_notion_bug_detection.py',
            'name': 'Notion Bug Detection Test',
            'description': 'Notion edge cases and potential bugs'
        },
        {
            'script': 'tests/test_logic_validation.py',
            'name': 'Logic Validation Test',
            'description': 'Business logic and loopholes'
        },
        {
            'script': 'tests/test_notion_logic_validation.py',
            'name': 'Notion Logic Validation Test',
            'description': 'Notion business logic and loopholes'
        },
        {
            'script': 'tests/test_stress.py',
            'name': 'Stress Test',
            'description': 'Performance and load testing'
        },
        {
            'script': 'tests/test_notion_stress.py',
            'name': 'Notion Stress Test',
            'description': 'Notion performance and load testing'
        }
    ]
    
    results = []
    
    print(f"\n📋 Running {len(test_suites)} test suites...")
    
    # Run each test suite
    for i, suite in enumerate(test_suites, 1):
        print(f"\n{'='*70}")
        print(f"🧪 TEST SUITE {i}/{len(test_suites)}: {suite['name']}")
        print(f"{'='*70}")
        
        start_time = time.time()
        passed, stdout, stderr = run_test_script(suite['script'], suite['description'])
        end_time = time.time()
        
        result = {
            'name': suite['name'],
            'script': suite['script'],
            'passed': passed,
            'duration': end_time - start_time,
            'stdout': stdout,
            'stderr': stderr,
            'error': stderr if not passed else None
        }
        
        results.append(result)
        
        # Show brief result
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\n{suite['name']}: {status} ({result['duration']:.1f}s)")
    
    # Generate summary
    print(f"\n{'='*70}")
    print("📊 FINAL TEST RESULTS")
    print(f"{'='*70}")
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"{result['name']:<35} {status}")
    
    print(f"\n📈 Overall Success Rate: {passed_count}/{total_count} ({(passed_count/total_count)*100:.1f}%)")
    
    # Generate detailed report
    generate_test_report(results)
    
    # Final assessment
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is ready for production use")
        print("✅ No critical bugs detected")
        print("✅ Performance is acceptable")
        print("✅ Logic validation successful")
        
        print("\n🚀 Deployment Checklist:")
        print("[ ] Review test report")
        print("[ ] Set up production environment")
        print("[ ] Configure monitoring")
        print("[ ] Schedule regular runs")
        print("[ ] Set up error alerting")
        
    else:
        failed_count = total_count - passed_count
        print(f"\n⚠️ {failed_count} TEST SUITE(S) FAILED")
        print("❌ System has issues that need to be addressed")
        
        print("\n🔧 Required Actions:")
        print("1. Review failed test details in the report")
        print("2. Fix identified issues")
        print("3. Re-run the test suite")
        print("4. Only deploy after all tests pass")
        
        # Show which tests failed
        failed_tests = [r['name'] for r in results if not r['passed']]
        print(f"\n📋 Failed Tests:")
        for test in failed_tests:
            print(f"  • {test}")
    
    return passed_count == total_count

def quick_test():
    """Run a quick subset of tests"""
    print("⚡ QUICK TEST MODE")
    print("=" * 50)
    
    # Just run basic tests
    passed, stdout, stderr = run_test_script(
        'tests/test_todoist_sync.py', 
        'Quick Integration Test'
    )
    
    if passed:
        print("\n✅ Quick test passed! System appears to be working.")
        print("💡 Run full test suite with: python tests/run_all_tests.py")
    else:
        print("\n❌ Quick test failed! There are issues to fix.")
        print("🔧 Check your configuration and try again.")
    
    return passed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Todoist integration tests')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick test only')
    parser.add_argument('--prereq-only', action='store_true',
                       help='Check prerequisites only')
    
    args = parser.parse_args()
    
    if args.prereq_only:
        check_prerequisites()
    elif args.quick:
        quick_test()
    else:
        run_master_test_suite()
    
    print(f"\n{'='*70}")
    print("🏁 TESTING COMPLETE")
    print(f"{'='*70}")
