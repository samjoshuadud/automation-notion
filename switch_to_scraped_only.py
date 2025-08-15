#!/usr/bin/env python3
"""
Script to switch from merged assignments system to using only assignments_scraped.json
This is useful when you want to stop using Gmail fetching and only use Moodle scraping.
"""

import json
import shutil
import os
from datetime import datetime

def backup_file(filepath):
    """Create a backup of a file with timestamp"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backed up {filepath} to {backup_path}")
        return backup_path
    return None

def switch_to_scraped_only():
    """Switch to using only assignments_scraped.json as the main data source"""
    
    scraped_file = "data/assignments_scraped.json"
    main_file = "data/assignments.json"
    
    print("🔄 Switching to scraped-only mode...")
    print("=" * 50)
    
    # Check if files exist
    if not os.path.exists(scraped_file):
        print(f"❌ {scraped_file} not found!")
        return False
    
    if not os.path.exists(main_file):
        print(f"❌ {main_file} not found!")
        return False
    
    # Backup current files
    print("\n📦 Creating backups...")
    backup_file(scraped_file)
    backup_file(main_file)
    
    # Load scraped data
    try:
        with open(scraped_file, 'r') as f:
            scraped_data = json.load(f)
        print(f"✅ Loaded {len(scraped_data)} items from {scraped_file}")
    except Exception as e:
        print(f"❌ Failed to load {scraped_file}: {e}")
        return False
    
    # Replace main file with scraped data
    try:
        with open(main_file, 'w') as f:
            json.dump(scraped_data, f, indent=2)
        print(f"✅ Replaced {main_file} with scraped data")
    except Exception as e:
        print(f"❌ Failed to update {main_file}: {e}")
        return False
    
    # Update scraped file to mark it as the source
    try:
        for item in scraped_data:
            if 'source' in item:
                item['source'] = 'scrape_only'
            else:
                item['source'] = 'scrape_only'
        
        with open(scraped_file, 'w') as f:
            json.dump(scraped_data, f, indent=2)
        print(f"✅ Updated {scraped_file} source labels")
    except Exception as e:
        print(f"⚠️ Warning: Failed to update source labels: {e}")
    
    print("\n🎉 Switch complete!")
    print(f"📄 {main_file} now contains {len(scraped_data)} items from scraping")
    print(f"📄 {scraped_file} is your source of truth")
    print("\n💡 Your system is now configured to:")
    print("   - Use only scraped data (no more merging)")
    print("   - Save new scrapes to assignments_scraped.json")
    print("   - Keep assignments.json as your main database")
    
    return True

if __name__ == "__main__":
    try:
        switch_to_scraped_only()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
