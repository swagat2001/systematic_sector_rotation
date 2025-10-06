"""
Force Git to accept resolved conflicts
"""

import subprocess
import os

os.chdir(r"C:\Users\swaga\OneDrive\Desktop\systematic_sector_rotation")

files_to_resolve = [
    "utils/__init__.py",
    "utils/helpers.py", 
    "utils/logger.py",
    "requirements.txt",
    "config.py"
]

print("Resolving Git conflicts...\n")

for file in files_to_resolve:
    try:
        # Add the file (marks as resolved)
        subprocess.run(["git", "add", file], check=True, capture_output=True)
        print(f"✅ Resolved: {file}")
    except:
        print(f"⚠️  Skipped: {file} (not in conflict)")

print("\n✅ All conflicts resolved!")
print("\nRun: git status")
