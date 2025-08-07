#!/usr/bin/env python3
"""
Enhanced Moodle Assignment Fetcher with Notion Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moodle_fetcher import MoodleEmailFetcher
from notion_integration import NotionIntegration
from todoist_integration import TodoistIntegration
from assignment_archive import AssignmentArchiveManager
import argparse
import logging
import time

def setup_logging(verbose: bool = False, debug: bool = False):
    """Set up enhanced logging configuration"""
    if debug:
        level = logging.DEBUG
        log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    elif verbose:
        level = logging.INFO
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
    else:
        level = logging.WARNING
        log_format = '%(levelname)s - %(message)s'
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # File handler (always debug level for logs)
    file_handler = logging.FileHandler('logs/moodle_fetcher.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console handler (respects verbose/debug settings)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Add colors for better readability in verbose/debug mode
    if verbose or debug:
        try:
            import colorama
            from colorama import Fore, Style
            colorama.init()
            
            class ColoredFormatter(logging.Formatter):
                COLORS = {
                    'DEBUG': Fore.CYAN,
                    'INFO': Fore.GREEN,
                    'WARNING': Fore.YELLOW,
                    'ERROR': Fore.RED,
                    'CRITICAL': Fore.MAGENTA + Style.BRIGHT
                }
                
                def format(self, record):
                    color = self.COLORS.get(record.levelname, '')
                    record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
                    return super().format(record)
            
            console_handler.setFormatter(ColoredFormatter(log_format))
        except ImportError:
            # Fallback to regular formatting if colorama not available
            console_handler.setFormatter(logging.Formatter(log_format))
    else:
        console_handler.setFormatter(logging.Formatter(log_format))
    
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )

def check_remaining_assignments_after_deletion(delete_from, include_local, args):
    """Check for remaining assignments after deletion and return them"""
    remaining = {"todoist": [], "notion": [], "local": []}
    
    try:
        # Check local database (if it wasn't deleted)
        if not include_local and delete_from != 'both':
            fetcher = MoodleEmailFetcher()
            local_assignments = fetcher.load_existing_assignments()
            if local_assignments:
                remaining["local"] = local_assignments
        
        # Check Todoist (if it wasn't cleared or was only partially cleared)
        if not args.skip_todoist:
            try:
                todoist = TodoistIntegration()
                if todoist.enabled:
                    todoist_tasks = todoist.get_school_assignments()
                    if todoist_tasks:
                        remaining["todoist"] = todoist_tasks
            except Exception as e:
                if args.verbose:
                    print(f"⚠️ Could not check remaining Todoist tasks: {e}")
        
        # Check Notion (if it wasn't cleared or was only partially cleared)
        if not args.skip_notion:
            try:
                notion = NotionIntegration()
                if notion.enabled:
                    notion_assignments = notion.get_all_assignments_from_notion()
                    if notion_assignments:
                        remaining["notion"] = notion_assignments
            except Exception as e:
                if args.verbose:
                    print(f"⚠️ Could not check remaining Notion assignments: {e}")
        
        # Return all remaining assignments combined
        all_remaining = []
        for platform, assignments in remaining.items():
            for assignment in assignments:
                assignment['_platform'] = platform  # Tag with platform info
                all_remaining.append(assignment)
        
        return all_remaining
        
    except Exception as e:
        if args.verbose:
            print(f"⚠️ Error checking remaining assignments: {e}")
        return []

def interactive_deletion_menu(remaining_assignments, args):
    """Interactive menu for deleting remaining assignments"""
    if not remaining_assignments:
        return
    
    print(f"\n🔍 FOUND {len(remaining_assignments)} REMAINING ASSIGNMENTS")
    print("=" * 50)
    print("Some assignments may still exist on the platforms.")
    print("This could happen if:")
    print("  • Assignment titles don't match exactly")
    print("  • Network issues during deletion")
    print("  • Different formatting between platforms")
    print()
    
    while True:
        print("📋 REMAINING ASSIGNMENTS:")
        print("-" * 30)
        
        for i, assignment in enumerate(remaining_assignments, 1):
            platform = assignment.get('_platform', 'unknown')
            title = assignment.get('title', 'Unknown Assignment')
            course = assignment.get('course_code', assignment.get('course', 'Unknown'))
            due_date = assignment.get('due_date', 'No due date')
            
            # Format title for display (truncate if too long)
            display_title = title[:60] + "..." if len(title) > 60 else title
            
            platform_icon = {"notion": "📝", "todoist": "✅", "local": "📄"}.get(platform, "❓")
            print(f"  {i:2d}. [{platform_icon} {platform.upper()}] {display_title}")
            print(f"      Course: {course} | Due: {due_date}")
        
        print()
        print("🎯 OPTIONS:")
        print("  [1-N]     Delete specific assignment by number")
        print("  all       Delete ALL remaining assignments")
        print("  notion    Delete all from Notion only")
        print("  todoist   Delete all from Todoist only")
        print("  local     Delete all from local database only")
        print("  show      Show full details of all assignments")
        print("  quit      Exit interactive mode")
        print()
        
        try:
            choice = input("👉 Choose action: ").strip().lower()
            
            if choice == 'quit' or choice == 'q':
                print("👋 Exiting interactive deletion mode")
                break
            
            elif choice == 'show':
                show_detailed_assignments(remaining_assignments)
                continue
            
            elif choice == 'all':
                if confirm_deletion("ALL remaining assignments"):
                    deleted_count = delete_assignments_interactive(remaining_assignments, 'all', args)
                    remaining_assignments = [a for a in remaining_assignments if not a.get('_deleted')]
                    print(f"✅ Deleted {deleted_count} assignments")
                    if not remaining_assignments:
                        print("🎉 No more assignments remaining!")
                        break
            
            elif choice in ['notion', 'todoist', 'local']:
                platform_assignments = [a for a in remaining_assignments if a.get('_platform') == choice]
                if platform_assignments:
                    if confirm_deletion(f"all assignments from {choice.upper()}"):
                        deleted_count = delete_assignments_interactive(platform_assignments, choice, args)
                        # Remove deleted assignments from the list
                        remaining_assignments = [a for a in remaining_assignments if not a.get('_deleted')]
                        print(f"✅ Deleted {deleted_count} assignments from {choice.upper()}")
                        if not remaining_assignments:
                            print("🎉 No more assignments remaining!")
                            break
                else:
                    print(f"❌ No assignments found on {choice.upper()}")
            
            elif choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(remaining_assignments):
                    assignment = remaining_assignments[index]
                    platform = assignment.get('_platform', 'unknown')
                    title = assignment.get('title', 'Unknown')
                    
                    if confirm_deletion(f"'{title[:40]}...' from {platform.upper()}"):
                        deleted_count = delete_assignments_interactive([assignment], platform, args)
                        if deleted_count > 0:
                            assignment['_deleted'] = True
                            remaining_assignments = [a for a in remaining_assignments if not a.get('_deleted')]
                            print(f"✅ Deleted assignment from {platform.upper()}")
                            if not remaining_assignments:
                                print("🎉 No more assignments remaining!")
                                break
                        else:
                            print(f"❌ Failed to delete assignment from {platform.upper()}")
                else:
                    print(f"❌ Invalid number. Please choose 1-{len(remaining_assignments)}")
            
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Exiting interactive deletion mode")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

def show_detailed_assignments(assignments):
    """Show detailed view of assignments"""
    print("\n📋 DETAILED ASSIGNMENT VIEW")
    print("=" * 60)
    
    for i, assignment in enumerate(assignments, 1):
        platform = assignment.get('_platform', 'unknown')
        platform_icon = {"notion": "📝", "todoist": "✅", "local": "📄"}.get(platform, "❓")
        
        print(f"\n{i}. [{platform_icon} {platform.upper()}]")
        print(f"   Title: {assignment.get('title', 'Unknown Assignment')}")
        print(f"   Course: {assignment.get('course_code', assignment.get('course', 'Unknown'))}")
        print(f"   Due Date: {assignment.get('due_date', 'No due date')}")
        print(f"   Status: {assignment.get('status', 'Unknown')}")
        if assignment.get('source'):
            print(f"   Source: {assignment.get('source')}")
        if assignment.get('email_id'):
            print(f"   Email ID: {assignment.get('email_id')}")

def confirm_deletion(target):
    """Get user confirmation for deletion"""
    try:
        response = input(f"❓ Delete {target}? (y/N): ").strip().lower()
        return response in ['y', 'yes']
    except KeyboardInterrupt:
        return False

def delete_assignments_interactive(assignments, target_platform, args):
    """Delete assignments interactively"""
    deleted_count = 0
    
    for assignment in assignments:
        platform = assignment.get('_platform', target_platform)
        
        try:
            if platform == 'todoist' or target_platform == 'all':
                if not args.skip_todoist and (platform == 'todoist' or target_platform in ['all', 'todoist']):
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        if todoist.delete_assignment_task(assignment):
                            deleted_count += 1
                            assignment['_deleted'] = True
                            if args.verbose:
                                print(f"   ✅ Deleted from Todoist: {assignment.get('title', 'Unknown')[:50]}")
            
            if platform == 'notion' or target_platform == 'all':
                if not args.skip_notion and (platform == 'notion' or target_platform in ['all', 'notion']):
                    notion = NotionIntegration()
                    if notion.enabled:
                        if notion.delete_assignment_page(assignment):
                            deleted_count += 1
                            assignment['_deleted'] = True
                            if args.verbose:
                                print(f"   📝 Deleted from Notion: {assignment.get('title', 'Unknown')[:50]}")
            
            if platform == 'local' or target_platform == 'all':
                if platform == 'local' or target_platform in ['all', 'local']:
                    # For local deletion, we need to remove from the JSON file
                    fetcher = MoodleEmailFetcher()
                    local_assignments = fetcher.load_existing_assignments()
                    
                    # Find and remove the assignment
                    title_to_remove = assignment.get('title', '')
                    updated_assignments = [a for a in local_assignments if a.get('title') != title_to_remove]
                    
                    if len(updated_assignments) < len(local_assignments):
                        import json
                        with open('data/assignments.json', 'w') as f:
                            json.dump(updated_assignments, f, indent=2)
                        deleted_count += 1
                        assignment['_deleted'] = True
                        if args.verbose:
                            print(f"   📄 Deleted from local: {assignment.get('title', 'Unknown')[:50]}")
                            
        except Exception as e:
            if args.verbose:
                print(f"   ⚠️ Error deleting {assignment.get('title', 'Unknown')[:30]}: {e}")
    
    return deleted_count

def main():
    parser = argparse.ArgumentParser(description='Fetch Moodle assignments from Gmail')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days back to search for emails (default: 7)')
    parser.add_argument('--notion', action='store_true', 
                       help='Sync to Notion (requires Notion credentials)')
    parser.add_argument('--todoist', action='store_true', 
                       help='Sync to Todoist (requires Todoist API token)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable detailed progress logging with real-time status')
    parser.add_argument('--debug', '-d', action='store_true', 
                       help='Enable debug mode with maximum detail (includes --verbose)')
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Minimal output (only errors and final results)')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode - just check connection')
    parser.add_argument('--skip-notion', action='store_true',
                       help='Skip Notion integration even if configured')
    parser.add_argument('--skip-todoist', action='store_true',
                       help='Skip Todoist integration even if configured')
    parser.add_argument('--cleanup', action='store_true',
                       help='Run archive cleanup for completed assignments')
    parser.add_argument('--cleanup-days', type=int, default=30,
                       help='Days after completion to archive assignments (default: 30)')
    parser.add_argument('--restore', type=str, metavar='TITLE',
                       help='Restore assignment from archive by title')
    parser.add_argument('--archive-stats', action='store_true',
                       help='Show archive statistics')
    parser.add_argument('--manual-archive', type=str, metavar='TITLE',
                       help='Manually archive assignment by title')
    parser.add_argument('--show-duplicates', action='store_true',
                       help='Show detailed duplicate detection analysis')
    parser.add_argument('--status-report', action='store_true',
                       help='Show detailed status report of all assignments')
    parser.add_argument('--delete-all-assignments', action='store_true',
                       help='DELETE ALL assignments from database, Todoist, and Notion (DEBUG ONLY - emails are NOT touched)')
    parser.add_argument('--delete-from', type=str, choices=['notion', 'todoist', 'both'], default='both',
                       help='Choose where to delete assignments from: notion, todoist, or both (default: both)')
    parser.add_argument('--include-local', action='store_true',
                       help='Also delete assignments from local database when using selective deletion')
    parser.add_argument('--fresh-start', action='store_true',
                       help='DELETE ALL data files and start fresh (clears assignments.json, assignments.md, archive, backups - emails are NOT touched)')
    
    args = parser.parse_args()
    
    # Debug mode implies verbose
    if args.debug:
        args.verbose = True
    
    # Quiet mode overrides verbose/debug for console output (but not file logging)
    setup_logging(verbose=args.verbose and not args.quiet, debug=args.debug and not args.quiet)
    logger = logging.getLogger(__name__)
    
    if args.verbose and not args.quiet:
        print("🔍 VERBOSE MODE ENABLED - Detailed logging active")
        if args.debug:
            print("🐛 DEBUG MODE ENABLED - Maximum detail logging")
        print("=" * 60)
    
    # Initialize archive manager
    archive_manager = AssignmentArchiveManager()
    
    # Handle archive-specific commands first
    if args.archive_stats:
        stats = archive_manager.get_archive_stats()
        print("\n📊 ARCHIVE STATISTICS")
        print("=" * 30)
        print(f"Active assignments: {stats['active_assignments']}")
        print(f"Total archived: {stats['total_archived']}")
        print(f"Last cleanup: {stats['last_cleanup'] or 'Never'}")
        if stats['active_by_status']:
            print("\nActive assignments by status:")
            for status, count in stats['active_by_status'].items():
                print(f"  {status}: {count}")
        if stats['archived_by_reason']:
            print("\nArchived assignments by reason:")
            for reason, count in stats['archived_by_reason'].items():
                print(f"  {reason}: {count}")
        return 0
    
    if args.status_report:
        print("\n📋 DETAILED STATUS REPORT")
        print("=" * 50)
        try:
            fetcher = MoodleEmailFetcher()
            assignments = fetcher.load_existing_assignments()
            
            if not assignments:
                print("📄 No assignments found in database")
                return 0
            
            print(f"📊 Total assignments: {len(assignments)}")
            
            # Status breakdown
            status_counts = {}
            course_counts = {}
            overdue_assignments = []
            upcoming_assignments = []
            
            from datetime import datetime, date
            today = date.today()
            
            for assignment in assignments:
                # Count by status
                status = assignment.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by course
                course = assignment.get('course_code', 'Unknown')
                course_counts[course] = course_counts.get(course, 0) + 1
                
                # Check if overdue or upcoming
                try:
                    due_date = datetime.strptime(assignment['due_date'], '%Y-%m-%d').date()
                    days_diff = (due_date - today).days
                    
                    if days_diff < 0 and status != 'Completed':
                        overdue_assignments.append((assignment['title'], abs(days_diff)))
                    elif 0 <= days_diff <= 7 and status != 'Completed':
                        upcoming_assignments.append((assignment['title'], days_diff))
                except:
                    pass
            
            print(f"\n📈 Status Breakdown:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
            
            print(f"\n📚 Course Breakdown:")
            for course, count in sorted(course_counts.items()):
                print(f"  {course}: {count}")
            
            if overdue_assignments:
                print(f"\n⚠️ Overdue Assignments ({len(overdue_assignments)}):")
                for title, days_overdue in sorted(overdue_assignments, key=lambda x: x[1], reverse=True):
                    print(f"  📅 {title} (overdue by {days_overdue} days)")
            
            if upcoming_assignments:
                print(f"\n📅 Due This Week ({len(upcoming_assignments)}):")
                for title, days_until in sorted(upcoming_assignments, key=lambda x: x[1]):
                    if days_until == 0:
                        print(f"  🔥 {title} (due TODAY)")
                    else:
                        print(f"  📅 {title} (due in {days_until} days)")
            
            # Check sync status with integrations
            if not args.skip_notion:
                try:
                    notion = NotionIntegration()
                    if notion.enabled:
                        notion_assignments = notion.get_all_assignments_from_notion()
                        print(f"\n📝 Notion Status: {len(notion_assignments)} assignments in database")
                        missing_in_notion = len(assignments) - len(notion_assignments)
                        if missing_in_notion > 0:
                            print(f"  ⚠️ {missing_in_notion} assignments may be missing from Notion")
                except Exception as e:
                    print(f"\n📝 Notion Status: ❌ Error checking ({e})")
            
            if not args.skip_todoist:
                try:
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        print(f"\n✅ Todoist Status: Integration configured")
                        # Could add more detailed Todoist checking here
                except Exception as e:
                    print(f"\n✅ Todoist Status: ❌ Error checking ({e})")
                    
        except Exception as e:
            print(f"❌ Error generating status report: {e}")
            return 1
        return 0
    
    if args.show_duplicates:
        print("\n🔍 DUPLICATE DETECTION ANALYSIS")
        print("=" * 40)
        try:
            fetcher = MoodleEmailFetcher()
            assignments = fetcher.load_existing_assignments()
            
            if not assignments:
                print("📄 No assignments found in database")
                return 0
            
            print(f"🔍 Analyzing {len(assignments)} assignments for duplicates...")
            
            # Check for exact title duplicates
            title_groups = {}
            for assignment in assignments:
                title = assignment.get('title_normalized', assignment.get('title', '')).lower()
                if title not in title_groups:
                    title_groups[title] = []
                title_groups[title].append(assignment)
            
            exact_duplicates = {title: group for title, group in title_groups.items() if len(group) > 1}
            
            if exact_duplicates:
                print(f"\n⚠️ Found {len(exact_duplicates)} groups with exact title matches:")
                for title, group in exact_duplicates.items():
                    print(f"\n  📝 '{title}' ({len(group)} instances):")
                    for assignment in group:
                        print(f"    - Email ID: {assignment.get('email_id', 'N/A')}")
                        print(f"      Due: {assignment.get('due_date', 'N/A')}")
                        print(f"      Status: {assignment.get('status', 'N/A')}")
            
            # Check for email ID duplicates
            email_groups = {}
            for assignment in assignments:
                email_id = assignment.get('email_id', '')
                if email_id:
                    if email_id not in email_groups:
                        email_groups[email_id] = []
                    email_groups[email_id].append(assignment)
            
            email_duplicates = {eid: group for eid, group in email_groups.items() if len(group) > 1}
            
            if email_duplicates:
                print(f"\n⚠️ Found {len(email_duplicates)} duplicate email IDs:")
                for email_id, group in email_duplicates.items():
                    print(f"\n  📧 Email ID: {email_id} ({len(group)} instances)")
                    for assignment in group:
                        print(f"    - Title: {assignment.get('title', 'N/A')}")
                        print(f"      Due: {assignment.get('due_date', 'N/A')}")
            
            if not exact_duplicates and not email_duplicates:
                print("✅ No exact duplicates found!")
            
            # Fuzzy matching for similar titles
            print(f"\n🔍 Checking for similar titles (fuzzy matching)...")
            try:
                from fuzzywuzzy import fuzz
                similar_pairs = []
                
                for i, assignment1 in enumerate(assignments):
                    for j, assignment2 in enumerate(assignments[i+1:], i+1):
                        title1 = assignment1.get('title_normalized', assignment1.get('title', '')).lower()
                        title2 = assignment2.get('title_normalized', assignment2.get('title', '')).lower()
                        
                        if title1 and title2:
                            similarity = fuzz.ratio(title1, title2)
                            if similarity > 80 and similarity < 100:  # Similar but not exact
                                similar_pairs.append((assignment1, assignment2, similarity))
                
                if similar_pairs:
                    print(f"⚠️ Found {len(similar_pairs)} potentially similar assignments:")
                    for assign1, assign2, similarity in sorted(similar_pairs, key=lambda x: x[2], reverse=True):
                        print(f"\n  🔗 {similarity}% similar:")
                        print(f"    1. {assign1.get('title', 'N/A')} (Due: {assign1.get('due_date', 'N/A')})")
                        print(f"    2. {assign2.get('title', 'N/A')} (Due: {assign2.get('due_date', 'N/A')})")
                else:
                    print("✅ No similar titles found!")
                    
            except ImportError:
                print("⚠️ fuzzywuzzy not available for similarity checking")
                
        except Exception as e:
            print(f"❌ Error in duplicate analysis: {e}")
            return 1
        return 0
    
    if args.fresh_start:
        print("\n🔥 FRESH START - DELETING ALL DATA FILES")
        print("=" * 50)
        print("⚠️ WARNING: This will permanently delete:")
        print("  📄 All assignment data (assignments.json)")
        print("  📋 Assignment markdown file (assignments.md)")
        print("  📦 Archive files (assignments_archive.json)")
        print("  💾 All backup files")
        print("  📊 Any other data files in the data/ folder")
        print()
        print("✅ Your Gmail emails will NOT be touched!")
        print("✅ Your .env configuration will NOT be touched!")
        print()
        
        # Double confirmation for fresh start
        try:
            response = input("⚠️ Type 'FRESH START' to confirm total reset: ")
            if response != 'FRESH START':
                print("❌ Fresh start cancelled.")
                return 0
        except KeyboardInterrupt:
            print("\n❌ Fresh start cancelled.")
            return 0
        
        try:
            import os
            import glob
            
            # Create data directory if it doesn't exist
            if not os.path.exists('data'):
                os.makedirs('data')
                print("📁 Created data directory")
            
            # List all files in data directory before deletion
            data_files = glob.glob('data/*')
            
            if data_files:
                print(f"\n🗑️ Deleting {len(data_files)} files from data/ folder:")
                for file_path in data_files:
                    try:
                        if os.path.isfile(file_path):
                            filename = os.path.basename(file_path)
                            os.remove(file_path)
                            print(f"   ✅ Deleted: {filename}")
                        elif os.path.isdir(file_path):
                            import shutil
                            dirname = os.path.basename(file_path)
                            shutil.rmtree(file_path)
                            print(f"   ✅ Deleted directory: {dirname}")
                    except Exception as e:
                        print(f"   ⚠️ Could not delete {os.path.basename(file_path)}: {e}")
            else:
                print("📄 Data folder was already empty")
            
            # Create fresh empty files
            print(f"\n🆕 Creating fresh data files:")
            
            # Empty assignments.json
            import json
            with open('data/assignments.json', 'w') as f:
                json.dump([], f, indent=2)
            print("   ✅ Created empty assignments.json")
            
            # Empty assignments.md
            with open('data/assignments.md', 'w') as f:
                f.write("# Moodle Assignments\n\n")
                f.write("| Assignment | Due Date | Course | Status | Added Date |\n")
                f.write("|------------|----------|--------|--------|-----------|\n")
            print("   ✅ Created empty assignments.md")
            
            # Empty archive file
            archive_data = {
                "archived_assignments": [],
                "archive_metadata": {
                    "created": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "last_cleanup": None,
                    "total_archived": 0
                }
            }
            with open('data/assignments_archive.json', 'w') as f:
                json.dump(archive_data, f, indent=2)
            print("   ✅ Created empty assignments_archive.json")
            
            print(f"\n🎉 FRESH START COMPLETED!")
            print("=" * 30)
            print("✅ All data files have been reset")
            print("✅ Ready for a completely fresh start")
            print("📧 Your Gmail emails are completely untouched")
            print("⚙️ Your .env configuration is preserved")
            print()
            print("💡 Next steps:")
            print("  1. Run './deployment/run.sh check' to fetch assignments")
            print("  2. Run './deployment/run.sh notion' to sync to Notion")
            print("  3. Run './deployment/run.sh todoist' to sync to Todoist")
            print()
            
        except Exception as e:
            print(f"❌ Error during fresh start: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    if args.delete_all_assignments:
        print("\n🗑️ DELETING ALL ASSIGNMENTS")
        print("=" * 40)
        
        # Show what will be deleted based on --delete-from option
        delete_from = args.delete_from
        include_local = args.include_local
        print("⚠️ WARNING: This will delete assignments from:")
        if include_local or delete_from == 'both':
            print("  📄 Local database (assignments.json)")
        if delete_from in ['todoist', 'both']:
            print("  ✅ Todoist (if configured)")
        if delete_from in ['notion', 'both']:
            print("  📝 Notion (if configured)")
        print("  ✅ Your Gmail emails will NOT be touched!")
        print("  ✅ Your .env configuration will NOT be touched!")
        print()
        
        if delete_from != 'both':
            mode_text = f"{delete_from.upper()}"
            if include_local:
                mode_text += " + LOCAL DATABASE"
            print(f"🎯 SELECTIVE MODE: Only deleting from {mode_text}")
            print()
        elif include_local:
            print("🎯 FULL MODE: Deleting from both platforms + local database")
            print()
        
        # Double confirmation
        try:
            response = input("Type 'DELETE' to confirm: ")
            if response != 'DELETE':
                print("❌ Deletion cancelled.")
                return 0
        except KeyboardInterrupt:
            print("\n❌ Deletion cancelled.")
            return 0
        
        deleted_counts = {"local": 0, "todoist": 0, "notion": 0}
        
        try:
            # Get assignments from local database as the authoritative source
            fetcher = MoodleEmailFetcher()
            assignments = fetcher.load_existing_assignments()
            
            if not assignments:
                print("❌ No assignments found in local database")
                print("💡 Run './deployment/run.sh check' first to populate the database")
                return 0
            
            print(f"\n� Found {len(assignments)} assignments to delete from local database")
            
            if args.verbose:
                print("\n📋 Assignments to be deleted:")
                for i, assignment in enumerate(assignments, 1):
                    print(f"   {i}. {assignment.get('title', 'Unknown')}")
                    print(f"      Course: {assignment.get('course_code', 'Unknown')}")
                    print(f"      Due: {assignment.get('due_date', 'Unknown')}")
                print()
            
            # Delete from Todoist first (if configured and requested)
            if not args.skip_todoist and delete_from in ['todoist', 'both']:
                try:
                    print("✅ Deleting from Todoist...")
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        for assignment in assignments:
                            try:
                                # Try to find and delete the task
                                task_deleted = todoist.delete_assignment_task(assignment)
                                if task_deleted:
                                    deleted_counts["todoist"] += 1
                                    if args.verbose:
                                        print(f"   ✅ Deleted from Todoist: {assignment.get('title', 'Unknown')[:50]}")
                            except Exception as e:
                                if args.verbose:
                                    print(f"   ⚠️ Could not delete from Todoist: {assignment.get('title', 'Unknown')[:50]} - {e}")
                        
                        print(f"✅ Deleted {deleted_counts['todoist']} assignments from Todoist")
                    else:
                        print("⚠️ Todoist not configured - skipping")
                except Exception as e:
                    print(f"❌ Error deleting from Todoist: {e}")
            elif delete_from == 'notion':
                print("⏭️ Skipping Todoist deletion (notion-only mode)")
            
            # Delete from Notion (if configured and requested)
            if not args.skip_notion and delete_from in ['notion', 'both']:
                try:
                    print("📝 Deleting from Notion...")
                    notion = NotionIntegration()
                    if notion.enabled:
                        for assignment in assignments:
                            try:
                                # Try to find and delete the page
                                page_deleted = notion.delete_assignment_page(assignment)
                                if page_deleted:
                                    deleted_counts["notion"] += 1
                                    if args.verbose:
                                        print(f"   📝 Deleted from Notion: {assignment.get('title', 'Unknown')[:50]}")
                            except Exception as e:
                                if args.verbose:
                                    print(f"   ⚠️ Could not delete from Notion: {assignment.get('title', 'Unknown')[:50]} - {e}")
                        
                        print(f"📝 Deleted {deleted_counts['notion']} assignments from Notion")
                    else:
                        print("⚠️ Notion not configured - skipping")
                except Exception as e:
                    print(f"❌ Error deleting from Notion: {e}")
            elif delete_from == 'todoist':
                print("⏭️ Skipping Notion deletion (todoist-only mode)")
            
            # Delete from local database (only if requested)
            if include_local or delete_from == 'both':
                print("📄 Deleting from local database...")
                try:
                    import os
                    import json
                    
                    # Get current local assignments for backup
                    local_assignments = fetcher.load_existing_assignments()
                    
                    if local_assignments:
                        # Backup before deletion
                        backup_file = f"data/assignments_backup_before_delete_{int(time.time())}.json"
                        with open(backup_file, 'w') as f:
                            json.dump(local_assignments, f, indent=2)
                        print(f"💾 Backup created: {backup_file}")
                        
                        # Clear assignments
                        with open('data/assignments.json', 'w') as f:
                            json.dump([], f, indent=2)
                        
                        # Clear markdown file
                        with open('data/assignments.md', 'w') as f:
                            f.write("# Moodle Assignments\n\n")
                            f.write("| Assignment | Due Date | Course | Status | Added Date |\n")
                            f.write("|------------|----------|--------|--------|-----------|\n")
                        
                        deleted_counts["local"] = len(local_assignments)
                        print(f"📄 Deleted {deleted_counts['local']} assignments from local database")
                    else:
                        print("📄 Local database was already empty")
                    
                except Exception as e:
                    print(f"❌ Error deleting from local database: {e}")
                    return 1
            else:
                print("⏭️ Skipping local database deletion (not requested)")
            
            # Summary
            print(f"\n🎯 DELETION SUMMARY")
            print("=" * 30)
            if include_local or delete_from == 'both':
                print(f"📄 Local database: {deleted_counts['local']} deleted")
            else:
                print(f"📄 Local database: skipped (not requested)")
            if delete_from in ['todoist', 'both']:
                print(f"✅ Todoist: {deleted_counts['todoist']} deleted")
            else:
                print(f"✅ Todoist: skipped (not requested)")
            if delete_from in ['notion', 'both']:
                print(f"📝 Notion: {deleted_counts['notion']} deleted")
            else:
                print(f"📝 Notion: skipped (not requested)")
            print()
            if delete_from == 'both' and include_local:
                print("✅ All assignments deleted successfully!")
            elif delete_from == 'both':
                print("✅ Assignments deleted from both platforms successfully!")
            else:
                mode_text = delete_from.upper()
                if include_local:
                    mode_text += " + LOCAL DATABASE"
                print(f"✅ Assignments deleted from {mode_text} successfully!")
            print("💡 Your Gmail emails are completely untouched")
            print("🔄 Run './deployment/run.sh check' to fetch fresh assignments")
            
            # Check for remaining assignments and offer interactive deletion
            remaining_assignments = check_remaining_assignments_after_deletion(delete_from, include_local, args)
            if remaining_assignments:
                interactive_deletion_menu(remaining_assignments, args)
            
        except Exception as e:
            print(f"❌ Error during deletion: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1
        
        return 0
    
    if args.restore:
        print(f"🔄 Restoring assignment: {args.restore}")
        if archive_manager.restore_assignment_from_archive(args.restore):
            print(f"✅ Successfully restored: {args.restore}")
        else:
            print(f"❌ Failed to restore: {args.restore}")
        return 0
    
    if args.manual_archive:
        print(f"📦 Manually archiving assignment: {args.manual_archive}")
        if archive_manager.manual_archive_assignment(args.manual_archive):
            print(f"✅ Successfully archived: {args.manual_archive}")
        else:
            print(f"❌ Failed to archive: {args.manual_archive}")
        return 0
    
    if args.cleanup:
        print(f"🧹 Running archive cleanup (completed assignments older than {args.cleanup_days} days)")
        result = archive_manager.archive_completed_assignments(args.cleanup_days)
        print(f"📦 Archive cleanup results:")
        print(f"  Active assignments: {result['active_count']}")
        print(f"  Newly archived: {result['newly_archived_count']}")
        print(f"  Total archived: {result['total_archived']}")
        if result['newly_archived']:
            print(f"  Archived assignments: {', '.join(result['newly_archived'])}")
        return 0
    
    try:
        logger.info("=" * 50)
        logger.info("MOODLE ASSIGNMENT FETCHER STARTED")
        logger.info("=" * 50)
        
        # Initialize fetcher
        logger.info("Initializing Moodle email fetcher...")
        fetcher = MoodleEmailFetcher()
        
        if args.test:
            # Test connections with verbose feedback
            if args.verbose:
                print("\n🧪 TESTING ALL CONNECTIONS")
                print("=" * 40)
            
            logger.info("Testing Gmail connection...")
            try:
                if args.verbose:
                    print("📧 Testing Gmail IMAP connection...")
                mail = fetcher.connect_to_gmail()
                mail.logout()
                print("✅ Gmail connection successful!")
                if args.verbose:
                    print("   ✓ IMAP authentication working")
                    print("   ✓ Connection established and closed properly")
            except Exception as e:
                print(f"❌ Gmail connection failed: {e}")
                if args.verbose:
                    print(f"   ✗ Error details: {str(e)}")
                return 1
            
            if args.notion and not args.skip_notion:
                logger.info("Testing Notion connection...")
                try:
                    if args.verbose:
                        print("\n📝 Testing Notion integration...")
                    notion = NotionIntegration()
                    if notion.enabled:
                        print("✅ Notion integration configured and connected!")
                        if args.verbose:
                            print("   ✓ API token valid")
                            print("   ✓ Database accessible")
                            # Test actual API call
                            try:
                                test_assignments = notion.get_all_assignments_from_notion()
                                print(f"   ✓ Found {len(test_assignments)} assignments in database")
                            except Exception as e:
                                print(f"   ⚠️ Database query warning: {e}")
                    else:
                        print("⚠️ Notion integration not configured")
                        if args.verbose:
                            print("   ✗ Missing NOTION_TOKEN or NOTION_DATABASE_ID in .env")
                except Exception as e:
                    print(f"❌ Notion connection failed: {e}")
                    if args.verbose:
                        print(f"   ✗ Error details: {str(e)}")
            
            if args.todoist and not args.skip_todoist:
                logger.info("Testing Todoist connection...")
                try:
                    if args.verbose:
                        print("\n✅ Testing Todoist integration...")
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        print("✅ Todoist integration configured and connected!")
                        if args.verbose:
                            print("   ✓ API token valid")
                            # Test actual API call
                            try:
                                projects = todoist.api.get_projects()
                                print(f"   ✓ Found {len(projects)} projects in account")
                                assignment_project = todoist.get_or_create_project("Assignments")
                                print(f"   ✓ Assignment project ready (ID: {assignment_project})")
                            except Exception as e:
                                print(f"   ⚠️ API test warning: {e}")
                    else:
                        print("⚠️ Todoist integration not configured")
                        if args.verbose:
                            print("   ✗ Missing TODOIST_API_TOKEN in .env")
                except Exception as e:
                    print(f"❌ Todoist connection failed: {e}")
                    if args.verbose:
                        print(f"   ✗ Error details: {str(e)}")
            
            if args.verbose:
                print("\n🎯 All connection tests completed!")
            return 0
        
        # Run the main check with enhanced verbose logging
        if args.verbose:
            print(f"\n🔍 FETCHING ASSIGNMENTS")
            print("=" * 40)
            print(f"📅 Searching emails from last {args.days} days")
            print(f"📧 Connecting to Gmail...")
        
        logger.info(f"Checking for assignments from the past {args.days} days...")
        
        # Load existing assignments first for comparison
        existing_assignments = fetcher.load_existing_assignments()
        existing_count = len(existing_assignments)
        
        if args.verbose:
            print(f"📄 Found {existing_count} existing assignments in database")
            if existing_count > 0:
                # Show status breakdown
                status_counts = {}
                for assignment in existing_assignments:
                    status = assignment.get('status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                print("   Status breakdown:", ", ".join([f"{status}: {count}" for status, count in status_counts.items()]))
        
        # Run the check
        new_count = fetcher.run_check(args.days)
        
        # Reload assignments to see what was added
        updated_assignments = fetcher.load_existing_assignments()
        final_count = len(updated_assignments)
        
        if args.verbose and new_count > 0:
            print(f"\n📊 PROCESSING RESULTS")
            print("=" * 30)
            print(f"✅ Found {new_count} NEW assignments")
            print(f"📈 Total assignments: {existing_count} → {final_count}")
            
            # Show the new assignments
            new_assignments = updated_assignments[-new_count:] if new_count <= final_count else updated_assignments
            print(f"\n📝 New assignments added:")
            for i, assignment in enumerate(new_assignments, 1):
                print(f"   {i}. {assignment.get('title', 'Unknown Title')}")
                print(f"      Course: {assignment.get('course_code', 'Unknown')}")
                print(f"      Due: {assignment.get('due_date', 'Unknown')}")
                print(f"      Status: {assignment.get('status', 'Pending')}")
                if args.debug:
                    print(f"      Email ID: {assignment.get('email_id', 'N/A')}")
                print()
        
        if new_count > 0:
            print(f"✅ Successfully found {new_count} new assignments!")
            logger.info(f"Successfully added {new_count} new assignments!")
            
            # Sync to Notion if requested and not skipped
            if args.notion and not args.skip_notion:
                try:
                    if args.verbose:
                        print(f"\n📝 NOTION SYNC")
                        print("=" * 20)
                        print("🔗 Initializing Notion integration...")
                    
                    logger.info("Initializing Notion integration...")
                    notion = NotionIntegration()
                    if notion.enabled:
                        assignments = fetcher.load_existing_assignments()
                        # Only sync recent assignments (avoid duplicates)
                        recent_assignments = assignments[-new_count:] if new_count <= len(assignments) else assignments
                        
                        if args.verbose:
                            print(f"📊 Syncing {len(recent_assignments)} new assignments to Notion...")
                            for i, assignment in enumerate(recent_assignments, 1):
                                print(f"   {i}. Syncing: {assignment.get('title', 'Unknown')[:50]}...")
                        
                        logger.info(f"Syncing {len(recent_assignments)} new assignments to Notion...")
                        notion_count = notion.sync_assignments(recent_assignments)
                        
                        print(f"📝 Synced {notion_count} assignments to Notion!")
                        logger.info(f"Successfully synced {notion_count} assignments to Notion")
                        
                        if args.verbose:
                            if notion_count != len(recent_assignments):
                                print(f"   ⚠️ Note: {len(recent_assignments) - notion_count} assignments may have been skipped (already exist)")
                            else:
                                print("   ✅ All assignments synced successfully")
                    else:
                        print("⚠️ Notion integration not configured")
                        logger.warning("Notion integration not available")
                        if args.verbose:
                            print("   💡 Add NOTION_TOKEN and NOTION_DATABASE_ID to .env to enable")
                except Exception as e:
                    print(f"⚠️ Notion sync failed: {e}")
                    logger.error(f"Notion integration failed: {e}")
                    if args.debug:
                        import traceback
                        logger.error(traceback.format_exc())
                    logger.info("Continuing without Notion integration...")
            
            # Sync to Todoist if requested and not skipped
            if args.todoist and not args.skip_todoist:
                try:
                    if args.verbose:
                        print(f"\n✅ TODOIST SYNC")
                        print("=" * 20)
                        print("🔗 Initializing Todoist integration...")
                    
                    logger.info("Initializing Todoist integration...")
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        assignments = fetcher.load_existing_assignments()
                        # Only sync recent assignments (avoid duplicates)
                        recent_assignments = assignments[-new_count:] if new_count <= len(assignments) else assignments
                        
                        if args.verbose:
                            print(f"📊 Syncing {len(recent_assignments)} new assignments to Todoist...")
                            for i, assignment in enumerate(recent_assignments, 1):
                                print(f"   {i}. Creating task: {assignment.get('title', 'Unknown')[:50]}...")
                        
                        logger.info(f"Syncing {len(recent_assignments)} new assignments to Todoist...")
                        todoist_count = todoist.sync_assignments(recent_assignments)
                        
                        print(f"✅ Synced {todoist_count} assignments to Todoist!")
                        logger.info(f"Successfully synced {todoist_count} assignments to Todoist")
                        
                        if args.verbose:
                            if todoist_count != len(recent_assignments):
                                print(f"   ⚠️ Note: {len(recent_assignments) - todoist_count} assignments may have been skipped (already exist)")
                            else:
                                print("   ✅ All assignments synced successfully")
                    else:
                        print("⚠️ Todoist integration not configured")
                        logger.warning("Todoist integration not available")
                        if args.verbose:
                            print("   💡 Add TODOIST_API_TOKEN to .env to enable")
                except Exception as e:
                    print(f"⚠️ Todoist sync failed: {e}")
                    logger.error(f"Todoist integration failed: {e}")
                    if args.debug:
                        import traceback
                        logger.error(traceback.format_exc())
                    logger.info("Continuing without Todoist integration...")
                    
        elif new_count == 0:
            print("ℹ️ No new assignments found.")
            logger.info("No new assignments found")
            
            # Even if no new assignments, check if existing ones need to be synced to Notion
            if args.notion and not args.skip_notion:
                try:
                    logger.info("Checking existing assignments for Notion sync...")
                    notion = NotionIntegration()
                    if notion.enabled:
                        assignments = fetcher.load_existing_assignments()
                        if assignments:
                            logger.info(f"Checking {len(assignments)} existing assignments against Notion...")
                            print(f"🔍 Checking {len(assignments)} assignments against Notion database...")
                            
                            # Check each assignment to see if it exists in Notion
                            assignments_to_sync = []
                            
                            for assignment in assignments:
                                try:
                                    # Check if this specific assignment exists in Notion
                                    if not notion.assignment_exists_in_notion(assignment):
                                        assignments_to_sync.append(assignment)
                                        logger.info(f"Missing from Notion: {assignment.get('title')}")
                                    else:
                                        logger.debug(f"Already in Notion: {assignment.get('title')}")
                                except Exception as e:
                                    logger.warning(f"Could not check Notion for '{assignment.get('title')}': {e}")
                                    # If we can't check, assume it needs to be synced
                                    assignments_to_sync.append(assignment)
                            
                            if assignments_to_sync:
                                logger.info(f"Found {len(assignments_to_sync)} assignments missing from Notion")
                                print(f"📝 Syncing {len(assignments_to_sync)} missing assignments to Notion...")
                                notion_count = notion.sync_assignments(assignments_to_sync)
                                print(f"✅ Successfully synced {notion_count} assignments to Notion!")
                                logger.info(f"Successfully synced {notion_count} assignments to Notion")
                            else:
                                print("✅ All assignments already exist in Notion")
                                logger.info("All assignments already exist in Notion")
                        else:
                            print("📄 No assignments found in local database")
                            logger.info("No assignments found in local database")
                    else:
                        print("⚠️ Notion integration not configured")
                        logger.warning("Notion integration not available")
                except Exception as e:
                    print(f"⚠️ Notion sync failed: {e}")
                    logger.error(f"Notion integration failed: {e}")
                    logger.info("Continuing without Notion integration...")
            
            # Even if no new assignments, check if existing ones need to be synced to Todoist
            if args.todoist and not args.skip_todoist:
                try:
                    logger.info("Checking existing assignments for Todoist sync...")
                    todoist = TodoistIntegration()
                    if todoist.enabled:
                        assignments = fetcher.load_existing_assignments()
                        if assignments:
                            logger.info(f"Checking {len(assignments)} existing assignments against Todoist...")
                            print(f"🔍 Checking {len(assignments)} assignments against Todoist...")
                            
                            # Check each assignment to see if it exists in Todoist
                            assignments_to_sync = []
                            
                            for assignment in assignments:
                                try:
                                    # Check if this specific assignment exists in Todoist
                                    if not todoist.task_exists_in_todoist(assignment):
                                        assignments_to_sync.append(assignment)
                                        logger.info(f"Missing from Todoist: {assignment.get('title')}")
                                    else:
                                        logger.debug(f"Already in Todoist: {assignment.get('title')}")
                                except Exception as e:
                                    logger.warning(f"Could not check Todoist for '{assignment.get('title')}': {e}")
                                    # If we can't check, assume it needs to be synced
                                    assignments_to_sync.append(assignment)
                            
                            if assignments_to_sync:
                                logger.info(f"Found {len(assignments_to_sync)} assignments missing from Todoist")
                                print(f"✅ Syncing {len(assignments_to_sync)} missing assignments to Todoist...")
                                todoist_count = todoist.sync_assignments(assignments_to_sync)
                                print(f"✅ Successfully synced {todoist_count} assignments to Todoist!")
                                logger.info(f"Successfully synced {todoist_count} assignments to Todoist")
                            else:
                                print("✅ All assignments already exist in Todoist")
                                logger.info("All assignments already exist in Todoist")
                        else:
                            print("📄 No assignments found in local database")
                            logger.info("No assignments found in local database")
                    else:
                        print("⚠️ Todoist integration not configured")
                        logger.warning("Todoist integration not available")
                except Exception as e:
                    print(f"⚠️ Todoist sync failed: {e}")
                    logger.error(f"Todoist integration failed: {e}")
                    logger.info("Continuing without Todoist integration...")
        else:
            print("❌ Error occurred during check.")
            logger.error("Error occurred during assignment check")
            return 1

        # Auto-cleanup: Archive completed assignments (only if not running specific archive commands)
        if not any([args.cleanup, args.restore, args.manual_archive, args.archive_stats]):
            try:
                logger.info("Running automatic archive cleanup...")
                result = archive_manager.archive_completed_assignments(args.cleanup_days)
                
                if result['newly_archived_count'] > 0:
                    print(f"🧹 Automatic cleanup: Archived {result['newly_archived_count']} completed assignments")
                    logger.info(f"Automatic cleanup archived {result['newly_archived_count']} assignments: {result['newly_archived']}")
                else:
                    logger.debug("Automatic cleanup: No assignments need archiving")
                    
            except Exception as e:
                logger.warning(f"Automatic archive cleanup failed: {e}")
                print(f"⚠️ Archive cleanup warning: {e}")

        # Status sync from Notion (if Notion is enabled and available)
        if args.notion and not args.skip_notion:
            try:
                logger.info("Syncing assignment status from Notion...")
                notion = NotionIntegration()
                if notion.enabled:
                    # Get current assignments from Notion to sync status
                    notion_assignments = notion.get_all_assignments_from_notion()
                    if notion_assignments:
                        sync_result = archive_manager.smart_status_sync(notion_assignments)
                        
                        if sync_result['updated_count'] > 0 or sync_result['restored_count'] > 0:
                            print(f"🔄 Notion sync: Updated {sync_result['updated_count']}, Restored {sync_result['restored_count']} assignments")
                            logger.info(f"Notion status sync completed: {sync_result['updated_count']} updated, {sync_result['restored_count']} restored")
                        else:
                            logger.debug("Notion status sync: No changes needed")
                    else:
                        logger.debug("No assignments found in Notion for status sync")
                        
            except Exception as e:
                logger.warning(f"Status sync from Notion failed: {e}")
                print(f"⚠️ Notion status sync warning: {e}")

        # Status sync from Todoist (if Todoist is enabled and available)
        if args.todoist and not args.skip_todoist:
            try:
                logger.info("Syncing assignment status from Todoist...")
                todoist = TodoistIntegration()
                if todoist.enabled:
                    # Get current local assignments
                    fetcher = MoodleEmailFetcher()
                    local_assignments = fetcher.load_existing_assignments()
                    
                    if local_assignments:
                        # Sync status from Todoist
                        todoist_sync_result = todoist.sync_status_from_todoist(local_assignments)
                        
                        if todoist_sync_result['updated'] > 0:
                            # Save updated assignments back to file
                            fetcher.save_assignments(local_assignments)
                            print(f"🔄 Todoist sync: Updated {todoist_sync_result['updated']} assignments to Completed")
                            logger.info(f"Todoist status sync: Updated {todoist_sync_result['updated']} assignments")
                            
                            # Log which assignments were marked as completed
                            for assignment_title in todoist_sync_result['completed_in_todoist']:
                                logger.info(f"Marked as completed (from Todoist): {assignment_title}")
                        else:
                            logger.debug("Todoist status sync: No changes needed")
                    else:
                        logger.debug("No local assignments found for Todoist status sync")
                        
            except Exception as e:
                logger.warning(f"Status sync from Todoist failed: {e}")
                print(f"⚠️ Todoist status sync warning: {e}")
        
        logger.info("=" * 50)
        logger.info("MOODLE ASSIGNMENT FETCHER COMPLETED")
        logger.info("=" * 50)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("⚠️ Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
