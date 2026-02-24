# AGENTS.md
Guidance for coding agents working in `UNS-Shain-Daicho-Manager`.
This file is based on the current repository state.

## Project overview
- Language: Python 3.8+
- Main logic: `src/shain_utils.py`
- Web app: `src/app_shain_daicho.py` (Streamlit)
- CLI entrypoints: `main.py`, `src/shain_utils.py`
- Example script: `examples/example_usage.py`
- Dependencies: `requirements.txt`

## Setup
Run from repository root.

```bash
python -m venv .venv
```

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

## Build / lint / test / run commands
No formal build system or committed lint/test config is present (`pyproject.toml`, `pytest.ini`, `tox.ini`, `ruff.toml` are absent).

### Run CLI
```bash
python main.py <path-to-xlsm> <command>
python src/shain_utils.py <path-to-xlsm> <command>
```

Examples:
```bash
python main.py "data.xlsm" summary
python main.py "data.xlsm" visa-alerts
python main.py "data.xlsm" search NGUYEN
python main.py "data.xlsm" export excel
```

### Run web app
```bash
streamlit run src/app_shain_daicho.py
```

### Practical pre-PR validation
```bash
python -m compileall src main.py examples
python src/shain_utils.py "<path-to-xlsm>" summary
python src/shain_utils.py "<path-to-xlsm>" visa-alerts
streamlit run src/app_shain_daicho.py
```

Stop Streamlit after basic tab smoke checks.

### Lint fallback (until tooling is added)
```bash
python -m py_compile main.py src/shain_utils.py src/app_shain_daicho.py
```

## Testing guidance (including single-test commands)
- Current tests: `tests/test_shain_daicho.py` (unittest).
- Test data is generated dynamically in tests; no fixture file is required.

Run all tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Run one test file:
```bash
python -m unittest tests.test_shain_daicho
```

Run one test class:
```bash
python -m unittest tests.test_shain_daicho.TestShainDaicho
```

Run one test method:
```bash
python -m unittest tests.test_shain_daicho.TestShainDaicho.test_search_employee_case_insensitive
```

If project later adopts `pytest`:
```bash
pytest tests/test_shain_daicho.py::TestShainDaicho::test_search_employee_case_insensitive
```

## Code style guidelines
Baseline: follow PEP 8, existing code patterns, and `docs/CONTRIBUTING.md`.

### Imports
- Order imports as standard library, third-party, then local modules.
- Keep imports explicit and readable.
- Avoid `sys.path` edits outside entry scripts and isolated examples.

### Formatting
- Use 4 spaces; no tabs.
- Keep functions focused; extract helpers when blocks get long.
- Add docstrings for public classes/functions.
- Keep lines readable (target around 88-100 chars unless nearby code differs).

### Types and signatures
- Add type hints for new/changed public functions.
- Use consistent typing forms (`Optional`, `Union`, `Dict`, `List`).
- Preserve existing return shapes unless API changes are requested.

### Naming
- Classes: `CamelCase`.
- Functions/methods/variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- DataFrame names should remain descriptive (`df_genzai`, `active_staff`, etc.).

### Error handling and logging
- Wrap file I/O and parsing in `try/except`.
- Log with module logger; do not swallow exceptions silently.
- For recoverable failures, return safe defaults consistent with current APIs (`[]`, `{}`, `None`).
- Use precondition checks like `_ensure_loaded()` before accessing data.

### Pandas and data handling
- Validate required columns before transformations.
- Prefer coercive conversions for messy data:
  - `pd.to_numeric(..., errors="coerce")`
  - `pd.to_datetime(..., errors="coerce")`
- Copy filtered DataFrames before mutating.
- Keep sheet and column expectations aligned with constants and `src/config.yaml`.

### Streamlit patterns
- Keep heavy loaders cached via `@st.cache_resource`.
- Surface user-visible issues with `st.error` / `st.warning`.
- Preserve current tab-based UX unless a refactor is explicitly requested.

### CLI conventions
- Keep command names stable: `summary`, `active`, `visa-alerts`, `search`, `export`.
- Show help text when args are missing.
- Exit non-zero on hard failures.

## Sensitive areas
- `src/shain_utils.py`: business logic and output contracts.
- `src/app_shain_daicho.py`: user workflows and export behavior.
- `src/config.yaml`: keep keys backward-compatible unless migration is included.

## Cursor and Copilot instructions
Checked and not found in this repo:
- `.cursorrules`
- `.cursor/rules/`
- `.github/copilot-instructions.md`

If any of these files are added later, treat them as higher-priority agent instructions and update this file.

## Agent workflow expectations
- Prefer minimal diffs over broad rewrites.
- Avoid breaking CLI behavior unless requested.
- If you add lint/test tooling, document exact commands here.
- Run at least one relevant runtime check before handoff.
- Repository owner preference: after completing a requested change, create a commit and push it unless the user explicitly asks not to push.

## Documentation freshness rule
- Before implementing non-trivial changes, check current upstream guidance in Context7 when available.
- Prefer repository conventions first; use Context7 to validate modern patterns and avoid outdated advice.
- In handoff notes, mention when recommendations were cross-checked against Context7.

## React / Next.js / Vercel best-practice rule
- For frontend work, follow React and Next.js best practices for server/client boundaries, data fetching, caching, and routing.
- Prefer Next.js App Router patterns unless the existing project clearly uses Pages Router.
- Keep Vercel deployment compatibility in mind (environment variables, edge/node runtime constraints, build output).
- Favor incremental, production-safe changes and include verification steps for local run/build.
