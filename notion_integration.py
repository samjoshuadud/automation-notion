import requests
import json
import os
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
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Assignment": {
                        "title": [
                            {
                                "text": {
                                    "content": assignment.get('title', 'Unknown Assignment')[:100]  # Notion title limit
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
                logger.info(f"Processing assignment {i}/{len(assignments)}: {assignment.get('title', 'Unknown')}")
                
                # Check if assignment already exists
                if self.check_assignment_exists(assignment):
                    logger.info(f"Assignment already exists in Notion: {assignment.get('title')}")
                    duplicate_count += 1
                    continue
                
                # Create new assignment
                if self.create_assignment_page(assignment):
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing assignment {assignment.get('title', 'Unknown')}: {e}")
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
                assignment_title = assignment.get('title', '').strip().lower()
                
                if not assignment_title:
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
                    
                    if existing_title and existing_title == assignment_title:
                        logger.debug(f"Assignment '{assignment.get('title')}' already exists in Notion")
                        return True
                
                logger.debug(f"Assignment '{assignment.get('title')}' not found in Notion")
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
            
            assignment_title = assignment.get('title', '').strip().lower()
            assignment_due_date = assignment.get('due_date', '').strip()
            
            logger.debug(f"Checking Notion for assignment: '{assignment_title}'")
            
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
                    if existing_title and existing_title == assignment_title:
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
                            logger.debug(f"Assignment '{assignment_title}' exists with matching due date")
                            return True
                        # If only title matches but no due date info, assume it's the same
                        elif not assignment_due_date or not existing_due_date:
                            logger.debug(f"Assignment '{assignment_title}' exists (title match only)")
                            return True
                
                logger.debug(f"Assignment '{assignment_title}' not found in Notion")
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
