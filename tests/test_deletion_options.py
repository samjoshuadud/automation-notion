#!/usr/bin/env python3
"""
Test script to demonstrate the new selective deletion options
This script simulates the argument parsing without actually running deletion
"""

import argparse

def main():
    parser = argparse.ArgumentParser(description='Test Selective Deletion Options')
    parser.add_argument('--delete-all-assignments', action='store_true',
                       help='DELETE ALL assignments from database, Todoist, and Notion (DEBUG ONLY - emails are NOT touched)')
    parser.add_argument('--delete-from', type=str, choices=['notion', 'todoist', 'both'], default='both',
                       help='Choose where to delete assignments from: notion, todoist, or both (default: both)')
    
    # Test different scenarios
    test_scenarios = [
        ['--delete-all-assignments'],  # Default: both
        ['--delete-all-assignments', '--delete-from', 'notion'],  # Notion only
        ['--delete-all-assignments', '--delete-from', 'todoist'],  # Todoist only
        ['--delete-all-assignments', '--delete-from', 'both'],  # Explicit both
    ]
    
    print("🧪 Testing Selective Deletion Options")
    print("=" * 50)
    
    for i, scenario in enumerate(test_scenarios, 1):
        args = parser.parse_args(scenario)
        delete_from = args.delete_from
        
        print(f"\n#{i} Command: python run_fetcher.py {' '.join(scenario)}")
        print(f"   Result: Will delete from {delete_from.upper()}")
        
        # Show what would be deleted
        targets = []
        if delete_from in ['todoist', 'both']:
            targets.append("✅ Todoist")
        if delete_from in ['notion', 'both']:
            targets.append("📝 Notion")
        targets.append("📄 Local Database")
        
        print(f"   Targets: {', '.join(targets)}")
    
    print("\n🚀 Shell Script Usage Examples:")
    print("  ./run.sh delete-all           # Deletes from both Notion and Todoist")
    print("  ./run.sh delete-all notion    # Deletes only from Notion")
    print("  ./run.sh delete-all todoist   # Deletes only from Todoist")
    print("  ./run.sh delete-all both      # Explicitly deletes from both")

if __name__ == "__main__":
    main()
