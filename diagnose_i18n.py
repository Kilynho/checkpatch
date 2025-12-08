#!/usr/bin/env python3
"""
diagnose_i18n.py - Diagnostic script for i18n issues

Run this script to diagnose i18n-related problems:
    python3 diagnose_i18n.py
"""

import sys
import os
from pathlib import Path

def main():
    print("=" * 70)
    print("i18n Diagnostic Script")
    print("=" * 70)
    print()
    
    # Check current directory
    print("1. Current directory:", os.getcwd())
    print()
    
    # Check if i18n directory exists
    i18n_dir = Path(__file__).parent / "i18n"
    print("2. i18n directory:", i18n_dir)
    print("   Exists:", i18n_dir.exists())
    if i18n_dir.exists():
        files = list(i18n_dir.glob("*.json"))
        print("   Files found:", [f.name for f in files])
    print()
    
    # Try to import i18n
    print("3. Importing i18n module...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import i18n
        print("   ✓ i18n module imported successfully")
        print("   Language:", i18n.get_language())
        print("   Strings loaded:", len(i18n._locale_manager.strings))
    except Exception as e:
        print(f"   ✗ Failed to import i18n: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Test get_text function
    print("4. Testing get_text function...")
    try:
        from i18n import get_text as _
        test_strings = [
            ('html.dashboard_title', {}),
            ('html.analyzer_title', {}),
            ('analyzer.analyzing', {'total': 10, 'workers': 4}),
            ('errors.file_not_exist', {'file': 'test.c'})
        ]
        for key, params in test_strings:
            result = _(key, **params)
            print(f"   ✓ {key}: {result}")
    except Exception as e:
        print(f"   ✗ Failed to get text: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Test language switching
    print("5. Testing language switching...")
    try:
        i18n.set_language('en')
        result = _('html.analyzer_title')
        print(f"   English: {result}")
        
        i18n.set_language('es')
        result = _('html.analyzer_title')
        print(f"   Spanish: {result}")
        print("   ✓ Language switching works")
    except Exception as e:
        print(f"   ✗ Failed to switch language: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Try importing main
    print("6. Importing main module...")
    try:
        import main
        print("   ✓ main module imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import main: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    # Try importing report
    print("7. Importing report module...")
    try:
        import report
        print("   ✓ report module imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import report: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()
    
    print("=" * 70)
    print("All diagnostic checks passed! ✓")
    print("=" * 70)
    print()
    print("If you're still experiencing issues, please provide the full error")
    print("traceback from running the analyze command:")
    print("  python3 main.py --analyze /path/to/kernel --paths init 2>&1")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
