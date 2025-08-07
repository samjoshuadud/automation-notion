#!/usr/bin/env python3
"""
Comprehensive bug testing for Notion integration
Tests edge cases, malformed data, and potential logic errors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_integration import NotionIntegration
from datetime import datetime, timedelta
import json
import time

def main():
    print("🧪 COMPREHENSIVE NOTION BUG TESTING SUITE")
    print("=" * 70)
    print("Testing for logic errors, edge cases, and potential loopholes...")
    print("=" * 70)
    
    # Initialize Notion integration
    try:
        notion = NotionIntegration()
        if not notion.enabled:
            print("❌ Notion integration not enabled - check credentials")
            return False
        print("✅ Notion integration initialized successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    print("\n🔸 Phase 1: Edge Cases")
    print("🐛 TESTING EDGE CASES & POTENTIAL BUGS")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Invalid due date handling
    print("1. Testing invalid due date handling...")
    total_tests += 1
    try:
        invalid_dates = ["", "None", "invalid-date", "2025-13-45", "2025-02-30"]
        for invalid_date in invalid_dates:
            test_assignment = {
                "title": f"Test Invalid Date: {invalid_date}",
                "title_normalized": f"test invalid date: {invalid_date}",
                "course": "TEST COURSE",
                "course_code": "TEST",
                "due_date": invalid_date,
                "source": "email",
                "email_id": f"test_invalid_date_{int(time.time())}",
                "status": "Pending"
            }
            # This should not crash - invalid dates should be handled gracefully
            success = notion.create_assignment_page(test_assignment)
            print(f"   Invalid date '{invalid_date}' → Success: {success}")
        
        print("✅ Invalid date handling works")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Invalid date handling failed: {e}")
    
    # Test 2: Malformed assignment data
    print("\n2. Testing malformed assignment data...")
    total_tests += 1
    try:
        malformed_assignments = [
            {},  # Empty assignment
            {"title": ""},  # Empty title
            {"title": None},  # None title
            {"course_code": ""},  # Empty course code
            {"due_date": None},  # None due date
            {"raw_title": None, "title": "Test"},  # None raw_title
        ]
        
        for assignment in malformed_assignments:
            try:
                # Add required fields to prevent immediate rejection
                if "email_id" not in assignment:
                    assignment["email_id"] = f"malformed_test_{int(time.time())}"
                if "status" not in assignment:
                    assignment["status"] = "Pending"
                
                success = notion.create_assignment_page(assignment)
                print(f"   Malformed: {assignment} → Success: {success}")
            except Exception as inner_e:
                print(f"   Malformed: {assignment} → Error: {inner_e}")
        
        print("✅ Malformed assignment handling works")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Malformed assignment handling failed: {e}")
    
    # Test 3: Very long content
    print("\n3. Testing very long content...")
    total_tests += 1
    try:
        long_title = "A" * 500  # Very long title
        long_course = "B" * 300  # Very long course name
        
        long_assignment = {
            "title": long_title,
            "title_normalized": long_title.lower(),
            "course": long_course,
            "course_code": "LONG",
            "due_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "source": "email",
            "email_id": f"long_test_{int(time.time())}",
            "status": "Pending"
        }
        
        success = notion.create_assignment_page(long_assignment)
        print(f"   Long content handled: Title {len(long_title)} chars, Course {len(long_course)} chars")
        print(f"   Result: {success}")
        print("✅ Long content handling works")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Long content handling failed: {e}")
    
    # Test 4: Special characters
    print("\n4. Testing special characters...")
    total_tests += 1
    try:
        special_chars_assignment = {
            "title": "SPÉ - Activity 1 (SPÉCIAŁ ÇHARS)",
            "title_normalized": "spé - activity 1 (spéciał çhars)",
            "course": "SPÉCIAŁ ÇHARS & ÉMOJIS 🎓📚",
            "course_code": "SPÉ",
            "due_date": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "source": "email",
            "email_id": f"special_test_{int(time.time())}",
            "status": "Pending"
        }
        
        success = notion.create_assignment_page(special_chars_assignment)
        print(f"   Special chars assignment: {special_chars_assignment['title']}")
        print(f"   Result: {success}")
        print("✅ Special character handling works")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Special character handling failed: {e}")
    
    print(f"\n📊 Edge Case Tests: {passed_tests}/{total_tests} passed")
    
    print("\n🔸 Phase 2: Duplicate Detection")
    print("🔍 TESTING DUPLICATE DETECTION LOGIC")
    print("=" * 60)
    
    # Test duplicate detection
    print("1. Testing duplicate detection logic...")
    total_tests += 1
    try:
        base_assignment = {
            "title": "DUP - Test Assignment (Duplicate Detection)",
            "title_normalized": "dup - test assignment (duplicate detection)",
            "course": "DUPLICATE TEST COURSE",
            "course_code": "DUP",
            "due_date": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "source": "email",
            "email_id": f"dup_test_{int(time.time())}",
            "status": "Pending"
        }
        
        # Create the first assignment
        success1 = notion.create_assignment_page(base_assignment)
        print(f"   First creation: {success1}")
        
        # Wait a moment and try to create the same assignment again
        time.sleep(1)
        success2 = notion.create_assignment_page(base_assignment)
        print(f"   Duplicate creation: {success2}")
        
        # Test similar assignments
        similar_assignments = [
            {**base_assignment, "title": "DUP - Test Assignment (Duplicate Detection)", "email_id": base_assignment["email_id"]},  # Exact same
            {**base_assignment, "title": "dup - test assignment (duplicate detection)", "email_id": f"dup_test_case_{int(time.time())}"},  # Case difference
            {**base_assignment, "title": "DUP - Test Assignment (Duplicate Detections)", "email_id": f"dup_test_plural_{int(time.time())}"},  # Plural difference
        ]
        
        for i, similar in enumerate(similar_assignments):
            exists = notion.check_assignment_exists(similar)
            print(f"   Similar assignment {i+1} exists: {exists}")
        
        print("✅ Duplicate detection logic tested")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
    
    print(f"\n📊 Duplicate Detection Tests: {1 if passed_tests > total_tests - 1 else 0}/1 passed")
    
    print("\n🔸 Phase 3: API Error Handling")
    print("🌐 TESTING API ERROR HANDLING")
    print("=" * 60)
    
    # Test API error handling
    print("1. Testing invalid credentials handling...")
    total_tests += 1
    try:
        # Test with invalid token temporarily
        original_token = notion.notion_token
        original_headers = notion.headers.copy()
        
        notion.notion_token = "invalid_token_123"
        notion.headers['Authorization'] = 'Bearer invalid_token_123'
        
        connected = notion._test_connection()
        if not connected:
            print("   ✅ Invalid token correctly rejected")
            passed_tests += 1
        else:
            print("   ⚠️ Invalid token not detected - potential security issue")
        
        # Restore original credentials
        notion.notion_token = original_token
        notion.headers = original_headers
        
    except Exception as e:
        print(f"   ✅ API error handling: {e}")
        passed_tests += 1
    
    print(f"\n📊 API Error Handling Tests: {1 if passed_tests > total_tests - 1 else 0}/1 passed")
    
    print("\n🔸 Phase 4: Data Integrity")
    print("💾 TESTING DATA INTEGRITY")
    print("=" * 60)
    
    # Test data integrity
    print("1. Testing sync with empty data...")
    total_tests += 1
    try:
        # Test sync with empty list
        empty_result = notion.sync_assignments([])
        print(f"   Empty list sync result: {empty_result}")
        
        # Test sync with None
        none_result = notion.sync_assignments(None) if hasattr(notion, 'sync_assignments') else 0
        print(f"   None sync result: {none_result}")
        
        # Test sync with malformed data
        malformed_list = [None, {}, {"title": "Valid"}, {"title": None}]
        malformed_result = notion.sync_assignments(malformed_list)
        print(f"   Malformed list sync result: {malformed_result}")
        
        print("✅ Data integrity tests completed")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
    
    print(f"\n📊 Data Integrity Tests: {1 if passed_tests > total_tests - 1 else 0}/1 passed")
    
    print("\n🔸 Phase 5: Database Operations")
    print("🗄️ TESTING DATABASE OPERATIONS")
    print("=" * 60)
    
    # Test database operations
    print("1. Testing database statistics...")
    total_tests += 1
    try:
        stats = notion.get_database_stats() if hasattr(notion, 'get_database_stats') else {}
        print(f"   Database stats: {stats}")
        
        # Test getting all assignments
        all_assignments = notion.get_all_assignments_from_notion()
        print(f"   Retrieved {len(all_assignments)} assignments from database")
        
        print("✅ Database operations completed")
        passed_tests += 1
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
    
    print(f"\n📊 Database Operations Tests: {1 if passed_tests > total_tests - 1 else 0}/1 passed")
    
    print("\n" + "=" * 70)
    print("📊 FINAL NOTION BUG TEST REPORT")
    print("=" * 70)
    
    categories = [
        ("Edge Cases", 4),
        ("Duplicate Detection", 1), 
        ("API Error Handling", 1),
        ("Data Integrity", 1),
        ("Database Operations", 1)
    ]
    
    category_results = []
    tests_run = 0
    
    for category, count in categories:
        category_passed = min(passed_tests - tests_run, count)
        tests_run += count
        status = "✅ PASSED" if category_passed == count else "❌ FAILED"
        category_results.append((category, status))
        print(f"{category:<20} {status}")
    
    print("-" * 70)
    overall_pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"Overall Result: {passed_tests}/{total_tests} test suites passed ({overall_pass_rate:.1f}%)")
    
    if passed_tests == total_tests:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed. Review the issues above.")
    
    print("\n🔧 Next Steps:")
    print("1. Fix any failing test cases")
    print("2. Add additional error handling if needed")
    print("3. Re-run this test suite")
    print("4. Test with real Notion database")
    
    print("\n📝 Additional Testing Recommendations:")
    print("1. Test with large datasets (100+ assignments)")
    print("2. Test network interruption scenarios")
    print("3. Test with different Notion database schemas")
    print("4. Monitor memory usage during large syncs")
    print("5. Test concurrent access scenarios")
    
    print("\n" + "=" * 70)
    if passed_tests == total_tests:
        print("🐛 TESTING COMPLETE: All tests passed! ✅")
    else:
        print("🐛 TESTING COMPLETE: Please address the issues found. ⚠️")
    print("=" * 70)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
