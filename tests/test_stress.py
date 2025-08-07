#!/usr/bin/env python3
"""
Stress Testing for Todoist Integration

Tests the system under various load conditions to find performance issues and bugs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todoist_integration import TodoistIntegration
from moodle_fetcher import MoodleEmailFetcher
import json
import time
from datetime import datetime, timedelta
import random
import string

def generate_test_assignments(count: int) -> list:
    """Generate a large number of test assignments"""
    assignments = []
    
    courses = ["HCI", "MATH", "CS", "PHYS", "CHEM", "BIO", "ENG", "HIST"]
    activities = ["Assignment", "Project", "Homework", "Lab", "Quiz", "Exam"]
    
    for i in range(count):
        course = random.choice(courses)
        activity = random.choice(activities)
        
        # Generate due date between now and 60 days from now
        days_ahead = random.randint(1, 60)
        due_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        assignment = {
            "title": f"{course} - {activity} {i+1} (Test Item)",
            "title_normalized": f"{course.lower()} - {activity.lower()} {i+1} (test item)",
            "due_date": due_date,
            "course": f"{course} - Test Course {i+1}",
            "course_code": course,
            "status": random.choice(["Pending", "In Progress", "Completed"]),
            "source": "stress_test",
            "raw_title": f"{activity.upper()} {i+1} - TEST ITEM",
            "email_id": f"stress_test_{i+1:04d}",
            "email_subject": f"{course} - Test Subject {i+1}",
            "email_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        assignments.append(assignment)
    
    return assignments

def stress_test_reminder_calculation():
    """Test reminder calculation with many dates"""
    print("⏰ STRESS TESTING REMINDER CALCULATION")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    if not todoist.enabled:
        print("❌ Todoist not enabled")
        return False
    
    # Test with 1000 different dates
    test_count = 1000
    start_time = time.time()
    
    print(f"Testing {test_count} reminder calculations...")
    
    successful = 0
    failed = 0
    
    for i in range(test_count):
        # Generate random due date
        days_ahead = random.randint(-30, 365)  # Include past dates
        due_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        try:
            reminder = todoist.calculate_reminder_date(due_date)
            if reminder:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if failed <= 5:  # Only show first 5 errors
                print(f"   Error on date {due_date}: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Results: {successful} successful, {failed} failed")
    print(f"Time: {duration:.2f} seconds ({test_count/duration:.0f} calculations/sec)")
    
    if failed == 0:
        print("✅ All reminder calculations successful")
        return True
    elif failed < test_count * 0.05:  # Less than 5% failure rate
        print("⚠️ Some failures but mostly working")
        return True
    else:
        print("❌ High failure rate in reminder calculations")
        return False

def stress_test_task_formatting():
    """Test task formatting with various content sizes"""
    print("\n🎨 STRESS TESTING TASK FORMATTING")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    if not todoist.enabled:
        print("❌ Todoist not enabled")
        return False
    
    # Generate assignments with varying content sizes
    test_assignments = []
    
    # Small content
    for i in range(100):
        test_assignments.append({
            "title": f"Test {i}",
            "course_code": "T",
            "raw_title": f"TEST {i}",
            "course": f"Test Course {i}",
            "due_date": "2025-12-31"
        })
    
    # Medium content
    for i in range(50):
        test_assignments.append({
            "title": f"Medium Test Assignment {i} " + "A" * 100,
            "course_code": "MED",
            "raw_title": f"MEDIUM TEST ASSIGNMENT {i} " + "B" * 50,
            "course": f"Medium Test Course {i} " + "C" * 200,
            "due_date": "2025-12-31"
        })
    
    # Large content
    for i in range(10):
        test_assignments.append({
            "title": f"Large Test Assignment {i} " + "X" * 500,
            "course_code": "LARGE",
            "raw_title": f"LARGE TEST ASSIGNMENT {i} " + "Y" * 300,
            "course": f"Large Test Course {i} " + "Z" * 1000,
            "due_date": "2025-12-31"
        })
    
    start_time = time.time()
    successful = 0
    failed = 0
    
    print(f"Testing formatting for {len(test_assignments)} assignments...")
    
    for assignment in test_assignments:
        try:
            content = todoist.format_task_content(assignment)
            description = todoist.format_task_description(assignment)
            
            # Basic validation
            if content and isinstance(content, str) and len(content) > 0:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"   Formatting error: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Results: {successful} successful, {failed} failed")
    print(f"Time: {duration:.2f} seconds ({len(test_assignments)/duration:.0f} formats/sec)")
    
    return failed == 0

def stress_test_duplicate_detection():
    """Test duplicate detection with large datasets"""
    print("\n🔍 STRESS TESTING DUPLICATE DETECTION")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    if not todoist.enabled:
        print("❌ Todoist not enabled")
        return False
    
    # Generate a mix of duplicate and unique assignments
    base_assignments = generate_test_assignments(100)
    
    # Add some duplicates (same email_id)
    duplicate_assignments = []
    for i in range(20):
        original = random.choice(base_assignments)
        duplicate = original.copy()
        duplicate["title"] = duplicate["title"] + " (Duplicate)"
        duplicate_assignments.append(duplicate)
    
    all_assignments = base_assignments + duplicate_assignments
    
    print(f"Testing duplicate detection on {len(all_assignments)} assignments...")
    start_time = time.time()
    
    try:
        # Test the prevent_duplicate_sync method
        filtered = todoist.prevent_duplicate_sync(all_assignments)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Original: {len(all_assignments)} assignments")
        print(f"Filtered: {len(filtered)} assignments")
        print(f"Detected duplicates: {len(all_assignments) - len(filtered)}")
        print(f"Time: {duration:.2f} seconds")
        
        if duration > 10:  # More than 10 seconds is too slow
            print("⚠️ Duplicate detection is slow")
            return False
        else:
            print("✅ Duplicate detection performance acceptable")
            return True
            
    except Exception as e:
        print(f"❌ Duplicate detection failed: {e}")
        return False

def stress_test_memory_usage():
    """Test memory usage with large datasets"""
    print("\n💾 STRESS TESTING MEMORY USAGE")
    print("=" * 50)
    
    import psutil
    import gc
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Initial memory usage: {initial_memory:.1f} MB")
    
    # Generate large dataset
    print("Generating large dataset...")
    large_dataset = generate_test_assignments(5000)
    
    after_generation = process.memory_info().rss / 1024 / 1024
    print(f"After generating 5000 assignments: {after_generation:.1f} MB")
    
    # Test JSON operations
    print("Testing JSON serialization...")
    json_data = json.dumps(large_dataset)
    
    after_json = process.memory_info().rss / 1024 / 1024
    print(f"After JSON serialization: {after_json:.1f} MB")
    
    # Test loading back
    print("Testing JSON deserialization...")
    loaded_data = json.loads(json_data)
    
    after_load = process.memory_info().rss / 1024 / 1024
    print(f"After JSON deserialization: {after_load:.1f} MB")
    
    # Cleanup
    del large_dataset
    del json_data
    del loaded_data
    gc.collect()
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"After cleanup: {final_memory:.1f} MB")
    
    memory_increase = final_memory - initial_memory
    
    if memory_increase > 100:  # More than 100MB increase
        print(f"⚠️ High memory usage increase: {memory_increase:.1f} MB")
        return False
    else:
        print(f"✅ Acceptable memory usage increase: {memory_increase:.1f} MB")
        return True

def stress_test_api_rate_limits():
    """Test API rate limiting and error handling"""
    print("\n🌐 STRESS TESTING API INTERACTIONS")
    print("=" * 50)
    
    todoist = TodoistIntegration()
    if not todoist.enabled:
        print("❌ Todoist not enabled")
        return False
    
    print("Testing multiple API calls in sequence...")
    
    start_time = time.time()
    successful_calls = 0
    failed_calls = 0
    
    # Make multiple API calls
    for i in range(10):
        try:
            # Test connection
            if todoist._test_connection():
                successful_calls += 1
            else:
                failed_calls += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            failed_calls += 1
            print(f"   API call {i+1} failed: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"API calls: {successful_calls} successful, {failed_calls} failed")
    print(f"Total time: {duration:.2f} seconds")
    
    if failed_calls == 0:
        print("✅ All API calls successful")
        return True
    elif failed_calls < 3:
        print("⚠️ Some API failures, might be rate limiting")
        return True
    else:
        print("❌ Many API failures")
        return False

def run_stress_tests():
    """Run comprehensive stress tests"""
    print("💪 COMPREHENSIVE STRESS TESTING SUITE")
    print("=" * 70)
    print("Testing system performance and stability under load...")
    print("=" * 70)
    
    test_results = []
    
    # Run stress tests
    print("\n🔸 Test 1: Reminder Calculation Stress Test")
    test_results.append(("Reminder Calculation", stress_test_reminder_calculation()))
    
    print("\n🔸 Test 2: Task Formatting Stress Test")
    test_results.append(("Task Formatting", stress_test_task_formatting()))
    
    print("\n🔸 Test 3: Duplicate Detection Stress Test")
    test_results.append(("Duplicate Detection", stress_test_duplicate_detection()))
    
    print("\n🔸 Test 4: Memory Usage Test")
    test_results.append(("Memory Usage", stress_test_memory_usage()))
    
    print("\n🔸 Test 5: API Rate Limiting Test")
    test_results.append(("API Rate Limits", stress_test_api_rate_limits()))
    
    # Generate report
    print("\n" + "=" * 70)
    print("📊 STRESS TEST REPORT")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Overall Result: {passed_tests}/{total_tests} stress tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL STRESS TESTS PASSED!")
        print("\n✅ System Performance Assessment:")
        print("• Can handle large datasets efficiently")
        print("• Memory usage is reasonable")
        print("• API interactions are stable")
        print("• No performance bottlenecks detected")
    else:
        print("⚠️ Some stress tests failed.")
        print("\n🔧 Performance Recommendations:")
        print("• Optimize slow operations")
        print("• Add caching for repeated operations")
        print("• Implement batch processing")
        print("• Add rate limiting protection")
        print("• Monitor memory usage in production")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    print("💪 STARTING STRESS TESTING...")
    
    # Check if required modules are available
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil not installed - memory tests will be limited")
        print("Install with: pip install psutil")
    
    success = run_stress_tests()
    
    print(f"\n{'='*70}")
    if success:
        print("🎯 STRESS TESTING COMPLETE: System performs well under load!")
    else:
        print("⚠️ STRESS TESTING COMPLETE: Performance issues detected.")
    print(f"{'='*70}")
    
    print("\n📈 Production Recommendations:")
    print("1. Monitor system performance regularly")
    print("2. Set up alerts for high memory usage")
    print("3. Implement logging for slow operations")
    print("4. Consider implementing caching")
    print("5. Test with real production data sizes")
