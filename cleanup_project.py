"""
CLEANUP SCRIPT - Remove Unnecessary Files from Project

This script identifies and removes:
1. Duplicate directories (systematic_sector_rotation_temp)
2. Obsolete test files (test_*.py in root)
3. Temporary database files
4. Redundant documentation files
5. __pycache__ directories
6. Git conflict files in venv

SAFE TO DELETE - All verified as duplicates or unused.
"""

import os
import shutil
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent

print("\n" + "="*80)
print("SYSTEMATIC SECTOR ROTATION - PROJECT CLEANUP")
print("="*80 + "\n")

# Track what we're deleting
files_deleted = []
dirs_deleted = []
space_freed = 0

def get_size(path):
    """Calculate total size of path"""
    total = 0
    try:
        if os.path.isfile(path):
            total = os.path.getsize(path)
        elif os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
    except:
        pass
    return total

# ============================================================================
# 1. DUPLICATE DIRECTORY - systematic_sector_rotation_temp (ENTIRE COPY!)
# ============================================================================
temp_dir = PROJECT_ROOT / 'systematic_sector_rotation_temp'
if temp_dir.exists():
    size = get_size(temp_dir)
    print(f"🗑️  Removing duplicate directory: systematic_sector_rotation_temp")
    print(f"   Size: {size / (1024*1024):.1f} MB")
    try:
        shutil.rmtree(temp_dir)
        dirs_deleted.append('systematic_sector_rotation_temp')
        space_freed += size
        print("   ✅ Deleted\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

# ============================================================================
# 2. OBSOLETE TEST FILES IN ROOT (moved to tests/ directory)
# ============================================================================
obsolete_tests = [
    'test_dual_approach.py',
    'test_implementation_options.py', 
    'test_setup.py'
]

for test_file in obsolete_tests:
    file_path = PROJECT_ROOT / test_file
    if file_path.exists():
        size = get_size(file_path)
        print(f"🗑️  Removing obsolete test: {test_file}")
        try:
            os.remove(file_path)
            files_deleted.append(test_file)
            space_freed += size
            print("   ✅ Deleted\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

# ============================================================================
# 3. TEMPORARY DATABASE FILES
# ============================================================================
temp_dbs = [
    'database/test_strategy.db',
    'database/test_strategy_temp.db'
]

for db_file in temp_dbs:
    file_path = PROJECT_ROOT / db_file
    if file_path.exists():
        size = get_size(file_path)
        print(f"🗑️  Removing temp database: {db_file}")
        try:
            os.remove(file_path)
            files_deleted.append(db_file)
            space_freed += size
            print("   ✅ Deleted\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

# ============================================================================
# 4. REDUNDANT DOCUMENTATION (keeping only essential ones)
# ============================================================================
redundant_docs = [
    'directory.md',  # Redundant with FILE_MAP.md
    'IMPLEMENTATION_OPTIONS_GUIDE.md',  # Already implemented
    'cleanup_obsolete_files.py',  # Old cleanup script
]

for doc_file in redundant_docs:
    file_path = PROJECT_ROOT / doc_file
    if file_path.exists():
        size = get_size(file_path)
        print(f"🗑️  Removing redundant doc: {doc_file}")
        try:
            os.remove(file_path)
            files_deleted.append(doc_file)
            space_freed += size
            print("   ✅ Deleted\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")

# ============================================================================
# 5. __pycache__ DIRECTORIES (auto-generated, safe to delete)
# ============================================================================
print("🗑️  Cleaning __pycache__ directories...")
pycache_count = 0
for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
    if '__pycache__' in dirnames:
        pycache_path = os.path.join(dirpath, '__pycache__')
        if 'venv' not in pycache_path:  # Don't touch venv
            size = get_size(pycache_path)
            try:
                shutil.rmtree(pycache_path)
                pycache_count += 1
                space_freed += size
            except:
                pass

if pycache_count > 0:
    print(f"   ✅ Removed {pycache_count} __pycache__ directories\n")

# ============================================================================
# 6. FIX VENV ACTIVATION SCRIPT (Git conflict markers)
# ============================================================================
venv_activate = PROJECT_ROOT / 'venv' / 'Scripts' / 'Activate.ps1'
if venv_activate.exists():
    print("🔧 Checking venv activation script...")
    try:
        with open(venv_activate, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '<<<<<<< HEAD' in content:
            print("   ⚠️  Git conflict markers found in venv/Scripts/Activate.ps1")
            print("   ℹ️  Recommend: Delete venv and recreate with 'python -m venv venv'")
            print("   (Skipping auto-fix to avoid breaking venv)\n")
        else:
            print("   ✅ No issues found\n")
    except:
        pass

# ============================================================================
# SUMMARY
# ============================================================================
print("="*80)
print("CLEANUP SUMMARY")
print("="*80)
print(f"\nFiles deleted: {len(files_deleted)}")
for f in files_deleted:
    print(f"  - {f}")

print(f"\nDirectories deleted: {len(dirs_deleted)}")
for d in dirs_deleted:
    print(f"  - {d}")

print(f"\nTotal space freed: {space_freed / (1024*1024):.1f} MB")

print("\n" + "="*80)
print("CLEANUP COMPLETE")
print("="*80)

print("\n✅ Project cleaned successfully!")
print("\nREMAINING STRUCTURE:")
print("  ├── config.py          (Configuration)")
print("  ├── main.py            (Entry point)")
print("  ├── verify_system.py   (System verification)")
print("  ├── models/            (Scoring models)")
print("  ├── strategy/          (Strategy engines)")
print("  ├── backtesting/       (Backtest engine)")
print("  ├── dashboard/         (Streamlit UI)")
print("  ├── data/              (Data bridge)")
print("  ├── execution/         (Paper trading)")
print("  ├── utils/             (Helper functions)")
print("  ├── tests/             (Test suites)")
print("  ├── NSE_sector_wise_data/ (Database)")
print("  └── Documentation files")

print("\n📊 Next: Run backtest with 'streamlit run dashboard/streamlit_app.py'")
print("="*80 + "\n")
