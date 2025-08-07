#!/usr/bin/env python3
"""
Setup Todoist Integration for Moodle Assignment Automation

This script helps you set up Todoist integration for your assignment automation system.
"""

import os
import sys
from dotenv import load_dotenv

def print_banner():
    print("🎯 TODOIST INTEGRATION SETUP")
    print("=" * 50)
    print("This script will help you set up Todoist integration")
    print("for your Moodle assignment automation system.")
    print("=" * 50)

def check_todoist_token():
    """Check if Todoist token is configured"""
    load_dotenv()
    token = os.getenv('TODOIST_TOKEN')
    
    if token:
        print("✅ Todoist token found in .env file")
        return True
    else:
        print("❌ Todoist token not found in .env file")
        return False

def guide_token_setup():
    """Guide user through getting Todoist API token"""
    print("\n📝 GETTING YOUR TODOIST API TOKEN")
    print("=" * 40)
    print("Follow these steps to get your Todoist API token:")
    print()
    print("1. 🌐 Go to: https://todoist.com/prefs/integrations")
    print("2. 🔍 Look for 'API token' section")
    print("3. 📋 Copy your API token (it's a long string)")
    print("4. 📄 Add it to your .env file as: TODOIST_TOKEN=your_token_here")
    print()
    print("📌 Note: Your Todoist API token works with the free tier!")
    print("   No premium subscription required for basic task management.")
    print()
    
    # Check if .env file exists
    env_path = '.env'
    if not os.path.exists(env_path):
        print("⚠️  No .env file found. Creating one from .env.example...")
        try:
            if os.path.exists('.env.example'):
                with open('.env.example', 'r') as example:
                    content = example.read()
                with open('.env', 'w') as env_file:
                    env_file.write(content)
                print("✅ Created .env file from template")
            else:
                # Create basic .env file
                basic_env = """# Gmail Configuration (Required)
GMAIL_EMAIL=your.email@umak.edu.ph
GMAIL_APP_PASSWORD=your_16_character_app_password

# School Domain Configuration  
SCHOOL_DOMAIN=umak.edu.ph

# Notion Integration (Optional)
NOTION_TOKEN=secret_xyz123...
NOTION_DATABASE_ID=your_database_id

# Todoist Integration (Optional)
TODOIST_TOKEN=your_todoist_api_token
"""
                with open('.env', 'w') as env_file:
                    env_file.write(basic_env)
                print("✅ Created basic .env file")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    print(f"📄 Edit your .env file and add your Todoist token:")
    print(f"   TODOIST_TOKEN=your_api_token_here")
    print()
    return True

def test_todoist_connection():
    """Test Todoist connection"""
    print("\n🧪 TESTING TODOIST CONNECTION")
    print("=" * 40)
    
    try:
        # Add current directory to path for imports
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from todoist_integration import TodoistIntegration
        
        print("1. Initializing Todoist integration...")
        todoist = TodoistIntegration()
        
        if not todoist.enabled:
            print("❌ Todoist integration not enabled")
            print("   Make sure TODOIST_TOKEN is set in your .env file")
            return False
        
        print("✅ Todoist integration initialized")
        
        print("2. Testing API connection...")
        if todoist._test_connection():
            print("✅ Todoist API connection successful")
        else:
            print("❌ Todoist API connection failed")
            return False
        
        print("3. Setting up School Assignments project...")
        project_id = todoist.get_or_create_project("School Assignments")
        if project_id:
            print(f"✅ 'School Assignments' project ready (ID: {project_id})")
        else:
            print("❌ Failed to create/find School Assignments project")
            return False
        
        print("4. Getting project statistics...")
        stats = todoist.get_project_stats()
        if stats:
            print(f"📊 Project Statistics:")
            print(f"   Total tasks: {stats.get('total_tasks', 0)}")
            print(f"   Completed: {stats.get('completed_tasks', 0)}")
            print(f"   Pending: {stats.get('pending_tasks', 0)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running this from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples"""
    print("\n🚀 USAGE EXAMPLES")
    print("=" * 40)
    print("Now that Todoist is set up, you can use these commands:")
    print()
    print("📥 Fetch and sync to Todoist:")
    print("   python run_fetcher.py --todoist")
    print()
    print("📥 Fetch and sync to both Notion and Todoist:")
    print("   python run_fetcher.py --notion --todoist")
    print()
    print("🧪 Test Todoist integration:")
    print("   python tests/test_todoist_sync.py")
    print()
    print("🔍 Test connection only:")
    print("   python run_fetcher.py --test --todoist")
    print()

def show_todoist_features():
    """Show what Todoist integration provides"""
    print("\n✨ TODOIST INTEGRATION FEATURES")
    print("=" * 40)
    print("Your Todoist will automatically get:")
    print()
    print("📋 Features:")
    print("   • Assignments as tasks in 'School Assignments' project")
    print("   • Course codes as task labels [HCI], [MATH], etc.")
    print("   • Due dates automatically set")
    print("   • Course information in task descriptions")
    print("   • Duplicate detection (won't create duplicates)")
    print()
    print("🎯 Free Tier Compatible:")
    print("   • Works with Todoist free account")
    print("   • No premium features required")
    print("   • Up to 80 projects (more than enough)")
    print("   • Task management and due dates")
    print()
    print("📱 Cross-Platform:")
    print("   • Access on mobile, web, desktop")
    print("   • Real-time sync across devices")
    print("   • Notifications and reminders")
    print()

def main():
    print_banner()
    
    # Step 1: Check current setup
    print("\n1️⃣ CHECKING CURRENT SETUP")
    print("-" * 30)
    
    token_exists = check_todoist_token()
    
    if not token_exists:
        # Step 2: Guide through token setup
        print("\n2️⃣ SETTING UP TODOIST TOKEN")
        print("-" * 30)
        guide_token_setup()
        
        print("\n⏸️  SETUP PAUSED")
        print("Please add your Todoist token to the .env file, then run this script again.")
        return
    
    # Step 3: Test connection
    print("\n2️⃣ TESTING CONNECTION")
    print("-" * 30)
    
    connection_ok = test_todoist_connection()
    
    if not connection_ok:
        print("\n❌ SETUP INCOMPLETE")
        print("Please check your Todoist token and try again.")
        return
    
    # Step 4: Show features and usage
    show_todoist_features()
    show_usage_examples()
    
    print("\n🎉 TODOIST INTEGRATION SETUP COMPLETE!")
    print("=" * 50)
    print("✅ Your Todoist integration is ready to use!")
    print("✅ Run 'python run_fetcher.py --todoist' to start syncing")
    print("=" * 50)

if __name__ == "__main__":
    main()
