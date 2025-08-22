#!/usr/bin/env python3
"""
Assignment Archive Manager
Handles status-based archiving and restoration of assignments
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AssignmentArchiveManager:
    def __init__(self, assignments_file: str = 'data/assignments.json', archive_file: str = 'data/assignments_archive.json'):
        self.assignments_file = assignments_file
        self.archive_file = archive_file
        self._initialize_archive()
    
    def _initialize_archive(self):
        """Initialize archive file if it doesn't exist"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.archive_file), exist_ok=True)
            
            if not os.path.exists(self.archive_file):
                initial_archive = {
                    "created_date": datetime.now().isoformat(),
                    "last_cleanup": None,
                    "total_archived": 0,
                    "assignments": []
                }
                with open(self.archive_file, 'w') as f:
                    json.dump(initial_archive, f, indent=2)
                logger.info(f"Created new archive file: {self.archive_file}")
        except Exception as e:
            logger.error(f"Failed to initialize archive file {self.archive_file}: {e}")
            # Create minimal fallback
            try:
                os.makedirs(os.path.dirname(self.archive_file), exist_ok=True)
                with open(self.archive_file, 'w') as f:
                    json.dump({"assignments": [], "total_archived": 0}, f, indent=2)
            except Exception as fallback_e:
                logger.error(f"Failed to create fallback archive file: {fallback_e}")
    
    def load_assignments(self) -> List[Dict]:
        """Load active assignments"""
        try:
            with open(self.assignments_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_assignments(self, assignments: List[Dict]):
        """Save active assignments"""
        with open(self.assignments_file, 'w') as f:
            json.dump(assignments, f, indent=2)
    
    def load_archive(self) -> Dict:
        """Load archive data"""
        try:
            with open(self.archive_file, 'r') as f:
                return json.load(f)
        except:
            return {"assignments": [], "total_archived": 0}
    
    def save_archive(self, archive_data: Dict):
        """Save archive data"""
        archive_data["last_cleanup"] = datetime.now().isoformat()
        with open(self.archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
    
    def archive_completed_assignments(self, days_after_completion: int = 30) -> Dict:
        """Archive assignments that have been completed for specified days"""
        
        logger.info(f"Starting archive cleanup (completed assignments older than {days_after_completion} days)")
        
        assignments = self.load_assignments()
        archive_data = self.load_archive()
        
        active_assignments = []
        newly_archived = []
        
        cutoff_date = datetime.now() - timedelta(days=days_after_completion)
        
        for assignment in assignments:
            should_archive = False
            archive_reason = ""
            
            # Check if assignment should be archived
            if assignment.get('status') == 'Completed':
                # Check completion date (use last_updated as proxy for completion date)
                last_updated = assignment.get('last_updated', assignment.get('added_date', ''))
                if last_updated:
                    try:
                        # Handle different date formats
                        if 'T' in last_updated:
                            completion_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        else:
                            completion_date = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
                        
                        if completion_date < cutoff_date:
                            should_archive = True
                            archive_reason = f"completed_{days_after_completion}_days"
                            
                    except ValueError as e:
                        logger.warning(f"Could not parse date '{last_updated}' for assignment {assignment.get('title', 'Unknown')}: {e}")
            
            if should_archive:
                # Archive the assignment
                archived_assignment = {
                    "original_data": assignment,
                    "archived_date": datetime.now().isoformat(),
                    "archive_reason": archive_reason,
                    "completion_date": last_updated,
                    "title": assignment.get('title', 'Unknown'),
                    "course_code": assignment.get('course_code', 'Unknown')
                }
                
                archive_data["assignments"].append(archived_assignment)
                newly_archived.append(assignment.get('title', 'Unknown'))
                logger.info(f"Archived completed assignment: {assignment.get('title', 'Unknown')}")
                
            else:
                # Keep in active assignments
                active_assignments.append(assignment)
        
        # Update archive metadata
        archive_data["total_archived"] = len(archive_data["assignments"])
        
        # Save updated data
        if newly_archived:
            self.save_assignments(active_assignments)
            self.save_archive(archive_data)
            
            logger.info(f"Archive cleanup completed:")
            logger.info(f"  - Active assignments: {len(active_assignments)}")
            logger.info(f"  - Newly archived: {len(newly_archived)}")
            logger.info(f"  - Total archived: {archive_data['total_archived']}")
        else:
            logger.info("No assignments need archiving")
        
        return {
            "active_count": len(active_assignments),
            "newly_archived_count": len(newly_archived),
            "newly_archived": newly_archived,
            "total_archived": archive_data["total_archived"]
        }
    
    def restore_assignment_from_archive(self, assignment_title: str) -> bool:
        """Restore a specific assignment from archive to active list"""
        
        logger.info(f"Attempting to restore assignment: {assignment_title}")
        
        assignments = self.load_assignments()
        archive_data = self.load_archive()
        
        # Find assignment in archive
        restored_assignment = None
        remaining_archived = []
        
        for archived_item in archive_data["assignments"]:
            if archived_item.get("title") == assignment_title:
                restored_assignment = archived_item["original_data"]
                # Update the status and timestamp
                restored_assignment["status"] = "Pending"  # Default restore status
                restored_assignment["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Found assignment in archive: {assignment_title}")
            else:
                remaining_archived.append(archived_item)
        
        if restored_assignment:
            # Add back to active assignments
            assignments.append(restored_assignment)
            
            # Update archive (remove restored assignment)
            archive_data["assignments"] = remaining_archived
            archive_data["total_archived"] = len(remaining_archived)
            
            # Save updated data
            self.save_assignments(assignments)
            self.save_archive(archive_data)
            
            logger.info(f"Successfully restored assignment: {assignment_title}")
            return True
        else:
            logger.warning(f"Assignment not found in archive: {assignment_title}")
            return False
    
    def smart_status_sync(self, notion_assignments: List[Dict]) -> Dict:
        """Sync status changes from Notion and handle smart restore"""
        
        logger.info("Starting smart status sync with Notion")
        
        local_assignments = self.load_assignments()
        archive_data = self.load_archive()
        
        # Create lookup dictionaries
        local_lookup = {a.get('title', ''): a for a in local_assignments}
        archived_lookup = {a.get('title', ''): a for a in archive_data.get('assignments', [])}
        
        restored_count = 0
        updated_count = 0
        
        for notion_assignment in notion_assignments:
            title = notion_assignment.get('title', '')
            notion_status = notion_assignment.get('status', 'Pending')
            
            # Check if assignment exists in local active list
            if title in local_lookup:
                # Update status if different
                local_assignment = local_lookup[title]
                if local_assignment.get('status') != notion_status:
                    local_assignment['status'] = notion_status
                    local_assignment['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updated_count += 1
                    logger.info(f"Updated status for {title}: {notion_status}")
            
            # Check if assignment needs to be restored from archive
            elif title in archived_lookup and notion_status in ['Pending', 'In Progress']:
                # Restore from archive
                if self.restore_assignment_from_archive(title):
                    restored_count += 1
                    # Update the restored assignment's status
                    updated_assignments = self.load_assignments()
                    for assignment in updated_assignments:
                        if assignment.get('title') == title:
                            assignment['status'] = notion_status
                            assignment['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            break
                    self.save_assignments(updated_assignments)
                    logger.info(f"Restored and updated {title}: {notion_status}")
        
        # Save updated assignments if any changes
        if updated_count > 0:
            self.save_assignments(local_assignments)
        
        return {
            "updated_count": updated_count,
            "restored_count": restored_count,
            "total_active": len(self.load_assignments()),
            "total_archived": len(archive_data.get('assignments', []))
        }
    
    def get_archive_stats(self) -> Dict:
        """Get archive statistics"""
        
        assignments = self.load_assignments()
        archive_data = self.load_archive()
        
        # Count by status
        status_counts = {}
        for assignment in assignments:
            status = assignment.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count archived by reason
        archive_reasons = {}
        for archived in archive_data.get('assignments', []):
            reason = archived.get('archive_reason', 'Unknown')
            archive_reasons[reason] = archive_reasons.get(reason, 0) + 1
        
        return {
            "active_assignments": len(assignments),
            "active_by_status": status_counts,
            "total_archived": archive_data.get('total_archived', 0),
            "archived_by_reason": archive_reasons,
            "last_cleanup": archive_data.get('last_cleanup'),
            "archive_file_size": os.path.getsize(self.archive_file) if os.path.exists(self.archive_file) else 0
        }
    
    def manual_archive_assignment(self, assignment_title: str, reason: str = "manual_request") -> bool:
        """Manually archive a specific assignment"""
        
        assignments = self.load_assignments()
        archive_data = self.load_archive()
        
        # Find and remove assignment from active list
        assignment_to_archive = None
        remaining_assignments = []
        
        for assignment in assignments:
            if assignment.get('title') == assignment_title:
                assignment_to_archive = assignment
            else:
                remaining_assignments.append(assignment)
        
        if assignment_to_archive:
            # Archive the assignment
            archived_assignment = {
                "original_data": assignment_to_archive,
                "archived_date": datetime.now().isoformat(),
                "archive_reason": reason,
                "completion_date": assignment_to_archive.get('last_updated', ''),
                "title": assignment_to_archive.get('title', 'Unknown'),
                "course_code": assignment_to_archive.get('course_code', 'Unknown')
            }
            
            archive_data["assignments"].append(archived_assignment)
            archive_data["total_archived"] = len(archive_data["assignments"])
            
            # Save updated data
            self.save_assignments(remaining_assignments)
            self.save_archive(archive_data)
            
            logger.info(f"Manually archived assignment: {assignment_title}")
            return True
        else:
            logger.warning(f"Assignment not found for manual archiving: {assignment_title}")
            return False
