import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class TodoistIntegration:
    def __init__(self):
        load_dotenv()
        self.todoist_token = os.getenv('TODOIST_TOKEN')
        
        if not self.todoist_token:
            logger.warning("Todoist credentials not found. Skipping Todoist integration.")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                'Authorization': f'Bearer {self.todoist_token}',
                'Content-Type': 'application/json'
            }
            self.base_url = 'https://api.todoist.com/rest/v2'
            
            # Verify connection on initialization
            try:
                self._test_connection()
                logger.info("Todoist integration initialized successfully")
            except Exception as e:
                logger.error(f"Todoist integration failed to initialize: {e}")
                self.enabled = False
    
    def _test_connection(self) -> bool:
        """Test the Todoist API connection"""
        if not self.enabled:
            return False
            
        try:
            url = f'{self.base_url}/projects'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("Todoist connection test successful")
                return True
            else:
                logger.error(f"Todoist connection test failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Todoist connection error: {e}")
            return False
    
    def calculate_reminder_date(self, assignment: Dict) -> Optional[str]:
        """Calculate smart reminder date based on opening date (if available) or due date"""
        due_date_str = assignment.get('due_date', '')
        opening_date_str = assignment.get('opening_date', '')
        
        if not due_date_str:
            return None
            
        try:
            # Parse due date
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Determine the reference date for reminder calculation
            # Use the later of due date and opening date (if available and valid)
            reference_date = due_date
            reference_type = "due date"

            if opening_date_str and opening_date_str not in [None, 'No opening date']:
                try:
                    opening_date = datetime.strptime(opening_date_str, '%Y-%m-%d').date()
                    # Choose the later of due_date vs opening_date as reference
                    if opening_date > reference_date:
                        reference_date = opening_date
                        reference_type = "opening date"
                        logger.debug(f"Using opening date {opening_date_str} as reference for reminder calculation (later than due date)")
                    else:
                        logger.debug(f"Using due date {due_date_str} as reference (later than or equal to opening date)")
                except ValueError:
                    logger.debug(f"Invalid opening date format: {opening_date_str}, using due date instead")
            
            # Calculate days until reference date
            days_until_reference = (reference_date - today).days
            
            if days_until_reference <= 0:
                # Already due/opened or overdue, set reminder for today
                logger.debug(f"Reference date ({reference_type}) is today or in the past, setting reminder for today")
                return today.strftime('%Y-%m-%d')
            elif reference_type == "opening date":
                # For opening dates, use more intuitive timing
                if days_until_reference <= 1:
                    # Opening today or tomorrow: remind today
                    reminder_days_before = 0
                elif days_until_reference <= 3:
                    # 2-3 days: remind 1 day before
                    reminder_days_before = 1
                elif days_until_reference <= 7:
                    # 4-7 days: remind 2 days before
                    reminder_days_before = 2
                elif days_until_reference <= 14:
                    # 8-14 days: remind 3 days before
                    reminder_days_before = 3
                else:
                    # 15+ days: remind 1 week before opening
                    reminder_days_before = 7
            else:
                # For due dates, use the original logic
                if days_until_reference <= 3:
                    # 1-3 days: remind 1 day before (or today if due tomorrow)
                    reminder_days_before = max(1, days_until_reference - 1)
                elif days_until_reference <= 7:
                    # 4-7 days: remind 3 days before
                    reminder_days_before = 3
                elif days_until_reference <= 14:
                    # 8-14 days: remind 5 days before  
                    reminder_days_before = 5
                elif days_until_reference <= 30:
                    # 15-30 days: remind 1 week before
                    reminder_days_before = 7
                else:
                    # 30+ days: remind 2 weeks before
                    reminder_days_before = 14
            
            # Calculate reminder date
            reminder_date = reference_date - timedelta(days=reminder_days_before)
            
            # Don't set reminder in the past
            if reminder_date < today:
                reminder_date = today
                
            logger.debug(f"Calculated reminder: {reminder_date} ({reminder_days_before} days before {reference_type} {reference_date})")
            return reminder_date.strftime('%Y-%m-%d')
            
        except ValueError as e:
            logger.warning(f"Invalid due date format: {due_date_str}, error: {e}")
            return None
    
    def format_task_content(self, assignment: Dict) -> str:
        """Format task content as: CODE - Activity # (Activity Name)"""
        if not assignment or not isinstance(assignment, dict):
            return "Unknown Assignment - Invalid Data"
            
        title = assignment.get('title', 'Unknown Assignment') or 'Unknown Assignment'
        course_code = assignment.get('course_code', '') or ''
        raw_title = assignment.get('raw_title', '') or ''
        
        # Try to extract activity number and name from raw_title or title
        activity_match = None
        activity_name = ""
        
        # Look for patterns like "ACTIVITY 1 - USER STORY [1]" or "Activity 1 (User Story)"
        if raw_title:
            # Pattern 1: "ACTIVITY # - NAME [#]" 
            pattern1 = re.search(r'ACTIVITY\s+(\d+)\s*-\s*([^[]+)', raw_title, re.IGNORECASE)
            if pattern1:
                activity_num = pattern1.group(1)
                activity_name = pattern1.group(2).strip()
                activity_match = f"Activity {activity_num}"
            else:
                # Pattern 2: Look for just "ACTIVITY #"
                pattern2 = re.search(r'ACTIVITY\s+(\d+)', raw_title, re.IGNORECASE)
                if pattern2:
                    activity_num = pattern2.group(1)
                    activity_match = f"Activity {activity_num}"
                    # Try to get name from the rest
                    remaining = re.sub(r'ACTIVITY\s+\d+\s*-?\s*', '', raw_title, flags=re.IGNORECASE)
                    activity_name = re.sub(r'\[\d+\]', '', remaining).strip()
        
        # If no activity found in raw_title, try the formatted title
        if not activity_match and title:
            # Look for patterns in the formatted title
            title_pattern = re.search(r'Activity\s+(\d+)\s*\(([^)]+)\)', title, re.IGNORECASE)
            if title_pattern:
                activity_num = title_pattern.group(1)
                activity_name = title_pattern.group(2).strip()
                activity_match = f"Activity {activity_num}"
        
        # Build the final format
        if course_code and activity_match:
            if activity_name:
                # Clean up activity name (remove extra chars)
                activity_name = re.sub(r'\s*\[\d+\]', '', activity_name).strip()
                formatted_title = f"{course_code} - {activity_match} ({activity_name})"
            else:
                formatted_title = f"{course_code} - {activity_match}"
        elif course_code:
            # Fallback: use course code with original title
            formatted_title = f"{course_code} - {title}"
        else:
            # Fallback: use original title
            formatted_title = title
            
        return formatted_title
    
    def format_task_description(self, assignment: Dict) -> str:
        """Format task description with deadline and other details"""
        if not assignment or not isinstance(assignment, dict):
            return "Invalid assignment data"
            
        description_parts = []
        
        # Add deadline
        due_date = assignment.get('due_date', '')
        if due_date:
            try:
                # Format the due date nicely
                formatted_date = datetime.strptime(due_date, '%Y-%m-%d').strftime('%B %d, %Y')
                description_parts.append(f"📅 Deadline: {formatted_date}")
            except ValueError:
                description_parts.append(f"📅 Deadline: {due_date}")
        
        # Add course information
        course = assignment.get('course', '')
        if course:
            # Clean up course name (remove line breaks)
            clean_course = re.sub(r'\r?\n', ' ', course).strip()
            description_parts.append(f"📚 Course: {clean_course}")
        
        # Add source information
        source = assignment.get('source', '')
        if source:
            description_parts.append(f"📧 Source: {source}")
        
        # Add task_id for reliable duplicate detection
        task_id = assignment.get('task_id', '')
        if task_id:
            description_parts.append(f"🔗 Task ID: {task_id}")
        
        # Add assignment metadata for tracking
        if assignment.get('course_code'):
            description_parts.append(f"📚 Course: {assignment.get('course_code')}")
        
        if assignment.get('activity_type'):
            description_parts.append(f"🔧 Type: {assignment.get('activity_type')}")
        
        return "\n".join(description_parts)
    
    def get_or_create_project(self, project_name: str = "School Assignments") -> Optional[str]:
        """Get existing project or create new one for assignments"""
        if not self.enabled:
            return None
            
        try:
            # Get all projects
            url = f'{self.base_url}/projects'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                projects = response.json()
                for project in projects:
                    if project['name'] == project_name:
                        logger.info(f"Found existing project: {project_name}")
                        return project['id']
                
                # Project not found, create new one
                create_url = f'{self.base_url}/projects'
                create_data = {
                    'name': project_name,
                    'color': 'blue'
                }
                create_response = requests.post(create_url, headers=self.headers, 
                                              json=create_data, timeout=10)
                
                if create_response.status_code == 200:
                    new_project = create_response.json()
                    logger.info(f"Created new project: {project_name}")
                    return new_project['id']
                else:
                    logger.error(f"Failed to create project: {create_response.status_code} - {create_response.text}")
                    return None
            else:
                logger.error(f"Failed to get projects: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting/creating project: {e}")
            return None
    
    def task_exists_in_todoist(self, assignment: Dict) -> Optional[str]:
        """Check if task already exists in Todoist using task_id for reliable duplicate detection"""
        if not self.enabled:
            return None
            
        try:
            # Get task_id from assignment
            task_id = assignment.get('task_id')
            if not task_id:
                logger.debug(f"No task_id found for assignment: {assignment.get('title', 'Unknown')}")
                return None
            
            # Search for tasks with the same task_id in description
            url = f'{self.base_url}/tasks'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                tasks = response.json()
                
                for task in tasks:
                    task_desc = task.get('description', '').lower()
                    
                    # Check for task_id in description (most reliable)
                    if f"task id: {task_id}" in task_desc:
                        logger.debug(f"Found existing task by task_id: {task['content']} (ID: {task_id})")
                        return task['id']
                        
                logger.debug(f"No existing task found with task_id: {task_id}")
                return None
            else:
                logger.error(f"Failed to get tasks: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking task existence: {e}")
            return None
    
    def create_assignment_task(self, assignment: Dict, project_id: str = None) -> bool:
        """Create a new task in Todoist for the assignment"""
        if not self.enabled:
            return False
            
        # Validate input
        if not assignment or not isinstance(assignment, dict):
            logger.error("Invalid assignment data provided to create_assignment_task")
            return False
            
        try:
            # Get or create project if not provided
            if not project_id:
                project_id = self.get_or_create_project()
                if not project_id:
                    logger.error("Could not get/create Todoist project")
                    return False
            
            # Format task content using the new format
            task_content = self.format_task_content(assignment)
            
            # Format task description with deadline and details
            description = self.format_task_description(assignment)
            
            # Get course code for labels
            course_code = assignment.get('course_code', '')
            
            # Prepare basic task data
            task_data = {
                'content': task_content,
                'description': description,
                'project_id': project_id,
                'priority': 2  # Normal priority (1=lowest, 4=highest)
            }
            
            # Handle due date and reminder
            due_date = assignment.get('due_date', '')
            if due_date:
                try:
                    # Validate due date format
                    datetime.strptime(due_date, '%Y-%m-%d')
                    
                    # Calculate smart reminder date
                    reminder_date = self.calculate_reminder_date(assignment)
                    
                    if reminder_date:
                        # Set reminder date instead of due date
                        task_data['due_date'] = reminder_date
                        logger.debug(f"Set reminder for {reminder_date} (due: {due_date})")
                    else:
                        # Fallback to due date if reminder calculation fails
                        task_data['due_date'] = due_date
                        logger.debug(f"Set due date: {due_date}")
                        
                except ValueError:
                    logger.warning(f"Invalid due date format: {due_date}")
            
            # Add labels for course code if available
            labels = []
            if course_code:
                labels.append(course_code.lower())
            if labels:
                task_data['labels'] = labels
            
            # Create the task
            url = f'{self.base_url}/tasks'
            response = requests.post(url, headers=self.headers, json=task_data, timeout=10)
            
            if response.status_code == 200:
                created_task = response.json()
                logger.info(f"Created Todoist task: {task_content}")
                return True
            else:
                logger.error(f"Failed to create task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating Todoist task: {e}")
            return False
    
    def update_assignment_task(self, assignment: Dict, todoist_task_id: str) -> bool:
        """Update an existing task in Todoist for the assignment"""
        if not self.enabled:
            return False
            
        try:
            # Format task content using the new format
            task_content = self.format_task_content(assignment)
            
            # Format task description with deadline and details
            description = self.format_task_description(assignment)
            
            # Get course code for labels
            course_code = assignment.get('course_code', '')
            
            # Prepare basic task data for update
            task_data = {
                'content': task_content,
                'description': description,
                'priority': 2  # Normal priority (1=lowest, 4=highest)
            }
            
            # Handle due date and reminder
            due_date = assignment.get('due_date', '')
            if due_date:
                try:
                    # Validate due date format
                    datetime.strptime(due_date, '%Y-%m-%d')
                    
                    # Calculate smart reminder date
                    reminder_date = self.calculate_reminder_date(assignment)
                    
                    if reminder_date:
                        # Set reminder date instead of due date
                        task_data['due_date'] = reminder_date
                        logger.debug(f"Set reminder date: {reminder_date} (due: {due_date})")
                    else:
                        # Fallback to due date if reminder calculation fails
                        task_data['due_date'] = due_date
                        logger.debug(f"Set due date: {due_date}")
                        
                except ValueError:
                    logger.warning(f"Invalid due date format: {due_date}")
            
            # Add labels for course code if available
            labels = []
            if course_code:
                labels.append(course_code.lower())
            if labels:
                task_data['labels'] = labels
            
            # Update the task
            url = f'{self.base_url}/tasks/{todoist_task_id}'
            logger.debug(f"Updating task with URL: {url}")
            logger.debug(f"Update data: {task_data}")
            
            response = requests.post(url, headers=self.headers, json=task_data, timeout=10)
            
            logger.debug(f"Update response status: {response.status_code}")
            logger.debug(f"Update response text: {response.text}")
            
            if response.status_code == 200:
                logger.info(f"Updated Todoist task: {task_content}")
                return True
            else:
                logger.error(f"Failed to update task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Todoist task: {e}")
            return False

    def sync_assignments(self, assignments: List[Dict]) -> int:
        """Sync assignments to Todoist, return number of synced assignments"""
        if not self.enabled:
            logger.warning("Todoist integration not enabled")
            return 0
            
        if not assignments:
            logger.info("No assignments to sync to Todoist")
            return 0
            
        # Validate input data
        valid_assignments = []
        for assignment in assignments:
            if isinstance(assignment, dict) and assignment.get('title'):
                valid_assignments.append(assignment)
            else:
                logger.warning(f"Skipping invalid assignment data: {assignment}")
        
        if not valid_assignments:
            logger.warning("No valid assignments found to sync")
            return 0
        
        # Filter out completed assignments and duplicates
        filtered_assignments = []
        for assignment in valid_assignments:
            # Skip completed assignments
            if assignment.get('status') == 'Completed':
                logger.info(f"Skipping completed assignment: {assignment.get('title')}")
                continue
            filtered_assignments.append(assignment)
        
        if len(filtered_assignments) < len(valid_assignments):
            skipped = len(valid_assignments) - len(filtered_assignments)
            logger.info(f"Skipped {skipped} completed assignments")
        
        # Separate assignments into new (to create) and existing (to update)
        assignment_groups = self.prevent_duplicate_sync(filtered_assignments)
        new_assignments = assignment_groups['new']
        existing_assignments = assignment_groups['existing']
        
        if not new_assignments and not existing_assignments:
            logger.info("No assignments to sync after filtering")
            return 0
        
        synced_count = 0
        updated_count = 0
        project_id = self.get_or_create_project()
        
        if not project_id:
            logger.error("Could not get/create Todoist project for assignments")
            return 0
        
        # Handle existing tasks (updates) - only if there are meaningful changes
        for assignment in existing_assignments:
            todoist_task_id = assignment.get('_todoist_task_id')
            if todoist_task_id:
                # Check if there are meaningful changes before updating
                has_changes = self._has_meaningful_changes(assignment, todoist_task_id)
                logger.info(f"Checking changes for '{assignment.get('title', 'Unknown')}': {'CHANGES DETECTED' if has_changes else 'No changes'}")
                
                if has_changes:
                    if self.update_assignment_task(assignment, todoist_task_id):
                        updated_count += 1
                        logger.info(f"Updated existing Todoist task: {assignment.get('title', 'Unknown')}")
                    else:
                        logger.warning(f"Failed to update existing Todoist task: {assignment.get('title', 'Unknown')}")
                else:
                    logger.info(f"No meaningful changes for task: {assignment.get('title', 'Unknown')} - skipping update")
            else:
                logger.warning(f"No Todoist task ID found for assignment: {assignment.get('title', 'Unknown')}")
        
        # Handle new tasks (creations)
        for assignment in new_assignments:
            if self.create_assignment_task(assignment, project_id):
                synced_count += 1
                logger.info(f"Created new Todoist task: {assignment.get('title', 'Unknown')}")
            else:
                logger.warning(f"Failed to create new Todoist task: {assignment.get('title', 'Unknown')}")
            
        total_processed = synced_count + updated_count
        if total_processed > 0:
            if synced_count > 0 and updated_count > 0:
                logger.info(f"✅ Todoist sync completed:")
                logger.info(f"   ➕ {synced_count} new tasks created")
                logger.info(f"   🔄 {updated_count} existing tasks updated")
            elif synced_count > 0:
                logger.info(f"✅ Todoist sync completed: {synced_count} new tasks created")
            elif updated_count > 0:
                logger.info(f"✅ Todoist sync completed: {updated_count} existing tasks updated")
        else:
            logger.info("No tasks were synced to Todoist")
            
        return {
            'total_processed': total_processed,
            'new_created': synced_count,
            'existing_updated': updated_count
        }
    
    def _has_meaningful_changes(self, assignment: Dict, todoist_task_id: str) -> bool:
        """Check if there are meaningful changes between local assignment and Todoist task"""
        try:
            # Get the current Todoist task
            url = f'{self.base_url}/tasks/{todoist_task_id}'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Could not fetch Todoist task {todoist_task_id} for comparison")
                return True  # Assume changes if we can't check
            
            todoist_task = response.json()
            
            # Compare the full formatted title (course code + title) to match Todoist format
            # Check if title already starts with course code to avoid duplication
            local_title = assignment.get('title', '').lower().strip()
            course_code = assignment.get('course_code', '').lower().strip()
            
            if local_title.startswith(course_code + ' - '):
                # Title already includes course code
                local_full_title = local_title
            else:
                # Add course code prefix
                local_full_title = (course_code + ' - ' + local_title).strip()
            
            todoist_title = todoist_task.get('content', '').lower().strip()
            
            logger.info(f"  Comparing full titles:")
            logger.info(f"    Local:  '{local_full_title}'")
            logger.info(f"    Todoist: '{todoist_title}'")
            logger.info(f"    Match: {local_full_title == todoist_title}")
            
            # If titles differ, we should update
            if local_full_title != todoist_title:
                logger.info(f"  Title change detected: '{todoist_title}' → '{local_full_title}'")
                return True

            # Check due/reminder date change as well
            current_due_in_todoist = None
            try:
                current_due_in_todoist = todoist_task.get('due', {}).get('date') if todoist_task.get('due') else None
            except Exception:
                current_due_in_todoist = None

            # Compute expected reminder date using our logic
            expected_reminder_date = self.calculate_reminder_date(assignment)
            expected_due_to_set = expected_reminder_date or assignment.get('due_date')

            logger.info(f"  Comparing due/reminder dates:")
            logger.info(f"    Current in Todoist: {current_due_in_todoist}")
            logger.info(f"    Expected (local):  {expected_due_to_set}")

            if expected_due_to_set and expected_due_to_set != current_due_in_todoist:
                logger.info(f"  Due/reminder date change detected → update required")
                return True

            # No meaningful changes detected
            logger.info(f"  No changes detected - titles and due/reminder date match")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for meaningful changes: {e}")
            return True  # Assume changes if we can't check
    
    def get_all_assignments_from_todoist(self, project_name: str = "School Assignments") -> List[Dict]:
        """Get all assignments from Todoist project with status information"""
        if not self.enabled:
            return []
            
        try:
            # Get project ID
            project_id = self.get_or_create_project(project_name)
            if not project_id:
                return []
            
            # Get tasks from the project
            url = f'{self.base_url}/tasks'
            params = {'project_id': project_id}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                tasks = response.json()
                assignments = []
                
                for task in tasks:
                    # Extract task_id from description for matching
                    task_id = None
                    description = task.get('description', '')
                    
                    # Extract task_id (primary identifier)
                    task_id_match = re.search(r'🔗 Task ID: (\w+)', description)
                    if task_id_match:
                        task_id = task_id_match.group(1)
                    
                    assignment = {
                        'id': task['id'],
                        'title': task['content'],
                        'completed': task['is_completed'],
                        'due_date': task.get('due', {}).get('date') if task.get('due') else None,
                        'priority': task.get('priority', 1),
                        'labels': task.get('labels', []),
                        'description': description,
                        'created_at': task.get('created_at'),
                        'url': task.get('url'),
                        'task_id': task_id  # Primary identifier for matching
                    }
                    assignments.append(assignment)
                
                logger.info(f"Retrieved {len(assignments)} assignments from Todoist")
                return assignments
            else:
                logger.error(f"Failed to get tasks from Todoist: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting assignments from Todoist: {e}")
            return []
    
    def get_school_assignments(self) -> List[Dict]:
        """Alias for get_all_assignments_from_todoist for interactive deletion"""
        return self.get_all_assignments_from_todoist()
    
    def sync_status_from_todoist(self, local_assignments: List[Dict]) -> Dict:
        """Sync completion status from Todoist back to local storage"""
        if not self.enabled:
            return {'updated': 0, 'completed_in_todoist': []}
            
        # Validate input
        if not local_assignments or not isinstance(local_assignments, list):
            logger.warning("Invalid local assignments data for status sync")
            return {'updated': 0, 'completed_in_todoist': []}
        
        # Filter valid assignments
        valid_assignments = []
        for assignment in local_assignments:
            if isinstance(assignment, dict) and assignment.get('title'):
                valid_assignments.append(assignment)
        
        if not valid_assignments:
            logger.info("No valid assignments for status sync")
            return {'updated': 0, 'completed_in_todoist': []}
            
        try:
            # Get all assignments from Todoist
            todoist_assignments = self.get_all_assignments_from_todoist()
            if not todoist_assignments:
                logger.info("No assignments found in Todoist for status sync")
                return {'updated': 0, 'completed_in_todoist': []}
            
            # Create lookup dictionary for Todoist assignments using task_id
            todoist_lookup = {}
            for task in todoist_assignments:
                task_id = task.get('task_id')
                if task_id:
                    todoist_lookup[task_id] = task
                    logger.debug(f"Indexed Todoist task by task_id: {task_id}")
            
            updated_count = 0
            completed_assignments = []
            
            # Check each local assignment against Todoist
            for assignment in valid_assignments:
                task_id = assignment.get('task_id', '')
                
                # Try to find matching Todoist task by task_id
                todoist_task = None
                if task_id and task_id in todoist_lookup:
                    todoist_task = todoist_lookup[task_id]
                    logger.debug(f"Found Todoist task by task_id: {task_id}")
                
                if todoist_task and todoist_task['completed']:
                    # Task is completed in Todoist, update local status
                    if assignment.get('status') != 'Completed':
                        assignment['status'] = 'Completed'
                        assignment['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated_count += 1
                        completed_assignments.append(assignment['title'])
                        logger.info(f"Updated status to Completed: {assignment['title']} (task_id: {task_id})")
            
            return {
                'updated': updated_count,
                'completed_in_todoist': completed_assignments
            }
            
        except Exception as e:
            logger.error(f"Error syncing status from Todoist: {e}")
            return {'updated': 0, 'completed_in_todoist': []}
    
    def prevent_duplicate_sync(self, assignments_to_sync: List[Dict]) -> Dict[str, List[Dict]]:
        """Separate assignments into new (to create) and existing (to update)"""
        if not self.enabled:
            return {'new': assignments_to_sync, 'existing': []}
            
        try:
            # Get ALL existing tasks from Todoist (both active and completed)
            todoist_assignments = self.get_all_assignments_from_todoist()
            
            if not todoist_assignments:
                return {'new': assignments_to_sync, 'existing': []}
            
            # Create lookup for existing tasks using task_id and their Todoist IDs
            existing_lookup = {}
            for task in todoist_assignments:
                # Extract task_id from description
                task_desc = task.get('description', '').lower()
                task_id_match = re.search(r'task id: (\w+)', task_desc)
                if task_id_match:
                    task_id = task_id_match.group(1)
                    existing_lookup[task_id] = task['id']  # Store Todoist task ID
                    logger.debug(f"Added existing task_id to lookup: {task_id} -> Todoist ID: {task['id']}")
            
            # Separate assignments into new and existing
            new_assignments = []
            existing_assignments = []
            
            for assignment in assignments_to_sync:
                task_id = assignment.get('task_id', '')
                
                if task_id and task_id in existing_lookup:
                    # Task exists in Todoist - mark for update
                    todoist_task_id = existing_lookup[task_id]
                    assignment['_todoist_task_id'] = todoist_task_id  # Store Todoist ID for update
                    existing_assignments.append(assignment)
                    logger.debug(f"Marked existing task for update: {assignment.get('title')} (task_id: {task_id}, Todoist ID: {todoist_task_id})")
                else:
                    # New task - mark for creation
                    new_assignments.append(assignment)
                    logger.debug(f"Marked new task for creation: {assignment.get('title')} (task_id: {task_id})")
            
            logger.info(f"Separated assignments: {len(new_assignments)} new, {len(existing_assignments)} existing")
            return {'new': new_assignments, 'existing': existing_assignments}
            
        except Exception as e:
            logger.error(f"Error separating assignments: {e}")
            return {'new': assignments_to_sync, 'existing': []}
    
    def update_task_status(self, task_id: str, completed: bool) -> bool:
        """Update task completion status"""
        if not self.enabled:
            return False
            
        try:
            if completed:
                url = f'{self.base_url}/tasks/{task_id}/close'
                response = requests.post(url, headers=self.headers, timeout=10)
            else:
                url = f'{self.base_url}/tasks/{task_id}/reopen'
                response = requests.post(url, headers=self.headers, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Updated task {task_id} status to {'completed' if completed else 'active'}")
                return True
            else:
                logger.error(f"Failed to update task status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task from Todoist"""
        if not self.enabled:
            return False
            
        try:
            url = f'{self.base_url}/tasks/{task_id}'
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Deleted task {task_id} from Todoist")
                return True
            else:
                logger.error(f"Failed to delete task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    def create_project_if_not_exists(self, project_name: str, color: str = 'blue') -> Optional[str]:
        """Create a project if it doesn't exist, return project ID"""
        return self.get_or_create_project(project_name)
    
    def get_project_stats(self, project_name: str = "School Assignments") -> Dict:
        """Get statistics for the assignments project"""
        if not self.enabled:
            return {}
            
        try:
            assignments = self.get_all_assignments_from_todoist(project_name)
            
            stats = {
                'total_tasks': len(assignments),
                'completed_tasks': len([a for a in assignments if a['completed']]),
                'pending_tasks': len([a for a in assignments if not a['completed']]),
                'overdue_tasks': 0,
                'due_today': 0,
                'due_this_week': 0
            }
            
            today = datetime.now().date()
            week_from_now = today + timedelta(days=7)
            
            for assignment in assignments:
                if assignment['due_date'] and not assignment['completed']:
                    try:
                        due_date = datetime.strptime(assignment['due_date'], '%Y-%m-%d').date()
                        if due_date < today:
                            stats['overdue_tasks'] += 1
                        elif due_date == today:
                            stats['due_today'] += 1
                        elif due_date <= week_from_now:
                            stats['due_this_week'] += 1
                    except ValueError:
                        continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting project stats: {e}")
            return {}
    
    def delete_assignment_task(self, assignment: Dict) -> bool:
        """
        Delete a specific assignment task from Todoist
        
        Args:
            assignment: Assignment dictionary with title and other details
            
        Returns:
            bool: True if task was found and deleted, False otherwise
        """
        if not self.enabled:
            logger.warning("Todoist integration not enabled")
            return False
        
        try:
            # Find the task by searching for it
            task_id = self._find_task_by_assignment(assignment)
            
            if not task_id:
                logger.debug(f"Task not found in Todoist for assignment: {assignment.get('title', 'Unknown')}")
                return False
            
            # Delete the task
            url = f'{self.base_url}/tasks/{task_id}'
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            if response.status_code == 204:  # Todoist returns 204 for successful deletion
                logger.info(f"Successfully deleted task from Todoist: {assignment.get('title', 'Unknown')}")
                return True
            else:
                logger.error(f"Failed to delete task from Todoist: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting task from Todoist: {e}")
            return False
    
    def _find_task_by_assignment(self, assignment: Dict) -> Optional[str]:
        """
        Find a Todoist task ID by assignment details
        
        Args:
            assignment: Assignment dictionary
            
        Returns:
            str or None: Task ID if found, None otherwise
        """
        try:
            # Get all tasks from the assignments project (use same project as creation)
            project_id = self.get_or_create_project()
            url = f'{self.base_url}/tasks'
            params = {'project_id': project_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to get tasks: {response.status_code}")
                return None
            
            tasks = response.json()
            
            # Use the same formatting logic as task creation for comparison
            expected_task_title = self.format_task_content(assignment)
            
            logger.debug(f"Looking for task with title: '{expected_task_title}'")
            
            # Search for task by formatted title match
            for task in tasks:
                task_title = task.get('content', '').strip()
                
                logger.debug(f"Comparing with task: '{task_title}'")
                
                # Exact match with formatted title
                if task_title.lower() == expected_task_title.lower():
                    logger.debug(f"Found exact match: {task['id']}")
                    return task['id']
                
                # Fallback: Check if task title contains the course code and activity pattern
                course_code = assignment.get('course_code', '').upper()
                if course_code and course_code in task_title.upper():
                    # Additional fuzzy matching for activity numbers
                    import re
                    original_activity = re.search(r'Activity\s+(\d+)', expected_task_title, re.IGNORECASE)
                    task_activity = re.search(r'Activity\s+(\d+)', task_title, re.IGNORECASE)
                    
                    if original_activity and task_activity and original_activity.group(1) == task_activity.group(1):
                        logger.debug(f"Found activity number match: {task['id']}")
                        return task['id']
            
            logger.debug("No matching task found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding task: {e}")
            return None
