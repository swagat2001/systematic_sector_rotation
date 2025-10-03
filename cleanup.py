"""
Cleanup Script for Production Deployment

Removes redundant files and organizes structure.
Run this to prepare for production/client delivery.
"""

import os
import shutil
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent

# Files to remove (redundant documentation)
FILES_TO_REMOVE = [
    'PHASE1_README.md',
    'PHASE2_README.md',
    'PHASE3_README.md',
    'PHASE4_README.md',
    'PHASE5_README.md',
    'PHASE6_README.md',
    'PROGRESS_REPORT.md',
    'PROJECT_COMPLETE.md',
    'PROJECT_STATUS_FINAL.md',
    'STATUS_UPDATE.md',
    'directory.md',
    'test_setup.py',
    'main.py',
    'CLEANUP_PLAN.md'  # Remove this file itself after reading
]

# Directories to remove (unused)
DIRS_TO_REMOVE = [
    'models',
    'logs',
    'database',
    'tests'
]

def cleanup():
    """Remove redundant files and directories"""
    
    print("\n" + "="*60)
    print("PRODUCTION CLEANUP")
    print("="*60)
    
    removed_files = 0
    removed_dirs = 0
    
    # Remove files
    print("\nRemoving redundant files...")
    for filename in FILES_TO_REMOVE:
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"  ✓ Removed: {filename}")
                removed_files += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {filename}: {e}")
        else:
            print(f"  - Not found: {filename}")
    
    # Remove directories
    print("\nRemoving unused directories...")
    for dirname in DIRS_TO_REMOVE:
        dirpath = PROJECT_ROOT / dirname
        if dirpath.exists() and dirpath.is_dir():
            try:
                shutil.rmtree(dirpath)
                print(f"  ✓ Removed: {dirname}/")
                removed_dirs += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {dirname}/: {e}")
        else:
            print(f"  - Not found: {dirname}/")
    
    # Summary
    print("\n" + "="*60)
    print("CLEANUP COMPLETE")
    print("="*60)
    print(f"\nRemoved:")
    print(f"  Files: {removed_files}")
    print(f"  Directories: {removed_dirs}")
    print(f"\nProject is now clean and production-ready!")
    print("="*60 + "\n")

if __name__ == "__main__":
    response = input("This will delete files. Continue? (yes/no): ")
    if response.lower() == 'yes':
        cleanup()
    else:
        print("Cleanup cancelled.")
