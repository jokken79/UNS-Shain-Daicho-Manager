#!/usr/bin/env python3
"""
UNS 社員台帳 Manager - Main Entry Point
"""

import os
import sys
from datetime import datetime
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shain_utils import ShainDaicho

EXPORT_SUFFIXES = {
    'excel': '.xlsx',
    'json': '.json',
    'csv': ''
}


def _print_usage() -> None:
    """Print CLI usage instructions."""
    print("UNS 社員台帳 Manager v2.0.0")
    print("\nUsage:")
    print("  # Run web app:")
    print("  streamlit run src/app_shain_daicho.py")
    print("\n  # Or use CLI:")
    print("  python main.py <file.xlsm> <command>")
    print("\nCommands:")
    print("  summary               - Show summary statistics")
    print("  active                - Count active employees")
    print("  visa-alerts [days]    - Show visa expiration alerts (default: 90)")
    print("  search <name>         - Search employee by name")
    print("  export <format>       - Export data (excel|json|csv)")


def _run_command(sd: ShainDaicho, command: str, args: List[str]) -> int:
    """Execute a CLI command and return an exit code."""
    if command == 'summary':
        print(sd.to_json_summary())
        return 0

    if command == 'active':
        stats = sd.get_summary_stats()
        total = stats.get('total', {})
        print(f"Active employees: {total.get('active', 0)}/{total.get('total', 0)}")
        return 0

    if command == 'visa-alerts':
        days = 90
        if args:
            try:
                days = max(int(args[0]), 0)
            except ValueError:
                print("Error: visa-alerts optional days must be an integer")
                return 1

        alerts = sd.get_visa_alerts(days=days)
        print(f"Visa alerts (next {days} days): {len(alerts)}\n")
        for alert in alerts[:15]:
            print(
                f"  {alert['alert_level']} {str(alert['name']):20} "
                f"- {alert['expiry_date']} ({alert['days_left']} days)"
            )
        return 0

    if command == 'search':
        if not args:
            print("Error: search requires a name argument")
            return 1

        name = args[0]
        results = sd.search_employee(name)
        print(f"Found {len(results)} employees matching '{name}':\n")
        for result in results:
            print(
                f"  [{result['category']}] {str(result['name']):20} "
                f"(ID: {result['employee_id']}, {result['nationality']})"
            )
        return 0

    if command == 'export':
        if not args:
            print("Error: export requires format argument (excel|json|csv)")
            return 1

        format_type = args[0].lower()
        if format_type not in EXPORT_SUFFIXES:
            print(f"Unsupported export format: {format_type}")
            return 1

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = EXPORT_SUFFIXES[format_type]
        output_name = f"export_{timestamp}{suffix}" if suffix else f"export_{timestamp}"

        result = sd.export_active_employees(output_name, format=format_type)
        if result:
            print(f"✅ Exported to {result}")
            return 0

        print("❌ Export failed")
        return 1

    print(f"Unknown command: {command}")
    _print_usage()
    return 1

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        _print_usage()
        sys.exit(0)

    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    filepath = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    args = sys.argv[3:]

    sd = ShainDaicho(filepath)
    if not sd.load():
        print("Error loading file")
        sys.exit(1)

    validation_errors = sd.get_validation_errors()
    if validation_errors:
        print("⚠️ Validation warnings:")
        for error in validation_errors:
            print(f"  - {error}")

    sys.exit(_run_command(sd, command, args))
