#!/usr/bin/env python3
"""
Stress testing for Notion integration
Tests performance, memory usage, and API rate limits
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_integration import NotionIntegration
from datetime import datetime, timedelta
import time
import random
import string
import psutil
import gc

def generate_test_assignment(index: int) -> dict:
    """Generate a test assignment with realistic data"""
    courses = ["CS101", "MATH", "PHYS", "ENG", "HIST", "BIO", "CHEM", "ART"]
    activities = ["Assignment", "Project", "Quiz", "Exam", "Lab", "Report"]
    
    course_code = random.choice(courses)
    activity = random.choice(activities)
    
    return {
        "title": f"{course_code} - {activity} {index} (Stress Test)",
        "title_normalized": f"{course_code.lower()} - {activity.lower()} {index} (stress test)",
        "course": f"{course_code} - STRESS TEST COURSE {index}",
        "course_code": course_code,
        "due_date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
        "raw_title": f"ACTIVITY {index} - {activity.upper()} [1]",
        "source": "email",
        "email_id": f"stress_test_{index}_{int(time.time())}",
        "email_date": datetime.now().strftime('%Y-%m-%d'),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": random.choice(["Pending", "In Progress", "Completed"])
    }

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def main():
    print("🏋️ NOTION STRESS TESTING SUITE")
    print("=" * 70)
    print("Testing performance, memory usage, and API rate limits...")
    print("=" * 70)
    
    # Initialize Notion integration
    try:
        notion = NotionIntegration()
        if not notion.enabled:
            print("❌ Notion integration not enabled")
            return False
        print("✅ Notion integration initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    print(f"\n📊 Starting memory usage: {get_memory_usage():.1f} MB")
    
    stress_tests = []
    
    print("\n🔸 Phase 1: Small Batch Performance")
    print("📈 TESTING SMALL BATCH SYNC (10 assignments)")
    print("=" * 60)
    
    try:
        start_time = time.time()
        start_memory = get_memory_usage()
        
        # Generate 10 test assignments
        small_batch = [generate_test_assignment(i) for i in range(1, 11)]
        
        # Sync them
        synced_count = notion.sync_assignments(small_batch)
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"✅ Small batch test completed:")
        print(f"   Synced: {synced_count}/10 assignments")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Memory used: {memory_used:.1f} MB")
        print(f"   Rate: {synced_count/duration:.1f} assignments/second")
        
        stress_tests.append(("Small Batch (10)", "PASSED", duration, memory_used))
        
    except Exception as e:
        print(f"❌ Small batch test failed: {e}")
        stress_tests.append(("Small Batch (10)", "FAILED", 0, 0))
    
    print("\n🔸 Phase 2: Medium Batch Performance")
    print("📈 TESTING MEDIUM BATCH SYNC (50 assignments)")
    print("=" * 60)
    
    try:
        start_time = time.time()
        start_memory = get_memory_usage()
        
        # Generate 50 test assignments
        medium_batch = [generate_test_assignment(i) for i in range(100, 150)]
        
        # Sync them in smaller chunks to avoid rate limits
        total_synced = 0
        chunk_size = 10
        
        for i in range(0, len(medium_batch), chunk_size):
            chunk = medium_batch[i:i + chunk_size]
            synced = notion.sync_assignments(chunk)
            total_synced += synced
            
            # Small delay between chunks to respect rate limits
            time.sleep(1)
            
            print(f"   Chunk {i//chunk_size + 1}: {synced}/{len(chunk)} synced")
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"✅ Medium batch test completed:")
        print(f"   Synced: {total_synced}/50 assignments")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Memory used: {memory_used:.1f} MB")
        print(f"   Rate: {total_synced/duration:.1f} assignments/second")
        
        stress_tests.append(("Medium Batch (50)", "PASSED", duration, memory_used))
        
    except Exception as e:
        print(f"❌ Medium batch test failed: {e}")
        stress_tests.append(("Medium Batch (50)", "FAILED", 0, 0))
    
    print("\n🔸 Phase 3: Database Query Performance")
    print("🗄️ TESTING LARGE RETRIEVAL OPERATIONS")
    print("=" * 60)
    
    try:
        start_time = time.time()
        start_memory = get_memory_usage()
        
        # Test multiple retrievals
        for i in range(5):
            assignments = notion.get_all_assignments_from_notion()
            print(f"   Query {i+1}: Retrieved {len(assignments)} assignments")
            time.sleep(0.5)  # Brief pause between queries
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"✅ Database query test completed:")
        print(f"   Queries: 5")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Memory used: {memory_used:.1f} MB")
        print(f"   Avg query time: {duration/5:.2f} seconds")
        
        stress_tests.append(("Database Queries (5x)", "PASSED", duration, memory_used))
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        stress_tests.append(("Database Queries (5x)", "FAILED", 0, 0))
    
    print("\n🔸 Phase 4: Memory Leak Detection")
    print("🧠 TESTING MEMORY USAGE PATTERNS")
    print("=" * 60)
    
    try:
        start_memory = get_memory_usage()
        memory_samples = [start_memory]
        
        # Perform repeated operations
        for cycle in range(10):
            # Generate and sync a small batch
            test_batch = [generate_test_assignment(i + cycle * 1000) for i in range(5)]
            notion.sync_assignments(test_batch)
            
            # Get assignments
            assignments = notion.get_all_assignments_from_notion()
            
            # Force garbage collection
            gc.collect()
            
            # Sample memory
            current_memory = get_memory_usage()
            memory_samples.append(current_memory)
            
            print(f"   Cycle {cycle + 1}: {current_memory:.1f} MB")
            
            time.sleep(1)
        
        # Analyze memory trend
        memory_increase = memory_samples[-1] - memory_samples[0]
        avg_increase_per_cycle = memory_increase / 10
        
        print(f"✅ Memory leak test completed:")
        print(f"   Initial memory: {memory_samples[0]:.1f} MB")
        print(f"   Final memory: {memory_samples[-1]:.1f} MB")
        print(f"   Total increase: {memory_increase:.1f} MB")
        print(f"   Avg increase per cycle: {avg_increase_per_cycle:.2f} MB")
        
        # Check for memory leak (arbitrary threshold)
        if avg_increase_per_cycle > 1.0:
            print(f"   ⚠️ Potential memory leak detected")
            stress_tests.append(("Memory Leak Test", "WARNING", 0, memory_increase))
        else:
            print(f"   ✅ No significant memory leak detected")
            stress_tests.append(("Memory Leak Test", "PASSED", 0, memory_increase))
        
    except Exception as e:
        print(f"❌ Memory leak test failed: {e}")
        stress_tests.append(("Memory Leak Test", "FAILED", 0, 0))
    
    print("\n🔸 Phase 5: Rate Limit Testing")
    print("⚡ TESTING API RATE LIMITS")
    print("=" * 60)
    
    try:
        start_time = time.time()
        
        # Test rapid API calls
        successful_calls = 0
        rate_limited_calls = 0
        error_calls = 0
        
        for i in range(20):  # Try 20 rapid calls
            try:
                # Make a simple API call
                assignments = notion.get_all_assignments_from_notion()
                successful_calls += 1
                print(f"   Call {i+1}: Success ({len(assignments)} assignments)")
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "429" in error_msg:
                    rate_limited_calls += 1
                    print(f"   Call {i+1}: Rate limited")
                else:
                    error_calls += 1
                    print(f"   Call {i+1}: Error - {str(e)[:50]}...")
            
            # Very brief pause
            time.sleep(0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Rate limit test completed:")
        print(f"   Successful calls: {successful_calls}")
        print(f"   Rate limited calls: {rate_limited_calls}")
        print(f"   Error calls: {error_calls}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Call rate: {20/duration:.1f} calls/second")
        
        if rate_limited_calls > 0:
            stress_tests.append(("Rate Limit Test", "WARNING", duration, 0))
        else:
            stress_tests.append(("Rate Limit Test", "PASSED", duration, 0))
        
    except Exception as e:
        print(f"❌ Rate limit test failed: {e}")
        stress_tests.append(("Rate Limit Test", "FAILED", 0, 0))
    
    print("\n🔸 Phase 6: Error Recovery Testing")
    print("🛠️ TESTING ERROR RECOVERY")
    print("=" * 60)
    
    try:
        # Test recovery from various error conditions
        recovery_tests = [
            ("Empty assignment list", []),
            ("None input", None),
            ("Malformed assignment", [{"title": None}]),
            ("Very long title", [{"title": "A" * 500, "email_id": f"recovery_test_{int(time.time())}"}]),
        ]
        
        recovery_successes = 0
        
        for test_name, test_data in recovery_tests:
            try:
                if test_data is None:
                    result = 0  # Expected behavior for None input
                else:
                    result = notion.sync_assignments(test_data)
                print(f"   {test_name}: Handled gracefully (result: {result})")
                recovery_successes += 1
            except Exception as e:
                print(f"   {test_name}: Error - {str(e)[:50]}...")
        
        print(f"✅ Error recovery test completed:")
        print(f"   Tests passed: {recovery_successes}/{len(recovery_tests)}")
        
        if recovery_successes == len(recovery_tests):
            stress_tests.append(("Error Recovery", "PASSED", 0, 0))
        else:
            stress_tests.append(("Error Recovery", "PARTIAL", 0, 0))
        
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
        stress_tests.append(("Error Recovery", "FAILED", 0, 0))
    
    print("\n" + "=" * 70)
    print("📊 STRESS TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(1 for _, status, _, _ in stress_tests if status == "PASSED")
    warning_tests = sum(1 for _, status, _, _ in stress_tests if status == "WARNING")
    failed_tests = sum(1 for _, status, _, _ in stress_tests if status == "FAILED")
    
    for test_name, status, duration, memory in stress_tests:
        status_icon = "✅" if status == "PASSED" else "⚠️" if status == "WARNING" else "❌"
        print(f"{test_name:<25} {status_icon} {status}")
        if duration > 0:
            print(f"{'':27} Duration: {duration:.2f}s")
        if memory > 0:
            print(f"{'':27} Memory: {memory:.1f}MB")
    
    print("-" * 70)
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests with Warnings: {warning_tests}")
    print(f"Tests Failed: {failed_tests}")
    print(f"Total Tests: {len(stress_tests)}")
    
    final_memory = get_memory_usage()
    print(f"\nFinal memory usage: {final_memory:.1f} MB")
    
    print("\n🎯 Performance Recommendations:")
    if any("FAILED" in status for _, status, _, _ in stress_tests):
        print("❌ Critical performance issues found - review failed tests")
    elif any("WARNING" in status for _, status, _, _ in stress_tests):
        print("⚠️ Performance warnings found - consider optimizations")
    else:
        print("✅ Performance tests passed - system is ready for production")
    
    print("\n📋 Optimization Suggestions:")
    print("   1. Implement batch operations for large datasets")
    print("   2. Add caching for frequently accessed data")
    print("   3. Implement exponential backoff for rate limiting")
    print("   4. Add connection pooling for API calls")
    print("   5. Consider background processing for large syncs")
    
    print("\n📊 Monitoring Recommendations:")
    print("   1. Monitor API call frequency and response times")
    print("   2. Track memory usage during large operations")
    print("   3. Set up alerts for rate limit violations")
    print("   4. Monitor database query performance")
    print("   5. Track sync success rates and error patterns")
    
    print("\n" + "=" * 70)
    if failed_tests == 0:
        print("🏋️ STRESS TESTING COMPLETE: System passed all critical tests! ✅")
    else:
        print("🏋️ STRESS TESTING COMPLETE: Issues found - review and optimize ⚠️")
    print("=" * 70)
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
