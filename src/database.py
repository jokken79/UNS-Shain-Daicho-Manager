#!/usr/bin/env python3
"""
UNS 社員台帳 — SQLite Database Backend
Provides full CRUD for genzai (派遣), ukeoi (請負), and staff (スタッフ) tables.

Usage:
    from database import ShainDatabase
    db = ShainDatabase('data/shain_daicho.db')
    db.init_db()

    # One-time import from Excel
    db.import_from_excel('path/to/社員台帳.xlsm')

    # Query
    df = db.get_all('genzai', active_only=True)

    # CRUD
    new_id = db.add_employee('genzai', {'氏名': '山田 太郎', ...})
    db.update_employee('genzai', new_id, {'時給': 1200})
    db.delete_employee('genzai', new_id)
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column definitions (matches actual Excel sheets)
# ---------------------------------------------------------------------------

GENZAI_COLS = [
    "現在", "社員№", "派遣先ID", "派遣先", "配属先", "配属ライン", "仕事内容",
    "氏名", "カナ", "性別", "国籍", "生年月日", "年齢", "時給", "時給改定",
    "請求単価", "請求改定", "差額利益", "標準報酬", "健康保険", "介護保険", "厚生年金",
    "ビザ期限", "ビザ種類", "〒", "住所", "ｱﾊﾟｰﾄ", "入居", "入社日", "退社日",
    "退去", "社保加入", "入社依頼", "備考", "現入社", "免許種類", "免許期限",
    "通勤方法", "任意保険期限", "日本語検定", "キャリアアップ5年目",
]

UKEOI_COLS = [
    "現在", "社員№", "請負業務", "氏名", "カナ", "性別", "国籍", "生年月日", "年齢",
    "時給", "時給改定", "標準報酬", "健康保険", "介護保険", "厚生年金", "通勤距離",
    "交通費", "差額利益", "ビザ期限", "ビザ種類", "〒", "住所", "ｱﾊﾟｰﾄ", "入居",
    "入社日", "退社日", "退去", "社保加入", "口座名義", "銀行名", "支店番号",
    "支店名", "口座番号", "入社依頼", "備考",
]

STAFF_COLS = [
    "現在", "社員№", "事務所", "氏名", "カナ", "性別", "国籍", "生年月日", "年齢",
    "ビザ期限", "ビザ種類", "配偶者", "〒", "住所", "建物名", "入社日", "退社日",
    "社保加入", "雇用保険", "携帯電話", "携帯代行", "銀行", "支店", "口座番号", "名義",
]

# Columns that store dates (ISO string in DB)
DATE_COLS = {"生年月日", "ビザ期限", "入居", "入社日", "退社日", "退去", "免許期限", "任意保険期限"}

# Columns that store numbers
NUMERIC_COLS = {
    "社員№", "年齢", "時給", "時給改定", "請求単価", "請求改定", "差額利益",
    "標準報酬", "健康保険", "介護保険", "厚生年金", "通勤距離", "交通費",
    "派遣先ID", "支店番号",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_col(col: str) -> str:
    """Quote column name for SQLite (handles Japanese + special chars)."""
    return f'"{col}"'


def _cols_ddl(cols: List[str]) -> str:
    """Build column definition string for CREATE TABLE."""
    return ", ".join(f'{_safe_col(c)} TEXT' for c in cols)


def _excel_date_to_iso(value: Any) -> Optional[str]:
    """Convert Excel serial date number or pd.Timestamp to ISO date string."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        if pd.isna(value):
            return None
        return value.strftime("%Y-%m-%d")
    try:
        n = float(value)
        if n == 0:
            return None
        # Excel serial date: days since 1899-12-30
        dt = pd.Timestamp("1899-12-30") + pd.Timedelta(days=n)
        return dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        # Try parsing as string
        try:
            ts = pd.to_datetime(str(value), errors="raise")
            return ts.strftime("%Y-%m-%d")
        except Exception:
            return None


def _clean_value(col: str, value: Any) -> Optional[str]:
    """Coerce a cell value to a storable string (or None for NULL)."""
    # Treat explicit "0" strings and NaN as NULL
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    str_val = str(value).strip()
    if str_val in ("0", "nan", "NaT", "None", ""):
        return None

    if col in DATE_COLS:
        return _excel_date_to_iso(value)

    if col in NUMERIC_COLS:
        try:
            f = float(value)
            if np.isnan(f):
                return None
            # Store as integer string when whole, else float
            return str(int(f)) if f == int(f) else str(f)
        except (TypeError, ValueError):
            pass

    return str_val if str_val else None


# ---------------------------------------------------------------------------
# ShainDatabase
# ---------------------------------------------------------------------------

class ShainDatabase:
    """SQLite-backed storage for 社員台帳 with full CRUD support."""

    DB_VERSION = 1
    COMPANY_BURDEN_RATE = 0.1576

    def __init__(self, db_path: str = "data/shain_daicho.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return a thread-local connection (lazy init)."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        for table, cols in [
            ("genzai", GENZAI_COLS),
            ("ukeoi", UKEOI_COLS),
            ("staff", STAFF_COLS),
        ]:
            col_defs = _cols_ddl(cols)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {col_defs},
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
        conn.commit()
        logger.info("Database schema initialised at %s", self.db_path)

    def _table_cols(self, table: str) -> List[str]:
        table_map = {"genzai": GENZAI_COLS, "ukeoi": UKEOI_COLS, "staff": STAFF_COLS}
        return table_map[table]

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_from_excel(
        self,
        excel_path: str,
        progress_callback=None,
    ) -> Dict[str, int]:
        """
        Import all 3 sheets from the .xlsm file into the database.
        Existing data is REPLACED (truncate-insert).

        progress_callback: optional callable(message: str, fraction: float)
        Returns dict with row counts per table.
        """
        path = Path(excel_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        def _progress(msg: str, frac: float):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, frac)

        conn = self._get_conn()
        counts: Dict[str, int] = {}

        sheet_map = [
            ("DBGenzaiX", "genzai", GENZAI_COLS, "派遣社員"),
            ("DBUkeoiX", "ukeoi", UKEOI_COLS, "請負社員"),
            ("DBStaffX", "staff", STAFF_COLS, "スタッフ"),
        ]

        for i, (sheet_name, table, cols, label) in enumerate(sheet_map):
            _progress(f"{label} シートを読み込み中…", i / len(sheet_map))
            try:
                df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
            except Exception as e:
                logger.warning("Could not read sheet %s: %s", sheet_name, e)
                counts[table] = 0
                continue

            # DBStaffX: first column may be "№" — remap to "現在"
            if table == "staff" and df.columns[0] != "現在":
                df = df.rename(columns={df.columns[0]: "現在"})

            # Drop formula-only column that doesn't survive import cleanly
            if "ｱﾗｰﾄ(ﾋﾞｻﾞ更新)" in df.columns:
                df = df.drop(columns=["ｱﾗｰﾄ(ﾋﾞｻﾞ更新)"])

            # Truncate existing data
            conn.execute(f"DELETE FROM {table}")

            inserted = 0
            col_list = ", ".join(_safe_col(c) for c in cols if c in df.columns)
            placeholders = ", ".join("?" for c in cols if c in df.columns)
            active_cols = [c for c in cols if c in df.columns]

            for _, row in df.iterrows():
                values = [_clean_value(c, row.get(c)) for c in active_cols]
                # Skip completely empty rows
                if all(v is None for v in values):
                    continue
                conn.execute(
                    f"INSERT INTO {table} ({col_list}, updated_at) VALUES ({placeholders}, datetime('now','localtime'))",
                    values,
                )
                inserted += 1

            conn.commit()
            counts[table] = inserted
            _progress(f"✅ {label}: {inserted} 件インポート完了", (i + 1) / len(sheet_map))

        logger.info("Import complete: %s", counts)
        return counts

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self, table: str, active_only: bool = False) -> pd.DataFrame:
        """Return all rows from a table as a DataFrame."""
        conn = self._get_conn()
        query = f"SELECT * FROM {table}"
        if active_only:
            if table in ("genzai", "ukeoi"):
                query += ' WHERE "現在" = \'在職中\''
            elif table == "staff":
                query += ' WHERE "入社日" IS NOT NULL AND "退社日" IS NULL'
        df = pd.read_sql_query(query, conn)
        return df

    def get_employee(self, table: str, row_id: int) -> Optional[Dict]:
        """Return a single row as a dict."""
        conn = self._get_conn()
        cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add_employee(self, table: str, data: Dict) -> int:
        """Insert a new employee record. Returns the new row id."""
        cols = self._table_cols(table)
        conn = self._get_conn()

        # Only insert known columns
        valid = {k: v for k, v in data.items() if k in cols}
        col_list = ", ".join(_safe_col(k) for k in valid)
        placeholders = ", ".join("?" for _ in valid)
        values = [_clean_value(k, v) for k, v in valid.items()]

        cur = conn.execute(
            f"INSERT INTO {table} ({col_list}, updated_at) VALUES ({placeholders}, datetime('now','localtime'))",
            values,
        )
        conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_employee(self, table: str, row_id: int, data: Dict) -> bool:
        """Update fields for a given row. Returns True on success."""
        cols = self._table_cols(table)
        conn = self._get_conn()

        valid = {k: v for k, v in data.items() if k in cols}
        if not valid:
            return False

        set_clause = ", ".join(f'{_safe_col(k)} = ?' for k in valid)
        values = [_clean_value(k, v) for k, v in valid.items()]
        values.append(row_id)

        conn.execute(
            f"UPDATE {table} SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?",
            values,
        )
        conn.commit()
        return True

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_employee(self, table: str, row_id: int) -> bool:
        """Hard-delete a row. Returns True on success."""
        conn = self._get_conn()
        cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Stats helpers (mirrors ShainDaicho API)
    # ------------------------------------------------------------------

    def get_summary_stats(self) -> Dict:
        """Return summary counts per table."""
        conn = self._get_conn()
        result = {}

        for table, label, status_col in [
            ("genzai", "派遣社員", "現在"),
            ("ukeoi", "請負社員", "現在"),
            ("staff", "スタッフ", None),
        ]:
            total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if status_col:
                active = conn.execute(
                    f'SELECT COUNT(*) FROM {table} WHERE "{status_col}" = ?', ("在職中",)
                ).fetchone()[0]
            else:
                active = conn.execute(
                    f'SELECT COUNT(*) FROM {table} WHERE "入社日" IS NOT NULL AND "退社日" IS NULL'
                ).fetchone()[0]
            result[label] = {"total": total, "active": active, "retired": total - active}

        totals = {k: sum(v[k] for v in result.values()) for k in ("total", "active", "retired")}
        result["total"] = totals
        return result

    def get_visa_alerts(self, days: int = 90) -> List[Dict]:
        """Return employees whose visa expires within `days` days."""
        conn = self._get_conn()
        today = datetime.now()
        cutoff = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        alerts: List[Dict] = []

        table_map = [
            ("genzai", "派遣", "現在"),
            ("ukeoi", "請負", "現在"),
            ("staff", "スタッフ", None),
        ]

        for table, label, status_col in table_map:
            where_status = f' AND "{status_col}" = \'在職中\'' if status_col else ""
            rows = conn.execute(
                f"""
                SELECT id, "社員№", "氏名", "ビザ種類", "ビザ期限"
                FROM {table}
                WHERE "ビザ期限" IS NOT NULL
                  AND "ビザ期限" <= ?
                  {where_status}
                ORDER BY "ビザ期限"
                """,
                (cutoff,),
            ).fetchall()

            for row in rows:
                expiry_str = row["ビザ期限"]
                try:
                    expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
                    days_left = (expiry - today).days
                except ValueError:
                    continue

                if days_left <= 0:
                    level = "🔴 EXPIRED"
                elif days_left <= 30:
                    level = "🔴 URGENT"
                elif days_left <= 60:
                    level = "🟠 WARNING"
                else:
                    level = "🟡 UPCOMING"

                alerts.append({
                    "id": row["id"],
                    "category": label,
                    "employee_id": row["社員№"],
                    "name": row["氏名"],
                    "visa_type": row["ビザ種類"] or "—",
                    "expiry_date": expiry_str,
                    "days_left": days_left,
                    "alert_level": level,
                })

        alerts.sort(key=lambda x: x["days_left"])
        return alerts

    def get_nationality_breakdown(self) -> Dict:
        """Return nationality counts per table."""
        conn = self._get_conn()
        result: Dict[str, Dict[str, int]] = {}
        for table, label in [("genzai", "派遣"), ("ukeoi", "請負"), ("staff", "スタッフ")]:
            rows = conn.execute(
                f'SELECT "国籍", COUNT(*) as cnt FROM {table} WHERE "国籍" IS NOT NULL GROUP BY "国籍" ORDER BY cnt DESC'
            ).fetchall()
            result[label] = {r["国籍"]: r["cnt"] for r in rows}
        return result

    def get_hakensaki_breakdown(self, top_n: int = 15) -> List[Dict]:
        """Return top dispatch companies."""
        conn = self._get_conn()
        rows = conn.execute(
            f'SELECT "派遣先", COUNT(*) as cnt FROM genzai WHERE "派遣先" IS NOT NULL GROUP BY "派遣先" ORDER BY cnt DESC LIMIT ?',
            (top_n,),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM genzai").fetchone()[0] or 1
        return [
            {"company": r["派遣先"], "count": r["cnt"], "percentage": round(r["cnt"] / total * 100, 1)}
            for r in rows
        ]

    def has_data(self) -> bool:
        """Return True if at least one table has rows."""
        conn = self._get_conn()
        for table in ("genzai", "ukeoi", "staff"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count > 0:
                return True
        return False

    def db_info(self) -> Dict:
        """Return metadata about the database."""
        conn = self._get_conn()
        info: Dict[str, Any] = {"path": str(self.db_path), "tables": {}}
        for table in ("genzai", "ukeoi", "staff"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            latest = conn.execute(
                f"SELECT MAX(updated_at) FROM {table}"
            ).fetchone()[0]
            info["tables"][table] = {"rows": count, "last_updated": latest}
        return info
