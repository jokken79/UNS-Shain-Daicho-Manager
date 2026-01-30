#!/usr/bin/env python3
"""
UNS 社員台帳 Manager - Main Entry Point
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shain_utils import ShainDaicho

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("UNS 社員台帳 Manager v2.0.0")
        print("\nUsage:")
        print("  # Run web app:")
        print("  streamlit run src/app_shain_daicho.py")
        print("\n  # Or use CLI:")
        print("  python main.py <file.xlsm> <command>")
        print("\nCommands: summary, active, visa-alerts, search <name>, export <format>")
        sys.exit(1)
    
    sd = ShainDaicho(sys.argv[1])
    if sd.load():
        command = sys.argv[2] if len(sys.argv) > 2 else 'summary'
        # CLI logic here...
    else:
        print("Error loading file")
        sys.exit(1)
