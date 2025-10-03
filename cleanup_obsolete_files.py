"""
Cleanup Obsolete Files

Removes old development files that are no longer needed.
Safe to run - only deletes documented obsolete files.
"""

import os
from pathlib import Path

print("=" * 70)
print("SYSTEMATIC SECTOR ROTATION - FILE CLEANUP")
print("=" * 70)

# List of obsolete files to delete
OBSOLETE_FILES = [
    # Root level - old documentation
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
    'CLEANUP_PLAN.md',
    'cleanup.py',
    'directory.md',
    'DATA_LOADING_GUIDE.md',
    'REAL_DATA_QUICKSTART.md',
    'test_setup.py',
    
    # NSE_sector_wise_data - old scrapers and guides
    'NSE_sector_wise_data/check_database.py',
    'NSE_sector_wise_data/nse_csv_loader.py',
    'NSE_sector_wise_data/nse_data_scraper.py',
    'NSE_sector_wise_data/nse_robust_scraper.py',
    'NSE_sector_wise_data/dynamic_sector_mapper.py',
    'NSE_sector_wise_data/sector_mapper.py',
    'NSE_sector_wise_data/SCRAPER_INTEGRATION_GUIDE.md',
    'NSE_sector_wise_data/SECTOR_MAPPING_GUIDE.md',
    'NSE_sector_wise_data/requirements.txt',
]

def cleanup():
    """Clean up obsolete files"""
    
    project_root = Path(__file__).parent
    
    deleted = []
    not_found = []
    errors = []
    
    print("\nScanning for obsolete files...\n")
    
    for file_path in OBSOLETE_FILES:
        full_path = project_root / file_path
        
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    deleted.append(file_path)
                    print(f"✓ Deleted: {file_path}")
                else:
                    errors.append((file_path, "Not a file"))
                    print(f"✗ Skipped: {file_path} (not a file)")
            except Exception as e:
                errors.append((file_path, str(e)))
                print(f"✗ Error deleting {file_path}: {e}")
        else:
            not_found.append(file_path)
            print(f"⊗ Not found: {file_path}")
    
    # Summary
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"\n✓ Successfully deleted: {len(deleted)} files")
    print(f"⊗ Not found: {len(not_found)} files")
    print(f"✗ Errors: {len(errors)} files")
    
    if deleted:
        print("\nDeleted files:")
        for f in deleted:
            print(f"  • {f}")
    
    if errors:
        print("\nErrors:")
        for f, err in errors:
            print(f"  • {f}: {err}")
    
    # Show what remains
    print("\n" + "=" * 70)
    print("ESSENTIAL FILES KEPT")
    print("=" * 70)
    
    essential_files = [
        'README.md (✓ UPDATED)',
        'ARCHITECTURE.md (✓ UPDATED)',
        'FILE_MAP.md (✓ NEW - Complete file reference)',
        'config.py',
        'main.py',
        'requirements.txt',
        'ZERODHA_KITE_GUIDE.md',
        '',
        'NSE_sector_wise_data/:',
        '  • nse_cash_ohlc_pipeline.py (main scraper)',
        '  • download_equity_list.py',
        '  • check_nse_database.py',
        '  • test_nse_connection.py',
        '  • nse_cash.db (database)',
        '  • EQUITY_L.csv',
        '',
        'strategy/:',
        '  • sector_rotation.py',
        '  • stock_selection.py',
        '  • portfolio_manager.py',
        '',
        'models/:',
        '  • technical_scorer.py',
        '  • fundamental_scorer.py',
        '  • statistical_scorer.py',
        '  • composite_scorer.py',
        '',
        'backtesting/:',
        '  • backtest_engine.py',
        '  • performance_analyzer.py',
        '',
        'dashboard/:',
        '  • streamlit_app.py',
        '  • real_data_backtest.py',
        '  • chart_generator.py',
        '',
        'data/:',
        '  • nse_data_bridge.py (★ CRITICAL)',
        '  • data_storage.py',
        '  • data_validator.py',
        '',
        'utils/:',
        '  • logger.py',
        '  • helpers.py',
    ]
    
    print("\n" + "\n".join(essential_files))
    
    print("\n" + "=" * 70)
    print("CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nProject structure is now clean and production-ready.")
    print("\nNext steps:")
    print("  1. Review: README.md")
    print("  2. File reference: FILE_MAP.md")
    print("  3. Architecture: ARCHITECTURE.md")
    print("  4. Run backtest: streamlit run dashboard/streamlit_app.py")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    # Confirm before deleting
    print("\nThis will delete old/obsolete development files.")
    print("All essential production files will be kept.")
    print("\nFiles to delete:")
    for f in OBSOLETE_FILES[:5]:
        print(f"  • {f}")
    print(f"  ... and {len(OBSOLETE_FILES) - 5} more files")
    
    response = input("\nProceed with cleanup? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        cleanup()
    else:
        print("\nCleanup cancelled. No files were deleted.")
