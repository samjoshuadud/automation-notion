import requests
import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NotionIntegration:
    def __init__(self):
        load_dotenv()
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.notion_token or not self.database_id:
            logger.warning("Notion credentials not found. Skipping Notion integration.")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                'Authorization': f'Bearer {self.notion_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            # Verify connection on initialization
            try:
                self._test_connection()
                logger.info("Notion integration initialized successfully")
            except Exception as e:
                logger.error(f"Notion integration failed to initialize: {e}")
                self.enabled = False
    
    def _test_connection(self) -> bool:
        """Test the Notion API connection"""
        if not self.enabled:
            return False
            
        try:
            url = f'https://api.notion.com/v1/databases/{self.database_id}'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Notion connection test failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error testing Notion connection: {e}")
            return False
    
    def format_task_content(self, assignment: Dict) -> str:
        """Format task content as: CODE - Activity # (Activity Name) - same as Todoist"""
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
    
    def create_assignment_page(self, assignment: Dict) -> bool:
        """Create a new page in Notion database for the assignment with reminder"""
        if not self.enabled:
            logger.warning("Notion integration not enabled")
            return False
        
        try:
            url = 'https://api.notion.com/v1/pages'
            
            # Parse due date for reminder calculation
            due_date_str = assignment.get('due_date')
            reminder_date = None
            
            if due_date_str and due_date_str != 'No due date':
                try:
                    # Try to parse the due date
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    # Set reminder 3 days before
                    reminder_date = (due_date - timedelta(days=3)).strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse due date for reminder: {due_date_str}")
            
            # Prepare the page data with enhanced properties
            formatted_title = self.format_task_content(assignment)
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Assignment": {
                        "title": [
                            {
                                "text": {
                                    "content": formatted_title[:100]  # Notion title limit
                                }
                            }
                        ]
                    },
                    "Course": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": assignment.get('course', 'Unknown Course')
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": assignment.get('status', 'Pending')
                        }
                    },
                    "Source": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": assignment.get('source', 'email')
                                }
                            }
                        ]
                    }
                }
            }
            
            # Add due date if available
            if due_date_str and due_date_str != 'No due date':
                try:
                    # Validate date format for Notion
                    datetime.strptime(due_date_str, '%Y-%m-%d')
                    page_data["properties"]["Due Date"] = {
                        "date": {
                            "start": due_date_str
                        }
                    }
                except ValueError:
                    # Fallback to rich text if date parsing fails
                    page_data["properties"]["Due Date"] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": due_date_str
                                }
                            }
                        ]
                    }
            else:
                page_data["properties"]["Due Date"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": "No due date"
                            }
                        }
                    ]
                }
            
            # Add reminder date if calculated
            if reminder_date:
                page_data["properties"]["Reminder Date"] = {
                    "date": {
                        "start": reminder_date
                    }
                }
            
            # Add course code if available
            if assignment.get('course_code'):
                page_data["properties"]["Course Code"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": assignment.get('course_code')
                            }
                        }
                    ]
                }
            
            # Make the API request with timeout and retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(url, headers=self.headers, json=page_data, timeout=30)
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully added assignment to Notion: {assignment['title']}")
                        return True
                    elif response.status_code == 400:
                        logger.error(f"Bad request to Notion API: {response.text}")
                        # Try to parse error and fix if possible
                        error_data = response.json() if response.text else {}
                        if 'message' in error_data:
                            logger.error(f"Notion API error: {error_data['message']}")
                        return False
                    elif response.status_code == 401:
                        logger.error("Notion API authentication failed. Check your token.")
                        self.enabled = False
                        return False
                    elif response.status_code == 404:
                        logger.error("Notion database not found. Check your database ID.")
                        return False
                    else:
                        logger.warning(f"Notion API returned {response.status_code}: {response.text}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying... (attempt {attempt + 2}/{max_retries})")
                            continue
                        return False
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Notion API timeout (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    return False
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Notion API connection error (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error calling Notion API: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating assignment page in Notion: {e}")
            return False
    
    def sync_assignments(self, assignments: List[Dict]) -> int:
        """Sync all assignments to Notion with duplicate checking"""
        if not self.enabled:
            logger.info("Notion integration not enabled")
            return 0
        
        if not assignments:
            logger.info("No assignments to sync")
            return 0
        
        success_count = 0
        duplicate_count = 0
        error_count = 0
        
        logger.info(f"Starting sync of {len(assignments)} assignments to Notion")
        
        for i, assignment in enumerate(assignments, 1):
            try:
                formatted_title = self.format_task_content(assignment)
                logger.info(f"Processing assignment {i}/{len(assignments)}: {formatted_title}")
                
                # Check if assignment already exists
                if self.check_assignment_exists(assignment):
                    logger.info(f"Assignment already exists in Notion: {formatted_title}")
                    duplicate_count += 1
                    continue
                
                # Create new assignment
                if self.create_assignment_page(assignment):
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                formatted_title = self.format_task_content(assignment) if assignment else "Unknown"
                logger.error(f"Error processing assignment {formatted_title}: {e}")
                error_count += 1
        
        logger.info(f"Notion sync completed: {success_count} created, {duplicate_count} duplicates, {error_count} errors")
        return success_count
    
    def check_assignment_exists(self, assignment: Dict) -> bool:
        """Check if assignment already exists in Notion database"""
        if not self.enabled:
            return False
        
        try:
            url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
            
            # Get all entries since we can't rely on specific property names yet
            query_data = {
                "page_size": 100
            }
            
            response = requests.post(url, headers=self.headers, json=query_data, timeout=15)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                formatted_title = self.format_task_content(assignment).strip().lower()
                
                if not formatted_title:
                    return False
                
                # Check each result for a matching title
                for result in results:
                    properties = result.get('properties', {})
                    
                    # Try different possible title property names
                    existing_title = None
                    for title_prop in ['Assignment', 'Task name', 'Title', 'Name']:
                        if title_prop in properties:
                            title_data = properties[title_prop]
                            if title_data.get('type') == 'title':
                                title_array = title_data.get('title', [])
                                if title_array:
                                    existing_title = title_array[0].get('plain_text', '').strip().lower()
                                    break
                    
                    # Compare using the same 100-char truncation as creation
                    if existing_title and existing_title == formatted_title[:100].strip().lower():
                        logger.debug(f"Assignment '{formatted_title}' already exists in Notion")
                        return True
                
                logger.debug(f"Assignment '{formatted_title}' not found in Notion")
                return False
            else:
                logger.warning(f"Could not check for existing assignments: {response.status_code}")
                # If we can't check, assume it doesn't exist to avoid missing assignments
                return False
                
        except Exception as e:
            logger.warning(f"Error checking for existing assignment: {e}")
            # If we can't check, assume it doesn't exist to avoid missing assignments
            return False
    
    def assignment_exists_in_notion(self, assignment: Dict) -> bool:
        """
        Check if a specific assignment exists in Notion database
        This is a more robust version of check_assignment_exists with better error handling
        """
        if not self.enabled:
            logger.debug("Notion integration not enabled")
            return False
        
        if not assignment or not assignment.get('title'):
            logger.warning("Invalid assignment data provided")
            return False
        
        try:
            url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
            
            formatted_title = self.format_task_content(assignment).strip().lower()
            assignment_due_date = assignment.get('due_date', '').strip()
            
            logger.debug(f"Checking Notion for assignment: '{formatted_title}'")
            
            # Get all entries to check against
            query_data = {
                "page_size": 100
            }
            
            response = requests.post(url, headers=self.headers, json=query_data, timeout=15)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                logger.debug(f"Found {len(results)} entries in Notion database")
                
                # Check each result for a matching assignment
                for result in results:
                    properties = result.get('properties', {})
                    
                    # Try to find title in various property names
                    existing_title = None
                    for title_prop in ['Assignment', 'Task name', 'Title', 'Name']:
                        if title_prop in properties:
                            title_data = properties[title_prop]
                            if title_data.get('type') == 'title':
                                title_array = title_data.get('title', [])
                                if title_array:
                                    existing_title = title_array[0].get('plain_text', '').strip().lower()
                                    break
                    
                    # If we found a matching title, check due date for extra confirmation
                    # Compare using the same 100-char truncation as creation
                    if existing_title and existing_title == formatted_title[:100].strip().lower():
                        logger.debug(f"Found matching title: '{existing_title}'")
                        
                        # Try to get due date for extra verification
                        existing_due_date = None
                        for date_prop in ['Due Date', 'Due', 'Date']:
                            if date_prop in properties:
                                date_data = properties[date_prop]
                                if date_data.get('type') == 'date':
                                    date_value = date_data.get('date')
                                    if date_value:
                                        existing_due_date = date_value.get('start', '').strip()
                                        break
                        
                        # If both title and due date match, it's definitely the same assignment
                        if assignment_due_date and existing_due_date and assignment_due_date == existing_due_date:
                            logger.debug(f"Assignment '{formatted_title}' exists with matching due date")
                            return True
                        # If only title matches but no due date info, assume it's the same
                        elif not assignment_due_date or not existing_due_date:
                            logger.debug(f"Assignment '{formatted_title}' exists (title match only)")
                            return True
                
                logger.debug(f"Assignment '{formatted_title}' not found in Notion")
                return False
                
            elif response.status_code == 404:
                logger.error("Notion database not found or integration not shared with database")
                return False
            else:
                logger.warning(f"Could not check Notion database: {response.status_code} - {response.text}")
                # If we can't check due to API issues, assume it doesn't exist
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("Notion API request timed out")
            return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Notion API request failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking Notion: {e}")
            return False

    def get_all_assignments_from_notion(self) -> List[Dict]:
        """Get all assignments from Notion database for status syncing"""
        if not self.enabled:
            return []
        try:
            url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
            all_assignments = []
            has_more = True
            start_cursor = None
            while has_more:
                payload = {'page_size': 100}
                if start_cursor:
                    payload['start_cursor'] = start_cursor
                response = requests.post(url, headers=self.headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    for page in results:
                        try:
                            properties = page.get('properties', {})
                            # Extract title
                            title = ""
                            for title_prop in ['Assignment', 'Title', 'Name']:
                                if title_prop in properties:
                                    title_data = properties[title_prop]
                                    if title_data.get('type') == 'title':
                                        title_array = title_data.get('title', [])
                                        if title_array:
                                            title = title_array[0].get('plain_text', '').strip()
                                            break
                            # Extract status
                            status = "Pending"  # default
                            for status_prop in ['Status', 'State']:
                                if status_prop in properties:
                                    status_data = properties[status_prop]
                                    if status_data.get('type') == 'select':
                                        select_data = status_data.get('select')
                                        if select_data:
                                            status = select_data.get('name', 'Pending')
                                            break
                            # Extract due date
                            due_date = ""
                            for date_prop in ['Due Date', 'Due', 'Date']:
                                if date_prop in properties:
                                    date_data = properties[date_prop]
                                    if date_data.get('type') == 'date':
                                        date_value = date_data.get('date')
                                        if date_value:
                                            due_date = date_value.get('start', '').strip()
                                            break
                            # Extract course code
                            course_code = ""
                            for course_prop in ['Course Code', 'Course', 'Subject']:
                                if course_prop in properties:
                                    course_data = properties[course_prop]
                                    if course_data.get('type') == 'rich_text':
                                        text_array = course_data.get('rich_text', [])
                                        if text_array:
                                            course_code = text_array[0].get('plain_text', '').strip()
                                            break
                            if title:  # Only add if we have a title
                                assignment = {
                                    'title': title,
                                    'status': status,
                                    'due_date': due_date,
                                    'course_code': course_code,
                                    'notion_id': page.get('id', '')
                                }
                                all_assignments.append(assignment)
                        except Exception as e:
                            logger.warning(f"Error parsing Notion page: {e}")
                            continue
                    has_more = data.get('has_more', False)
                    start_cursor = data.get('next_cursor')
                else:
                    logger.error(f"Failed to fetch assignments from Notion: {response.status_code} - {response.text}")
                    break
            logger.info(f"Retrieved {len(all_assignments)} assignments from Notion")
            return all_assignments
        except requests.exceptions.Timeout:
            logger.warning("Notion API request timed out while fetching all assignments")
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"Notion API request failed while fetching all assignments: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching assignments from Notion: {e}")
            return []
    
    def delete_assignment_page(self, assignment: Dict) -> bool:
        """
        Delete a specific assignment page from Notion database
        
        Args:
            assignment: Assignment dictionary with title and other details
            
        Returns:
            bool: True if page was found and deleted, False otherwise
        """
        if not self.enabled:
            logger.warning("Notion integration not enabled")
            return False
        
        try:
            # Find the page by assignment details
            page_id = self._find_page_by_assignment(assignment)
            formatted_title = self.format_task_content(assignment)
            
            if not page_id:
                logger.debug(f"Page not found in Notion for assignment: {formatted_title}")
                return False
            
            # Archive (delete) the page - Notion doesn't actually delete, but archives
            url = f'https://api.notion.com/v1/pages/{page_id}'
            data = {
                "archived": True
            }
            
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully archived page in Notion: {formatted_title}")
                return True
            else:
                logger.error(f"Failed to archive page in Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting page from Notion: {e}")
            return False
    
    def _find_page_by_assignment(self, assignment: Dict) -> Optional[str]:
        """
        Find a Notion page ID by assignment details
        
        Args:
            assignment: Assignment dictionary
            
        Returns:
            str or None: Page ID if found, None otherwise
        """
        try:
            # Search for the assignment by formatted title and email_id (same as creation)
            formatted_title = self.format_task_content(assignment)
            assignment_email_id = assignment.get('email_id', '').strip()
            
            # First try to search by email_id if available (most reliable)
            if assignment_email_id:
                url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
                data = {
                    "filter": {
                        "property": "Email ID",
                        "rich_text": {
                            "equals": assignment_email_id
                        }
                    }
                }
                
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    results = response.json().get('results', [])
                    if results:
                        return results[0]['id']
            
            # If email_id search didn't work, try formatted title search
            if formatted_title:
                url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
                data = {
                    "filter": {
                        "property": "Assignment",  # Title property in Notion (matches creation)
                        "title": {
                            "contains": formatted_title
                        }
                    }
                }
                
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    results = response.json().get('results', [])
                    
                    # Look for exact or close match
                    for result in results:
                        try:
                            title_prop = result.get('properties', {}).get('Assignment', {})  # Use 'Assignment' property
                            if title_prop.get('type') == 'title':
                                page_title = ''
                                for title_part in title_prop.get('title', []):
                                    page_title += title_part.get('text', {}).get('content', '')
                                
                                # Check for exact or close match (using truncated title like creation)
                                stored_title = formatted_title[:100]  # Match the 100 char limit from creation
                                if page_title.strip().lower() == stored_title.strip().lower():
                                    return result['id']
                        except Exception:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding page: {e}")
            return None
