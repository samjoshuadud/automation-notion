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
        self.json_file = 'data/assignments.json'
        self.md_file = 'data/assignments.md'
        
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
        """Search for ALL Moodle emails from the past 7 days (read + unread)"""
        try:
            mail.select('inbox')
            
            # Calculate date range (default 7 days for comprehensive coverage)
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search criteria for ALL Moodle emails (read + unread)
            # Updated to use the correct UMak TBL email address
            search_criteria = f'(FROM "noreply-tbl@{self.school_domain}" SINCE "{since_date}")'
            
            logger.info(f"Searching for emails: {search_criteria}")
            status, message_ids = mail.search(None, search_criteria)
            
            if status == 'OK' and message_ids[0]:
                email_ids = message_ids[0].split()
                logger.info(f"Found {len(email_ids)} Moodle emails from last {days_back} days")
                return email_ids
            else:
                logger.info("No Moodle emails found in the specified date range")
                return []
                
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    def parse_email_content(self, mail: imaplib.IMAP4_SSL, email_id: bytes) -> Optional[Dict]:
        """Parse email content to extract assignment information with email ID tracking"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                logger.warning(f"Failed to fetch email {email_id}")
                return None
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract subject and body
            subject = email_message['Subject'] or ""
            body = self._get_email_body(email_message)
            
            # Parse assignment info using regex
            assignment_info = self._extract_assignment_info(subject, body)
            
            if assignment_info:
                # Add email metadata for tracking
                assignment_info['email_id'] = email_id.decode('utf-8') if isinstance(email_id, bytes) else str(email_id)
                assignment_info['email_date'] = email_message['Date']
                assignment_info['email_subject'] = subject
                assignment_info['added_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                assignment_info['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logger.debug(f"Successfully parsed assignment: {assignment_info.get('title', 'Unknown')}")
                
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
            
            # Format the title according to requirements
            formatted_titles = self._format_assignment_title(assignment_title, course_code)
            
            # Apply fallbacks if extraction failed
            if not formatted_titles["display"]:
                display_title = assignment_title or "Unknown Assignment"
                normalized_title = (assignment_title or "unknown assignment").lower()
            else:
                display_title = formatted_titles["display"]
                normalized_title = formatted_titles["normalized"]
            
            if not due_date:
                due_date = "No due date"
                
            if not course_name:
                course_name = "Unknown Course"
            
            # If we found at least a title, return the info
            if assignment_title or display_title != "Unknown Assignment":
                return {
                    'title': display_title,  # Properly capitalized for display/Notion
                    'title_normalized': normalized_title,  # Lowercase for duplicate checking
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
    
    def _format_assignment_title(self, title: str, course_code: str) -> Dict[str, str]:
        """Format assignment title with proper capitalization for display and normalized for matching"""
        if not title:
            return {"display": "", "normalized": ""}
        
        try:
            # Clean the title
            title = title.strip()
            title = re.sub(r'\s+', ' ', title)
            
            # Extract activity number and name from title
            # Pattern: "ACTIVITY 1 - USER STORY" -> "Activity 1" and "User Story"
            activity_match = re.search(r'(ACTIVITY\s+\d+)', title, re.IGNORECASE)
            
            if activity_match and course_code:
                activity_part = activity_match.group(1)
                activity_display = activity_part.title()  # "Activity 1"
                activity_normalized = activity_part.lower()  # "activity 1"
                
                # Extract the remaining part as the activity name
                remaining = title.replace(activity_match.group(1), '', 1)
                remaining = re.sub(r'^\s*-\s*', '', remaining)  # Remove leading dash
                remaining = remaining.strip()
                
                if remaining:
                    # Proper title case for display
                    remaining_display = remaining.title()
                    remaining_normalized = remaining.lower()
                    
                    # Format with proper capitalization
                    display_title = f"{course_code.upper()} - {activity_display} ({remaining_display})"
                    normalized_title = f"{course_code.lower()} - {activity_normalized} ({remaining_normalized})"
                    
                    return {
                        "display": display_title,
                        "normalized": normalized_title
                    }
                else:
                    display_title = f"{course_code.upper()} - {activity_display}"
                    normalized_title = f"{course_code.lower()} - {activity_normalized}"
                    
                    return {
                        "display": display_title,
                        "normalized": normalized_title
                    }
            
            # Fallback: try to extract any number pattern
            number_match = re.search(r'(\d+)', title)
            if number_match and course_code:
                activity_num = number_match.group(1)
                # Try to get descriptive name
                name_part = re.sub(r'\b(?:activity|assignment|task)\s*\d+\b', '', title, flags=re.IGNORECASE)
                name_part = re.sub(r'[-\s]+', ' ', name_part).strip()
                
                if name_part:
                    name_display = name_part.title()
                    name_normalized = name_part.lower()
                    
                    display_title = f"{course_code.upper()} - Activity {activity_num} ({name_display})"
                    normalized_title = f"{course_code.lower()} - activity {activity_num} ({name_normalized})"
                    
                    return {
                        "display": display_title,
                        "normalized": normalized_title
                    }
                else:
                    display_title = f"{course_code.upper()} - Activity {activity_num}"
                    normalized_title = f"{course_code.lower()} - activity {activity_num}"
                    
                    return {
                        "display": display_title,
                        "normalized": normalized_title
                    }
            
            # If no course code, return cleaned title with proper capitalization
            if course_code:
                display_title = f"{course_code.upper()} - {title.title()}"
                normalized_title = f"{course_code.lower()} - {title.lower()}"
                
                return {
                    "display": display_title,
                    "normalized": normalized_title
                }
            else:
                return {
                    "display": title.title(),
                    "normalized": title.lower()
                }
                
        except Exception as e:
            logger.warning(f"Error formatting title '{title}': {e}")
            return {
                "display": title or "Unknown Assignment",
                "normalized": (title or "unknown assignment").lower()
            }

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
        """Enhanced duplicate checking with fuzzy matching and multiple criteria"""
        if not existing_assignments:
            return False
        
        # Use normalized title for comparison, fallback to regular title
        new_title = new_assignment.get('title_normalized', new_assignment.get('title', '')).lower().strip()
        new_course = new_assignment.get('course', '').lower().strip()
        new_due_date = new_assignment.get('due_date', '')
        new_email_id = new_assignment.get('email_id', '')
        
        # Quick exact match check first
        for existing in existing_assignments:
            # Use normalized title if available, fallback to regular title
            existing_title = existing.get('title_normalized', existing.get('title', '')).lower().strip()
            existing_course = existing.get('course', '').lower().strip()
            existing_due_date = existing.get('due_date', '')
            existing_email_id = existing.get('email_id', '')
            
            # Check for exact email ID match (most reliable)
            if new_email_id and existing_email_id and new_email_id == existing_email_id:
                logger.debug(f"Duplicate found by email ID: {new_email_id}")
                return True
            
            # Check for exact title + course match
            if new_title and existing_title and new_title == existing_title:
                if new_course and existing_course and new_course == existing_course:
                    logger.debug(f"Duplicate found by title+course: {new_title}")
                    return True
            
            # Check for fuzzy title match with same course
            if self._fuzzy_match(new_title, existing_title, threshold=0.85):
                if new_course and existing_course and new_course == existing_course:
                    logger.debug(f"Duplicate found by fuzzy match: {new_title} ≈ {existing_title}")
                    return True
            
            # Check for same assignment with updated due date
            if self._fuzzy_match(new_title, existing_title, threshold=0.90):
                if new_course == existing_course and new_due_date != existing_due_date:
                    logger.info(f"Assignment update detected: {new_assignment.get('title', 'Unknown')} - due date changed from {existing_due_date} to {new_due_date}")
                    # This is an update, not a duplicate - allow it through
                    return False
        
        return False
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.85) -> bool:
        """Simple fuzzy string matching using character similarity"""
        if not str1 or not str2:
            return False
        
        # Remove common variations
        str1 = self._normalize_title(str1)
        str2 = self._normalize_title(str2)
        
        if str1 == str2:
            return True
        
        # Calculate similarity using Jaccard similarity with character bigrams
        def get_bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        
        bigrams1 = get_bigrams(str1)
        bigrams2 = get_bigrams(str2)
        
        if not bigrams1 and not bigrams2:
            return True
        if not bigrams1 or not bigrams2:
            return False
        
        intersection = len(bigrams1.intersection(bigrams2))
        union = len(bigrams1.union(bigrams2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for better matching"""
        if not title:
            return ""
        
        # Convert to lowercase and strip
        title = title.lower().strip()
        
        # Remove common variations
        title = re.sub(r'\s+', ' ', title)  # Multiple spaces to single
        title = re.sub(r'[^\w\s-]', '', title)  # Remove special chars except hyphens
        title = re.sub(r'\b(activity|assignment|task|project)\s*', '', title)  # Remove common prefixes
        title = re.sub(r'\s*-\s*', ' ', title)  # Normalize dashes
        
        return title.strip()
    
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
        """Main method to check for new assignments (default: last 7 days)"""
        logger.info("=" * 60)
        logger.info("STARTING MOODLE ASSIGNMENT CHECK")
        logger.info(f"Checking emails from last {days_back} days")
        logger.info("=" * 60)
        
        try:
            # Connect to Gmail
            mail = self.connect_to_gmail()
            
            # Search for Moodle emails (all emails, read + unread)
            email_ids = self.search_moodle_emails(mail, days_back)
            
            if not email_ids:
                logger.info("No Moodle emails found in the specified date range")
                mail.logout()
                return 0
            
            # Load existing assignments for duplicate checking
            existing_assignments = self.load_existing_assignments()
            new_assignments_count = 0
            updated_assignments_count = 0
            skipped_duplicates = 0
            
            logger.info(f"Processing {len(email_ids)} emails...")
            logger.info(f"Existing assignments in database: {len(existing_assignments)}")
            
            # Process each email
            for i, email_id in enumerate(email_ids, 1):
                try:
                    logger.debug(f"Processing email {i}/{len(email_ids)}: {email_id}")
                    assignment_info = self.parse_email_content(mail, email_id)
                    
                    if assignment_info:
                        # Enhanced duplicate checking
                        if not self.is_duplicate(assignment_info, existing_assignments):
                            existing_assignments.append(assignment_info)
                            new_assignments_count += 1
                            logger.info(f"✅ New assignment: {assignment_info['title']}")
                        else:
                            skipped_duplicates += 1
                            logger.debug(f"⏭️  Skipped duplicate: {assignment_info.get('title', 'Unknown')}")
                    else:
                        logger.debug(f"❌ Failed to parse email {email_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            # Save updated assignments if there are new ones
            if new_assignments_count > 0:
                self.save_assignments(existing_assignments)
                logger.info(f"💾 Saved {new_assignments_count} new assignments to files")
            
            # Summary
            logger.info("=" * 60)
            logger.info("ASSIGNMENT CHECK COMPLETED")
            logger.info(f"📧 Emails processed: {len(email_ids)}")
            logger.info(f"✅ New assignments: {new_assignments_count}")
            logger.info(f"⏭️  Duplicates skipped: {skipped_duplicates}")
            logger.info(f"📊 Total assignments: {len(existing_assignments)}")
            logger.info("=" * 60)
            
            mail.logout()
            return new_assignments_count
            
        except Exception as e:
            logger.error(f"Fatal error during assignment check: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
