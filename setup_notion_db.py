#!/usr/bin/env python3
"""
Notion Database Setup Helper
This script helps you set up your Notion database with the required properties
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import requests
import json

load_dotenv()

def get_database_properties():
    """Get current database properties"""
    
    token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not token or not database_id:
        print("❌ NOTION_TOKEN or NOTION_DATABASE_ID not found in .env file")
        return None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    try:
        url = f'https://api.notion.com/v1/databases/{database_id}'
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error fetching database: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def show_current_properties(database_info):
    """Show current database properties"""
    
    if not database_info:
        return
    
    print("📊 CURRENT DATABASE PROPERTIES:")
    print("-" * 50)
    
    properties = database_info.get('properties', {})
    
    if not properties:
        print("❌ No properties found in the database")
        return
    
    for name, prop in properties.items():
        prop_type = prop.get('type', 'unknown')
        print(f"• {name} ({prop_type})")
        
        # Show additional details for some property types
        if prop_type == 'select':
            options = prop.get('select', {}).get('options', [])
            if options:
                option_names = [opt.get('name', '') for opt in options]
                print(f"  Options: {', '.join(option_names)}")
        elif prop_type == 'multi_select':
            options = prop.get('multi_select', {}).get('options', [])
            if options:
                option_names = [opt.get('name', '') for opt in options]
                print(f"  Options: {', '.join(option_names)}")

def show_required_properties():
    """Show the properties required by our script"""
    
    print("\n🎯 REQUIRED PROPERTIES FOR MOODLE FETCHER:")
    print("-" * 50)
    print("1. Assignment (Title) - The assignment title")
    print("2. Due Date (Date) - When the assignment is due") 
    print("3. Course (Rich Text) - The full course name")
    print("4. Course Code (Rich Text) - The course abbreviation (HCI, CALC, etc.)")
    print("5. Status (Select) - Assignment status with options:")
    print("   • Pending")
    print("   • In Progress") 
    print("   • Completed")
    print("6. Source (Rich Text) - Where the assignment came from (email)")
    print("7. Reminder Date (Date) - 3 days before due date for notifications")

def generate_setup_instructions():
    """Generate step-by-step setup instructions"""
    
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("=" * 60)
    print("1. Go to your Notion database")
    print("2. Click the '...' menu in the top right")
    print("3. Select 'Edit database'")
    print("4. Add/modify the following properties:")
    print()
    
    properties_to_add = [
        ("Assignment", "Title", "This will be the main title of each page"),
        ("Due Date", "Date", "When the assignment is due"),
        ("Course", "Rich Text", "Full course name (e.g., 'HCI - HUMAN COMPUTER INTERACTION')"),
        ("Course Code", "Rich Text", "Course abbreviation (e.g., 'HCI')"),
        ("Status", "Select", "Add options: Pending, In Progress, Completed"),
        ("Source", "Rich Text", "Where the assignment came from (usually 'email')"),
        ("Reminder Date", "Date", "Automatic reminder date (3 days before due)")
    ]
    
    for i, (name, prop_type, description) in enumerate(properties_to_add, 1):
        print(f"{i}. {name} ({prop_type})")
        print(f"   {description}")
        if prop_type == "Select" and name == "Status":
            print("   Add these options: Pending, In Progress, Completed")
        print()
    
    print("5. Save the database")
    print("6. Run the test again: python test_notion_sync.py")

def check_database_readiness():
    """Check if database has all required properties"""
    
    print("🔍 CHECKING DATABASE READINESS...")
    print("-" * 50)
    
    database_info = get_database_properties()
    if not database_info:
        return False
    
    properties = database_info.get('properties', {})
    
    required_properties = {
        'Assignment': 'title',
        'Due Date': 'date',
        'Course': 'rich_text',
        'Course Code': 'rich_text', 
        'Status': 'select',
        'Source': 'rich_text',
        'Reminder Date': 'date'
    }
    
    missing_properties = []
    incorrect_types = []
    
    for req_name, req_type in required_properties.items():
        if req_name not in properties:
            missing_properties.append(req_name)
        else:
            actual_type = properties[req_name].get('type')
            if actual_type != req_type:
                incorrect_types.append(f"{req_name} (found: {actual_type}, expected: {req_type})")
    
    if not missing_properties and not incorrect_types:
        print("✅ Database is ready! All required properties are correctly configured.")
        
        # Check Status options
        status_prop = properties.get('Status', {})
        if status_prop.get('type') == 'select':
            options = status_prop.get('select', {}).get('options', [])
            option_names = [opt.get('name', '') for opt in options]
            required_options = ['Pending', 'In Progress', 'Completed']
            missing_options = [opt for opt in required_options if opt not in option_names]
            
            if missing_options:
                print(f"⚠️  Status property missing options: {', '.join(missing_options)}")
                print("   Add these options to the Status select property")
            else:
                print("✅ Status property has all required options")
        
        return True
    else:
        print("❌ Database needs setup:")
        
        if missing_properties:
            print(f"   Missing properties: {', '.join(missing_properties)}")
        
        if incorrect_types:
            print("   Incorrect property types:")
            for item in incorrect_types:
                print(f"   • {item}")
        
        return False

def main():
    """Main function"""
    
    print("=" * 80)
    print("NOTION DATABASE SETUP HELPER")
    print("=" * 80)
    
    # Check current database
    database_info = get_database_properties()
    
    if database_info:
        print("✅ Successfully connected to Notion database")
        print(f"📄 Database: {database_info.get('title', [{}])[0].get('plain_text', 'Unnamed')}")
        print()
        
        show_current_properties(database_info)
        show_required_properties()
        
        print()
        is_ready = check_database_readiness()
        
        if not is_ready:
            print()
            generate_setup_instructions()
        else:
            print()
            print("🎉 Your database is ready! You can now run:")
            print("   python test_notion_sync.py")
    else:
        print("❌ Could not connect to database. Check your .env file:")
        print("   • NOTION_TOKEN should be your integration token")
        print("   • NOTION_DATABASE_ID should be your database ID")

if __name__ == "__main__":
    main()
