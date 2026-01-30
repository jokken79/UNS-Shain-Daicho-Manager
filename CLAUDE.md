# CLAUDE.md - AI Assistant Guide

## Project Overview

**UNS-Shain-Daicho-Manager** is an enterprise-grade employee registry management system for Universal Kikaku (UNS), a Japanese staffing company. It manages employee data from Excel files (社員台帳/Employee Registry), providing data analysis, visa expiration tracking, salary analytics, and employee search capabilities.

**Version:** 2.0.0
**Language:** Python 3.8+
**License:** MIT

## Quick Start Commands

```bash
# Run web interface (recommended)
streamlit run src/app_shain_daicho.py

# Run CLI commands
python main.py                                    # Show usage help
python src/shain_utils.py "file.xlsm" summary     # Get summary stats
python src/shain_utils.py "file.xlsm" visa-alerts # Check visa expirations
python src/shain_utils.py "file.xlsm" search NAME # Search employees

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
UNS-Shain-Daicho-Manager/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── .gitignore             # Git ignore patterns
│
├── src/
│   ├── app_shain_daicho.py   # Streamlit web application (697 lines)
│   ├── shain_utils.py        # Core utility class ShainDaicho (685 lines)
│   └── config.yaml           # Configuration settings (230+ lines)
│
├── examples/
│   └── example_usage.py      # Usage examples
│
└── docs/
    ├── README.md             # Quick start guide
    ├── QUICK_START.md        # 30-second quick start
    ├── GUIA_COMPLETA.md      # Complete guide
    ├── RESUMEN_EJECUTIVO.md  # Executive summary
    ├── CONTRIBUTING.md       # Contribution guidelines
    └── CHANGELOG.md          # Version history
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.8+ | Core logic |
| Data Processing | pandas, numpy | Excel reading, data manipulation |
| Excel Support | openpyxl | .xlsm/.xlsx file handling |
| Web UI | Streamlit | Interactive web interface |
| Visualization | Plotly | Interactive charts |
| Date Handling | python-dateutil | Date/time parsing |

## Core Architecture

### ShainDaicho Class (`src/shain_utils.py`)

The main class that handles all employee data operations:

```python
from shain_utils import ShainDaicho

sd = ShainDaicho('file.xlsm')
sd.load()  # Must call before using

# Key methods
sd.get_active_employees(category='派遣社員')  # Filter by category
sd.search_employee('NGUYEN', active_only=True)  # Search by name
sd.get_employee_by_id(12345)                    # Lookup by ID
sd.get_summary_stats()                          # Overall statistics
sd.get_salary_stats(active_only=True)           # Salary analysis
sd.get_visa_alerts(days=90)                     # Visa expiration alerts
sd.get_nationality_breakdown()                  # Count by country
sd.get_age_breakdown()                          # Age distribution
sd.export_active_employees(path, format='excel') # Export data
```

### Data Sources (Excel Sheets)

| Sheet Name | Japanese | Content |
|------------|----------|---------|
| DBGenzaiX | 派遣社員 | Dispatch workers |
| DBUkeoiX | 請負社員 | Contract workers |
| DBStaffX | スタッフ | Administrative staff |
| DBTaishaX | 退社者 | Former employees |

### Key Column Mappings

| Japanese | English | Type |
|----------|---------|------|
| 社員№ | Employee ID | Identifier |
| 氏名 | Name | Text |
| カナ | Name (Kana) | Text |
| 現在 | Current Status | 在職中/Inactive |
| 国籍 | Nationality | Text |
| 入社日 | Hire Date | Date |
| 退社日 | Resignation Date | Date |
| ビザ期限 | Visa Expiry | Date |
| 時給 | Hourly Rate | Numeric (¥) |
| 請求単価 | Billing Rate | Numeric (¥) |
| 差額利益 | Profit Margin | Numeric (¥) |
| 派遣先 | Dispatch Company | Text |
| 年齢 | Age | Numeric |

## Web Application (`src/app_shain_daicho.py`)

Streamlit app with 6 main tabs:

1. **📊 Dashboard** - Key metrics, distribution charts, nationality breakdown
2. **👤 Search** - Employee search with detailed cards
3. **🔔 Visa Alerts** - Expiration alerts with urgency levels (🔴🟠🟡)
4. **💰 Salary Analysis** - Hourly rate, billing rate, profit margin statistics
5. **📈 Reports** - Age distribution, tenure analysis, custom reports
6. **⚙️ Export** - Multi-format export (Excel, JSON, CSV)

## Code Conventions

### Type Hints
All functions use full type annotations:
```python
def search_employee(self, name: str, active_only: bool = True) -> List[Dict[str, Any]]:
```

### Error Handling
All methods wrap operations in try/except with logging:
```python
try:
    # operation
except Exception as e:
    logging.error(f"Error: {e}")
    return default_value
```

### Data Processing Patterns

```python
# Always copy to avoid SettingWithCopyWarning
df = self.df_genzai[self.df_genzai['現在'] == '在職中'].copy()

# Safe type conversion
numeric_values = pd.to_numeric(df['時給'], errors='coerce').dropna()

# Safe date conversion
df['ビザ期限'] = pd.to_datetime(df['ビザ期限'], errors='coerce')

# NaN checking
if pd.notna(value) and pd.isna(value)
```

### Status Checking
Active employees have status `'在職中'` (meaning "in employment"):
```python
df[df['現在'] == '在職中']
```

### Logging
Use standard Python logging:
```python
import logging
logging.info("Operation completed")
logging.warning("Warning message")
logging.error(f"Error occurred: {e}")
```

## Configuration (`src/config.yaml`)

Key settings:

```yaml
analysis:
  company_burden_rate: 15.76  # For profit calculation
  visa_alert_thresholds:
    critical: 30    # days - 🔴 URGENT
    warning: 60     # days - 🟠 WARNING
    upcoming: 90    # days - 🟡 UPCOMING

age_groups:
  - {min: 0, max: 19, label: "Under 20"}
  - {min: 20, max: 29, label: "20-29"}
  - {min: 30, max: 39, label: "30-39"}
  - {min: 40, max: 49, label: "40-49"}
  - {min: 50, max: 59, label: "50-59"}
  - {min: 60, max: 999, label: "60+"}

export:
  formats: [excel, json, csv]
  csv_encoding: utf-8-sig  # For Japanese character support
```

## Development Guidelines

### Adding New Features

1. Add core logic to `src/shain_utils.py` in the `ShainDaicho` class
2. Add UI components to `src/app_shain_daicho.py` in appropriate tab
3. Update `src/config.yaml` for any new settings
4. Update documentation in `docs/`

### Testing Changes

```bash
# Test web interface
streamlit run src/app_shain_daicho.py

# Test CLI
python src/shain_utils.py "data/file.xlsm" summary

# Test Python module
python -c "from src.shain_utils import ShainDaicho; print('Import OK')"
```

### File Naming

- Python files: `snake_case.py`
- Documentation: `UPPER_CASE.md` for main docs
- Configuration: `config.yaml`

### Commit Messages

Follow conventional format:
- `Add feature X`
- `Fix bug in Y`
- `Update documentation`
- `Refactor Z module`

## Important Context for AI Assistants

### Communication Language

**IMPORTANTE:** Siempre responder al usuario en español. Todas las interacciones y explicaciones deben ser en español.

### Language Notes

- **Data fields are in Japanese** - The Excel files and DataFrame columns use Japanese field names
- **UI can support multiple languages** - Config has language settings (ja, en, es)
- **Comments and docstrings are in English** - Code documentation is in English

### Business Logic

- **Company burden rate (15.76%)** - Applied to salary calculations for profit margins
- **Visa alerts** - Critical business function for compliance tracking
- **Employee categories** - Three main types: 派遣社員 (dispatch), 請負社員 (contract), スタッフ (staff)
- **Active status** - `'在職中'` means currently employed

### Common Operations

| Task | Location | Method |
|------|----------|--------|
| Load data | shain_utils.py | `ShainDaicho.load()` |
| Search employees | shain_utils.py | `search_employee(name)` |
| Get statistics | shain_utils.py | `get_summary_stats()` |
| Check visas | shain_utils.py | `get_visa_alerts(days)` |
| Export data | shain_utils.py | `export_active_employees()` |
| Render web UI | app_shain_daicho.py | Streamlit tabs |

### Data Validation

The system validates:
- Required columns exist in Excel sheets
- Date formats are parseable
- Numeric fields contain valid numbers
- Employee IDs are present

### Error Recovery

If data loading fails:
1. Check file path is correct
2. Verify Excel file has expected sheet names
3. Check for required columns
4. Review logs for specific errors

## Dependencies

```
pandas>=1.3.0,<3.0.0
openpyxl>=3.6.0,<4.0.0
numpy>=1.21.0,<2.0.0
streamlit>=1.10.0,<2.0.0
plotly>=5.0.0,<6.0.0
python-dateutil>=2.8.2,<3.0.0
```

## Current Dataset Statistics

- **Total employees:** 1,222
- **Active employees:** 475 (39%)
- **Top nationality:** Vietnam (84%)
- **Employee categories:** Dispatch (87%), Contract (12%), Staff (1%)

## Links

- **Repository:** UNS-Shain-Daicho-Manager
- **Documentation:** `docs/` directory
- **Examples:** `examples/example_usage.py`
