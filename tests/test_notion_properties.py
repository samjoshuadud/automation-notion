#!/usr/bin/env python3
"""
Test script to check Notion database properties
"""

import os
import requests
from dotenv import load_dotenv

def check_notion_properties():
    """Check what properties exist in the Notion database"""
    
    load_dotenv()
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token or not database_id:
        print("❌ Notion credentials not found!")
        return False
    
    headers = {
        'Authorization': f'Bearer {notion_token}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }
    
    try:
        url = f'https://api.notion.com/v1/databases/{database_id}'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            db_info = response.json()
            print("✅ Database found!")
            print(f"📊 Database name: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            
            properties = db_info.get('properties', {})
            print(f"\n📋 Available properties:")
            print("=" * 40)
            
            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get('type', 'unknown')
                print(f"• {prop_name} ({prop_type})")
                
                # Show select options if it's a select property
                if prop_type == 'select' and 'select' in prop_config:
                    options = prop_config['select'].get('options', [])
                    if options:
                        print(f"  Options: {[opt['name'] for opt in options]}")
                
                # Show multi-select options if it's a multi-select property
                elif prop_type == 'multi_select' and 'multi_select' in prop_config:
                    options = prop_config['multi_select'].get('options', [])
                    if options:
                        print(f"  Options: {[opt['name'] for opt in options]}")
            
            return True
        else:
            print(f"❌ Could not access database: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_notion_properties()
