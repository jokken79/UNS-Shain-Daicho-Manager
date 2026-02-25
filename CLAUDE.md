# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

UNS 社員台帳 Manager is a Python tool for managing UNS employee registry data stored in a `.xlsm` Excel workbook. It exposes a CLI and a Streamlit web dashboard.

## Commands

### Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run CLI
```bash
python main.py <file.xlsm> summary
python main.py <file.xlsm> active
python main.py <file.xlsm> visa-alerts [days]   # default 90
python main.py <file.xlsm> search <name>
python main.py <file.xlsm> export excel|json|csv
```

### Run web app
```bash
streamlit run src/app_shain_daicho.py
# Opens at http://localhost:8501
```

### Tests
```bash
# All tests (no fixture file needed — test data is generated dynamically)
python -m unittest discover -s tests -p "test_*.py"

# Single test class
python -m unittest tests.test_shain_daicho.TestShainDaicho

# Single test method
python -m unittest tests.test_shain_daicho.TestShainDaicho.test_search_employee_case_insensitive
```

### Lint (no formatter configured)
```bash
python -m py_compile main.py src/shain_utils.py src/app_shain_daicho.py
python -m compileall src main.py examples
```

## Architecture

The application has two entry points backed by a single core library:

```
main.py                     ← CLI entry point (delegates to ShainDaicho)
src/
  shain_utils.py            ← ShainDaicho class: all business logic, data parsing, export
  app_shain_daicho.py       ← Streamlit dashboard (imports ShainDaicho from shain_utils)
  config.yaml               ← Sheet names, column names, thresholds (reference only — not
                               loaded at runtime; constants are hardcoded in shain_utils.py)
tests/
  test_shain_daicho.py      ← unittest tests; builds a real .xlsx in a temp dir via setUpClass
examples/
  example_usage.py          ← Usage demonstrations
```

### ShainDaicho class (`src/shain_utils.py`)

Central class. Workflow: instantiate → call `load()` → call query methods.

- **Data model**: Reads 4 Excel sheets as DataFrames: `DBGenzaiX` (派遣社員/dispatch), `DBUkeoiX` (請負社員/contract), `DBStaffX` (スタッフ/staff), `DBTaishaX` (退社者/former, optional).
- **Active employee detection**: 派遣 and 請負 filter on column `現在 == '在職中'`; Staff filter on `入社日.notna() AND 退社日.isna()`.
- **Key column names** (Japanese): `社員№`, `氏名`, `現在`, `派遣先`, `ビザ期限`, `ビザ種類`, `時給`, `請求単価`, `差額利益`, `国籍`, `年齢`.
- **Profit calculation**: `COMPANY_BURDEN_RATE = 0.1576`; net profit = `請求単価 − 時給 − (時給 × 0.1576)`.
- **Visa alert levels**: EXPIRED (≤0d), URGENT (≤30d), WARNING (≤60d), UPCOMING (≤`days` param, default 90).
- **Guard pattern**: every public method calls `_ensure_loaded()` before accessing DataFrames.
- **Data coercion**: always use `pd.to_numeric(..., errors='coerce')` and `pd.to_datetime(..., errors='coerce')` for messy Excel data.

### Streamlit app (`src/app_shain_daicho.py`)

- Uses `@st.cache_resource` to avoid reloading on each interaction.
- Imports `ShainDaicho` directly from `shain_utils` (no package install needed; `sys.path` is adjusted by the CLI entry points).
- Tab-based layout with Dashboard, Search, Visa Alerts, Salary Analysis, and Export sections.

### config.yaml

Documents sheet/column names and thresholds for human reference. The constants in `ShainDaicho` (e.g., `SHEET_GENZAI = 'DBGenzaiX'`) must be kept in sync with this file when sheet names change.

## Key Constraints

- `src/shain_utils.py` is the contract boundary — preserve public method signatures and return shapes.
- CLI command names (`summary`, `active`, `visa-alerts`, `search`, `export`) must remain stable.
- No `pyproject.toml`, `pytest.ini`, or `ruff.toml` exist; do not assume pytest or ruff are available.
- See `AGENTS.md` for code style, naming conventions, and Pandas/Streamlit patterns.
- After completing a requested change, create a commit and push it unless the user explicitly asks not to.
