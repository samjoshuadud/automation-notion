"""
Shared utilities for assignment data management
Provides basic JSON loading/saving functions without Gmail dependencies
"""

import json
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def load_assignments_from_file(file_path: str) -> List[Dict]:
    """Load assignments from a JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            logger.info(f"File {file_path} does not exist, creating empty file")
            # Create empty file
            save_assignments_to_file(file_path, [])
            return []
    except Exception as e:
        logger.error(f"Error loading assignments from {file_path}: {e}")
        # Try to create empty file as fallback
        try:
            save_assignments_to_file(file_path, [])
            return []
        except Exception as fallback_e:
            logger.error(f"Failed to create fallback file {file_path}: {fallback_e}")
            return []

def save_assignments_to_file(file_path: str, assignments: List[Dict]):
    """Save assignments to a JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(assignments, f, indent=2)
        logger.debug(f"Saved {len(assignments)} assignments to {file_path}")
    except Exception as e:
        logger.error(f"Error saving assignments to {file_path}: {e}")
        raise

def is_duplicate_assignment(new_assignment: Dict, existing_assignments: List[Dict], 
                          fuzzy_threshold: float = 0.85) -> bool:
    """
    Check if an assignment is a duplicate based on title and course code
    Uses fuzzy matching for title comparison
    """
    try:
        from fuzzywuzzy import fuzz
        
        new_title = new_assignment.get('title', '').lower()
        new_course = new_assignment.get('course_code', '').lower()
        
        for existing in existing_assignments:
            existing_title = existing.get('title', '').lower()
            existing_course = existing.get('course_code', '').lower()
            
            # Check course code first (exact match)
            if new_course and existing_course and new_course == existing_course:
                # Check title similarity
                if new_title and existing_title:
                    similarity = fuzz.ratio(new_title, existing_title) / 100.0
                    if similarity >= fuzzy_threshold:
                        return True
        
        return False
    except ImportError:
        # Fallback to exact matching if fuzzywuzzy not available
        logger.warning("fuzzywuzzy not available, using exact matching")
        new_title = new_assignment.get('title', '').lower()
        new_course = new_assignment.get('course_code', '').lower()
        
        for existing in existing_assignments:
            existing_title = existing.get('title', '').lower()
            existing_course = existing.get('course_code', '').lower()
            
            if new_title == existing_title and new_course == existing_course:
                return True
        
        return False
