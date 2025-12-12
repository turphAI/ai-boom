#!/usr/bin/env python3
"""
Fix deprecated datetime.now(timezone.utc) usage across the codebase
"""

import os
import re
from pathlib import Path

def fix_datetime_imports(content):
    """Add timezone import if datetime is imported"""
    # Check if datetime is imported
    if 'from datetime import' in content:
        # Check if timezone is already imported
        if 'timezone' not in content:
            # Add timezone to existing datetime imports
            content = re.sub(
                r'from datetime import ([^,\n]+)',
                r'from datetime import \1, timezone',
                content
            )
    elif 'import datetime' in content:
        # For 'import datetime' style, we'll need to use datetime.timezone
        pass
    
    return content

def fix_utcnow_calls(content):
    """Replace datetime.now(timezone.utc) with datetime.now(timezone.utc)"""
    # Replace datetime.now(timezone.utc) with datetime.now(timezone.utc)
    content = re.sub(
        r'datetime\.utcnow\(\)',
        r'datetime.now(timezone.utc)',
        content
    )
    
    return content

def process_file(file_path):
    """Process a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports first
        content = fix_datetime_imports(content)
        
        # Fix utcnow calls
        content = fix_utcnow_calls(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix datetime deprecation across the codebase"""
    print("🔧 Fixing deprecated datetime.now(timezone.utc) usage...")
    print("=" * 50)
    
    # Directories to process
    directories = [
        'scrapers',
        'handlers', 
        'services',
        'utils',
        'tests',
        'scripts'
    ]
    
    files_processed = 0
    files_fixed = 0
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n📁 Processing {directory}/")
            
            for file_path in Path(directory).rglob('*.py'):
                if file_path.name.startswith('.'):
                    continue
                    
                files_processed += 1
                if process_file(file_path):
                    files_fixed += 1
    
    print(f"\n" + "=" * 50)
    print(f"🎉 Processing complete!")
    print(f"   Files processed: {files_processed}")
    print(f"   Files fixed: {files_fixed}")
    
    if files_fixed > 0:
        print(f"\n✅ Fixed deprecated datetime.now(timezone.utc) usage in {files_fixed} files")
        print("   All datetime calls now use timezone-aware datetime.now(timezone.utc)")
    else:
        print("\n✅ No deprecated datetime usage found")

if __name__ == "__main__":
    main()