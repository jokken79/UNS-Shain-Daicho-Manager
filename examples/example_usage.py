#!/usr/bin/env python3
"""
Examples of using ShainDaicho
"""

import sys
sys.path.insert(0, '../src')

from shain_utils import ShainDaicho

# Initialize
sd = ShainDaicho('../data/社員台帳.xlsm')

# Load data
if sd.load():
    # Get summary
    stats = sd.get_summary_stats()
    print(f"Total employees: {stats['total']['total']}")
    
    # Search
    results = sd.search_employee('NGUYEN')
    for r in results:
        print(f"  {r['name']} - {r['category']}")
    
    # Visa alerts
    alerts = sd.get_visa_alerts(days=90)
    print(f"\nVisa alerts: {len(alerts)}")
    
    # Export
    sd.export_active_employees('output.xlsx', format='excel')
