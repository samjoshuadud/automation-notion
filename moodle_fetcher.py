import imaplib
import email
import re
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoodleEmailFetcher:
    def __init__(self):
        load_dotenv()
        self.gmail_email = os.getenv('GMAIL_EMAIL')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        self.school_domain = os.getenv('SCHOOL_DOMAIN', 'YOURSCHOOL.edu')
        
        if not self.gmail_email or not self.gmail_password:
            raise ValueError("Gmail credentials not found. Please check your .env file.")
        
        # File paths
        self.json_file = 'assignments.json'
        self.md_file = 'assignments.md'
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON and Markdown files if they don't exist"""
        if not os.path.exists(self.json_file):
            with open(self.json_file, 'w') as f:
                json.dump([], f, indent=2)
        
        if not os.path.exists(self.md_file):
            with open(self.md_file, 'w') as f:
                f.write("# Moodle Assignments\n\n")
                f.write("| Assignment | Due Date | Course | Status | Added Date |\n")
                f.write("|------------|----------|--------|--------|-----------|\n")
    
    def connect_to_gmail(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail using IMAP"""
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_email, self.gmail_password)
            logger.info("Successfully connected to Gmail")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            raise
    
    def search_moodle_emails(self, mail: imaplib.IMAP4_SSL, days_back: int = 7) -> List[bytes]:
        """Search for Moodle emails from the past few days"""
        mail.select('inbox')
        
        # Calculate date range
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        
        # Search criteria for Moodle emails
        search_criteria = f'(FROM "noreply@moodle.{self.school_domain}" SINCE "{since_date}")'
        
        try:
            status, message_ids = mail.search(None, search_criteria)
            if status == 'OK':
                email_ids = message_ids[0].split()
                logger.info(f"Found {len(email_ids)} Moodle emails")
                return email_ids
            else:
                logger.warning("No emails found matching criteria")
                return []
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    def parse_email_content(self, mail: imaplib.IMAP4_SSL, email_id: bytes) -> Optional[Dict]:
        """Parse email content to extract assignment information"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                return None
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract subject and body
            subject = email_message['Subject'] or ""
            body = self._get_email_body(email_message)
            
            # Parse assignment info using regex
            assignment_info = self._extract_assignment_info(subject, body)
            
            if assignment_info:
                # Add email metadata
                assignment_info['email_date'] = email_message['Date']
                assignment_info['added_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            return assignment_info
            
        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {e}")
            return None
    
    def _get_email_body(self, email_message) -> str:
        """Extract text body from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body += str(part.get_payload())
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())
        
        return body
    
    def _extract_assignment_info(self, subject: str, body: str) -> Optional[Dict]:
        """Extract assignment information using regex patterns"""
        
        # Enhanced regex patterns based on the email example
        patterns = {
            'assignment_submission': {
                'title_patterns': [
                    # Based on email example: "Assignment ACTIVITY 1 - USER STORY has been changed"
                    r'Assignment\s+([A-Z]+\s+\d+\s*-\s*[^h]+?)\s+has been\s+(?:changed|created|updated)',
                    r'Assignment\s+(.+?)\s+has been\s+(?:changed|created|updated)',
                    r'Assignment\s+(.+?)\s+(?:is|has)',
                    r'Assignment:\s*(.+?)(?:\s+has|\s+is|\n|$)',
                    r'Assignment\s+"(.+?)"\s+has been',
                    r'Assignment submission:\s*(.+?)\s*\(',
                    r'New assignment:\s*(.+?)(?:\n|$)',
                    r'Assignment\s*-\s*(.+?)(?:\n|$)'
                ],
                'due_patterns': [
                    # Multiple date formats from email body
                    r'Due:\s*([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'Due date:\s*([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'due\s+on\s+([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'Deadline:\s*([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'due\s+([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    # Specific pattern for "Friday, 5 September 2025, 10:09 AM"
                    r'(?:Due:|due)\s*([A-Za-z]+,\s*\d+\s+[A-Za-z]+\s+\d{4},?\s*\d{1,2}:\d{2}\s*[AP]M)',
                    r'([A-Za-z]+,\s*\d+\s+[A-Za-z]+\s+\d{4},?\s*\d{1,2}:\d{2}\s*[AP]M)'
                ],
                'course_patterns': [
                    # Based on course code pattern: "HCI - HUMAN COMPUTER INTERACTION (III-ACSAD)"
                    r'course\s+([A-Z]{2,5}\s*-\s*[^(]+(?:\([^)]+\))?)',
                    r'in\s+course\s+([A-Z]{2,5}\s*-\s*[^(]+(?:\([^)]+\))?)',
                    r'([A-Z]{2,5}\s*-\s*[A-Z\s]+(?:\([^)]+\))?)',
                    r'Course:\s*(.+?)(?:\n|$)',
                    r'in\s+course\s+(.+?)(?:\n|$)',
                    r'from\s+(.+?)\s+course'
                ]
            },
            'assignment_reminder': {
                'title_patterns': [
                    r'Reminder:\s*(.+?)\s+assignment',
                    r'Assignment\s+reminder:\s*(.+?)(?:\n|$)',
                    r'Upcoming\s+assignment:\s*(.+?)(?:\n|$)'
                ],
                'due_patterns': [
                    r'due\s+on\s+([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'Due:\s*([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)',
                    r'deadline\s+([^,\n]+(?:,\s*\d+\s*\w+\s*\d{4}[^,\n]*)?)'
                ]
            }
        }
        
        # Try to extract information with fallbacks
        assignment_title = None
        due_date = None
        course_name = None
        course_code = None
        
        full_text = f"{subject}\n{body}"
        
        try:
            # Extract assignment title with multiple fallbacks
            for pattern_type in patterns.values():
                for pattern in pattern_type.get('title_patterns', []):
                    try:
                        match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            assignment_title = match.group(1).strip()
                            # Clean up the title
                            assignment_title = re.sub(r'\s+', ' ', assignment_title)
                            break
                    except Exception as e:
                        logger.warning(f"Error in title pattern matching: {e}")
                        continue
                if assignment_title:
                    break
            
            # Fallback for title extraction
            if not assignment_title:
                # Try simple subject parsing
                subject_patterns = [
                    r'Assignment\s+(.+?)(?:\s+has|\s+is|$)',
                    r'(.+?)\s+has been changed',
                    r'(.+?)\s+assignment'
                ]
                for pattern in subject_patterns:
                    try:
                        match = re.search(pattern, subject, re.IGNORECASE)
                        if match:
                            assignment_title = match.group(1).strip()
                            break
                    except Exception as e:
                        logger.warning(f"Error in fallback title pattern: {e}")
                        continue
            
            # Extract due date with multiple fallbacks
            for pattern_type in patterns.values():
                for pattern in pattern_type.get('due_patterns', []):
                    try:
                        match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            due_date_raw = match.group(1).strip()
                            due_date = self._parse_date(due_date_raw)
                            if due_date and due_date != due_date_raw:  # Successfully parsed
                                break
                    except Exception as e:
                        logger.warning(f"Error in due date pattern matching: {e}")
                        continue
                if due_date:
                    break
            
            # Extract course name and code
            for pattern_type in patterns.values():
                for pattern in pattern_type.get('course_patterns', []):
                    try:
                        match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                        if match:
                            course_name = match.group(1).strip()
                            # Extract course code from course name
                            course_code_match = re.search(r'^([A-Z]{2,5})', course_name)
                            if course_code_match:
                                course_code = course_code_match.group(1).upper()
                            break
                    except Exception as e:
                        logger.warning(f"Error in course pattern matching: {e}")
                        continue
                if course_name:
                    break
            
            # Format the title according to requirements: coursecode - activity no. (name)
            formatted_title = self._format_assignment_title(assignment_title, course_code)
            
            # Apply fallbacks if extraction failed
            if not formatted_title:
                formatted_title = assignment_title or "Unknown Assignment"
            
            if not due_date:
                due_date = "No due date"
                
            if not course_name:
                course_name = "Unknown Course"
            
            # If we found at least a title, return the info
            if assignment_title or formatted_title != "Unknown Assignment":
                return {
                    'title': formatted_title,
                    'due_date': due_date,
                    'course': course_name,
                    'course_code': course_code,
                    'status': 'Pending',
                    'source': 'email',
                    'raw_title': assignment_title  # Keep original for debugging
                }
        
        except Exception as e:
            logger.error(f"Error extracting assignment info: {e}")
            # Return basic info if available
            if assignment_title:
                return {
                    'title': assignment_title,
                    'due_date': "No due date",
                    'course': "Unknown Course",
                    'status': 'Pending',
                    'source': 'email'
                }
        
        return None
    
    def _format_assignment_title(self, title: str, course_code: str) -> str:
        """Format assignment title according to requirements: coursecode - activity no. (name)"""
        if not title:
            return ""
        
        try:
            # Clean the title
            title = title.strip()
            title = re.sub(r'\s+', ' ', title)
            
            # Extract activity number and name from title
            # Pattern: "ACTIVITY 1 - USER STORY" -> "activity 1" and "user story"
            activity_match = re.search(r'(ACTIVITY\s+\d+)', title, re.IGNORECASE)
            
            if activity_match and course_code:
                activity_part = activity_match.group(1).lower()
                
                # Extract the remaining part as the activity name
                remaining = title.replace(activity_match.group(1), '', 1)
                remaining = re.sub(r'^\s*-\s*', '', remaining)  # Remove leading dash
                remaining = remaining.strip()
                
                if remaining:
                    # Format: "hci - activity 1 (user story)"
                    return f"{course_code.lower()} - {activity_part} ({remaining.lower()})"
                else:
                    return f"{course_code.lower()} - {activity_part}"
            
            # Fallback: try to extract any number pattern
            number_match = re.search(r'(\d+)', title)
            if number_match and course_code:
                activity_num = number_match.group(1)
                # Try to get descriptive name
                name_part = re.sub(r'\b(?:activity|assignment|task)\s*\d+\b', '', title, flags=re.IGNORECASE)
                name_part = re.sub(r'[-\s]+', ' ', name_part).strip()
                
                if name_part:
                    return f"{course_code.lower()} - activity {activity_num} ({name_part.lower()})"
                else:
                    return f"{course_code.lower()} - activity {activity_num}"
            
            # If no course code, return cleaned title
            if course_code:
                return f"{course_code.lower()} - {title.lower()}"
            else:
                return title.lower()
                
        except Exception as e:
            logger.warning(f"Error formatting title '{title}': {e}")
            return title or "Unknown Assignment"

    def _parse_date(self, date_string: str) -> Optional[str]:
        """Parse various date formats into ISO format with enhanced error handling"""
        if not date_string:
            return None
            
        try:
            date_string = date_string.strip()
            
            # Enhanced date patterns for various formats
            date_patterns = [
                # ISO format
                (r'(\d{4}-\d{2}-\d{2})', ['%Y-%m-%d']),
                # MM/DD/YYYY and DD/MM/YYYY
                (r'(\d{1,2}/\d{1,2}/\d{4})', ['%m/%d/%Y', '%d/%m/%Y']),
                # MM-DD-YYYY and DD-MM-YYYY
                (r'(\d{1,2}-\d{1,2}-\d{4})', ['%m-%d-%Y', '%d-%m-%Y']),
                # Month DD, YYYY (e.g., "September 5, 2025")
                (r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', ['%B %d, %Y', '%b %d, %Y']),
                # DD Month YYYY (e.g., "5 September 2025")
                (r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', ['%d %B %Y', '%d %b %Y']),
                # Full format with day and time: "Friday, 5 September 2025, 10:09 AM"
                (r'[A-Za-z]+,\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})', ['%d %B %Y', '%d %b %Y']),
                # Just the date part from complex strings
                (r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', ['%d %B %Y', '%d %b %Y'])
            ]
            
            for pattern, formats in date_patterns:
                match = re.search(pattern, date_string, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    
                    # Try each format for this pattern
                    for fmt in formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
            
            # If no pattern matched, try some common formats directly
            direct_formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
            ]
            
            for fmt in direct_formats:
                try:
                    parsed_date = datetime.strptime(date_string, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error parsing date '{date_string}': {e}")
        
        # Return original string if parsing fails
        return date_string

    def load_existing_assignments(self) -> List[Dict]:
        """Load existing assignments from JSON file"""
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def is_duplicate(self, new_assignment: Dict, existing_assignments: List[Dict]) -> bool:
        """Check if assignment already exists"""
        for existing in existing_assignments:
            if (existing.get('title', '').lower() == new_assignment.get('title', '').lower() and
                existing.get('course', '').lower() == new_assignment.get('course', '').lower()):
                return True
        return False
    
    def save_assignments(self, assignments: List[Dict]):
        """Save assignments to both JSON and Markdown files"""
        
        # Save to JSON
        with open(self.json_file, 'w') as f:
            json.dump(assignments, f, indent=2)
        
        # Save to Markdown
        with open(self.md_file, 'w') as f:
            f.write("# Moodle Assignments\n\n")
            f.write("| Assignment | Due Date | Course | Status | Added Date |\n")
            f.write("|------------|----------|--------|--------|-----------|\n")
            
            for assignment in assignments:
                title = assignment.get('title', 'Unknown')
                due_date = assignment.get('due_date', 'No due date')
                course = assignment.get('course', 'Unknown Course')
                status = assignment.get('status', 'Pending')
                added_date = assignment.get('added_date', 'Unknown')
                
                # Escape pipe characters in content
                title = title.replace('|', '\\|')
                course = course.replace('|', '\\|')
                
                f.write(f"| {title} | {due_date} | {course} | {status} | {added_date} |\n")
    
    def run_check(self, days_back: int = 7) -> int:
        """Main method to check for new assignments"""
        logger.info("Starting Moodle assignment check...")
        
        try:
            # Connect to Gmail
            mail = self.connect_to_gmail()
            
            # Search for Moodle emails
            email_ids = self.search_moodle_emails(mail, days_back)
            
            if not email_ids:
                logger.info("No new Moodle emails found")
                mail.logout()
                return 0
            
            # Load existing assignments
            existing_assignments = self.load_existing_assignments()
            new_assignments_count = 0
            
            # Process each email
            for email_id in email_ids:
                assignment_info = self.parse_email_content(mail, email_id)
                
                if assignment_info:
                    # Check for duplicates
                    if not self.is_duplicate(assignment_info, existing_assignments):
                        existing_assignments.append(assignment_info)
                        new_assignments_count += 1
                        logger.info(f"Added new assignment: {assignment_info['title']}")
                    else:
                        logger.info(f"Skipped duplicate assignment: {assignment_info['title']}")
            
            # Save updated assignments
            if new_assignments_count > 0:
                self.save_assignments(existing_assignments)
                logger.info(f"Added {new_assignments_count} new assignments")
            else:
                logger.info("No new assignments to add")
            
            mail.logout()
            return new_assignments_count
            
        except Exception as e:
            logger.error(f"Error during assignment check: {e}")
            return -1

def main():
    """Main function"""
    try:
        fetcher = MoodleEmailFetcher()
        new_count = fetcher.run_check()
        
        if new_count > 0:
            print(f"✅ Successfully added {new_count} new assignments!")
        elif new_count == 0:
            print("ℹ️ No new assignments found.")
        else:
            print("❌ Error occurred during check.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
