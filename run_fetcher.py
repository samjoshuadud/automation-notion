#!/usr/bin/env python3
"""
Enhanced Moodle Assignment Fetcher with Notion Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moodle_fetcher import MoodleEmailFetcher
from notion_integration import NotionIntegration
from assignment_archive import AssignmentArchiveManager
import argparse
import logging

def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('moodle_fetcher.log'),
            logging.StreamHandler()
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Fetch Moodle assignments from Gmail')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days back to search for emails (default: 7)')
    parser.add_argument('--notion', action='store_true', 
                       help='Sync to Notion (requires Notion credentials)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--test', action='store_true', 
                       help='Test mode - just check connection')
    parser.add_argument('--skip-notion', action='store_true',
                       help='Skip Notion integration even if configured')
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
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
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
            # Test connections
            logger.info("Testing Gmail connection...")
            try:
                mail = fetcher.connect_to_gmail()
                mail.logout()
                print("✅ Gmail connection successful!")
            except Exception as e:
                print(f"❌ Gmail connection failed: {e}")
                return 1
            
            if args.notion and not args.skip_notion:
                logger.info("Testing Notion connection...")
                try:
                    notion = NotionIntegration()
                    if notion.enabled:
                        print("✅ Notion integration configured and connected!")
                    else:
                        print("⚠️ Notion integration not configured")
                except Exception as e:
                    print(f"❌ Notion connection failed: {e}")
            return 0
        
        # Run the main check
        logger.info(f"Checking for assignments from the past {args.days} days...")
        new_count = fetcher.run_check(args.days)
        
        if new_count > 0:
            print(f"✅ Successfully found {new_count} new assignments!")
            logger.info(f"Successfully added {new_count} new assignments!")
            
            # Sync to Notion if requested and not skipped
            if args.notion and not args.skip_notion:
                try:
                    logger.info("Initializing Notion integration...")
                    notion = NotionIntegration()
                    if notion.enabled:
                        assignments = fetcher.load_existing_assignments()
                        # Only sync recent assignments (avoid duplicates)
                        recent_assignments = assignments[-new_count:] if new_count <= len(assignments) else assignments
                        logger.info(f"Syncing {len(recent_assignments)} new assignments to Notion...")
                        notion_count = notion.sync_assignments(recent_assignments)
                        print(f"📝 Synced {notion_count} assignments to Notion!")
                        logger.info(f"Successfully synced {notion_count} assignments to Notion")
                    else:
                        print("⚠️ Notion integration not configured")
                        logger.warning("Notion integration not available")
                except Exception as e:
                    print(f"⚠️ Notion sync failed: {e}")
                    logger.error(f"Notion integration failed: {e}")
                    logger.info("Continuing without Notion integration...")
                    
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
                            print(f"🔄 Status sync: Updated {sync_result['updated_count']}, Restored {sync_result['restored_count']} assignments")
                            logger.info(f"Status sync completed: {sync_result['updated_count']} updated, {sync_result['restored_count']} restored")
                        else:
                            logger.debug("Status sync: No changes needed")
                    else:
                        logger.debug("No assignments found in Notion for status sync")
                        
            except Exception as e:
                logger.warning(f"Status sync from Notion failed: {e}")
                print(f"⚠️ Status sync warning: {e}")
        
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
