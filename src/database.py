#!/usr/bin/env python3
"""
UNS 社員台帳 — SQLite Database Backend  (v2 — full CRUD, audit log, soft-delete)

Key design decisions
────────────────────
• Per-call connections (thread-safe for Streamlit multi-session).
• WAL mode + busy_timeout=5000 ms for concurrent LAN access.
• Soft-delete: records gain a `deleted_at` timestamp; hard-delete is admin-only.
• Audit log: every write (INSERT/UPDATE/DELETE/RESTORE) is journaled.
• Schema migration: safe to run init_db() on an existing DB (ALTER TABLE IF missing).
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Column definitions (matches real Excel sheets exactly)
# ─────────────────────────────────────────────────────────────────────────────

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

# Field classification
DATE_COLS = {
    "生年月日", "ビザ期限", "入居", "入社日", "退社日", "退去",
    "免許期限", "任意保険期限",
}

NUMERIC_COLS = {
    "社員№", "年齢", "時給", "時給改定", "請求単価", "請求改定", "差額利益",
    "標準報酬", "健康保険", "介護保険", "厚生年金", "通勤距離", "交通費",
    "派遣先ID", "支店番号",
}

# Grouped display schema for detail forms
GENZAI_GROUPS: Dict[str, List[str]] = {
    "基本情報":  ["現在", "社員№", "氏名", "カナ", "性別", "国籍", "生年月日", "年齢"],
    "就業情報":  ["派遣先ID", "派遣先", "配属先", "配属ライン", "仕事内容",
                  "入社日", "退社日", "現入社", "入社依頼"],
    "給与情報":  ["時給", "時給改定", "請求単価", "請求改定", "差額利益"],
    "社会保険":  ["標準報酬", "健康保険", "介護保険", "厚生年金", "社保加入"],
    "ビザ・免許": ["ビザ期限", "ビザ種類", "免許種類", "免許期限",
                   "日本語検定", "キャリアアップ5年目"],
    "住所・居住": ["〒", "住所", "ｱﾊﾟｰﾄ", "入居", "退去"],
    "その他":    ["通勤方法", "任意保険期限", "備考"],
}

UKEOI_GROUPS: Dict[str, List[str]] = {
    "基本情報":  ["現在", "社員№", "氏名", "カナ", "性別", "国籍", "生年月日", "年齢"],
    "就業情報":  ["請負業務", "入社日", "退社日", "入社依頼"],
    "給与情報":  ["時給", "時給改定", "差額利益", "交通費", "通勤距離"],
    "社会保険":  ["標準報酬", "健康保険", "介護保険", "厚生年金", "社保加入"],
    "ビザ":      ["ビザ期限", "ビザ種類"],
    "住所・居住": ["〒", "住所", "ｱﾊﾟｰﾄ", "入居", "退去"],
    "口座情報":  ["口座名義", "銀行名", "支店番号", "支店名", "口座番号"],
    "その他":    ["備考"],
}

STAFF_GROUPS: Dict[str, List[str]] = {
    "基本情報":  ["現在", "社員№", "氏名", "カナ", "性別", "国籍", "生年月日", "年齢"],
    "就業情報":  ["事務所", "入社日", "退社日", "配偶者"],
    "社会保険":  ["社保加入", "雇用保険"],
    "ビザ":      ["ビザ期限", "ビザ種類"],
    "住所":      ["〒", "住所", "建物名"],
    "口座・連絡": ["銀行", "支店", "口座番号", "名義", "携帯電話", "携帯代行"],
}

TABLE_GROUPS = {
    "genzai": GENZAI_GROUPS,
    "ukeoi":  UKEOI_GROUPS,
    "staff":  STAFF_GROUPS,
}

# Default columns shown in the quick table (8-10 per type)
DEFAULT_VISIBLE: Dict[str, List[str]] = {
    "genzai": ["現在", "社員№", "氏名", "カナ", "派遣先", "時給", "請求単価", "差額利益", "ビザ期限", "入社日"],
    "ukeoi":  ["現在", "社員№", "氏名", "カナ", "請負業務", "時給", "差額利益", "ビザ期限", "入社日"],
    "staff":  ["現在", "社員№", "氏名", "カナ", "事務所", "ビザ期限", "入社日", "退社日"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _q(col: str) -> str:
    """Return a double-quoted column name safe for SQLite."""
    return f'"{col}"'


def _excel_date_to_iso(value: Any) -> Optional[str]:
    """Convert various date representations to YYYY-MM-DD string."""
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        if pd.isna(value):
            return None
        return value.strftime("%Y-%m-%d")
    try:
        n = float(value)
        if n == 0:
            return None
        dt = pd.Timestamp("1899-12-30") + pd.Timedelta(days=n)
        return dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        try:
            ts = pd.to_datetime(str(value), errors="raise")
            return ts.strftime("%Y-%m-%d")
        except Exception:
            return None


def _clean(col: str, value: Any) -> Optional[str]:
    """Coerce an Excel cell value to a storable string (None → SQL NULL)."""
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    sv = str(value).strip()
    if sv in ("0", "nan", "NaT", "None", "NaN", ""):
        return None
    if col in DATE_COLS:
        return _excel_date_to_iso(value)
    if col in NUMERIC_COLS:
        try:
            f = float(value)
            if np.isnan(f):
                return None
            return str(int(f)) if f == int(f) else str(f)
        except (TypeError, ValueError):
            pass
    return sv


# ─────────────────────────────────────────────────────────────────────────────
# ShainDatabase
# ─────────────────────────────────────────────────────────────────────────────

class ShainDatabase:
    """
    SQLite backend for 社員台帳 with full CRUD, soft-delete, and audit log.

    Thread safety: every public method opens its own connection (WAL mode
    allows unlimited concurrent readers + one writer at a time).
    """

    COMPANY_BURDEN_RATE = 0.1576
    _ALL_TABLES = ("genzai", "ukeoi", "staff")

    def __init__(self, db_path: str = "data/shain_daicho.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Connection ────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Open a new WAL-mode connection. Caller must close it."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Schema ────────────────────────────────────────────────────────────

    def init_db(self) -> None:
        """Create tables + run schema migrations. Safe to call repeatedly."""
        with self._get_conn() as conn:
            for table, cols in [
                ("genzai", GENZAI_COLS),
                ("ukeoi",  UKEOI_COLS),
                ("staff",  STAFF_COLS),
            ]:
                col_defs = ", ".join(f'{_q(c)} TEXT' for c in cols)
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        {col_defs},
                        deleted_at TEXT DEFAULT NULL,
                        updated_at TEXT DEFAULT (datetime('now','localtime'))
                    )
                """)

            # Audit log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name  TEXT NOT NULL,
                    row_id      INTEGER,
                    action      TEXT NOT NULL,
                    employee_name TEXT,
                    changes     TEXT,
                    changed_at  TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.commit()

        # Migration: add columns that may be absent in older DBs
        self._migrate()
        logger.info("DB schema ready: %s", self.db_path)

    def _migrate(self) -> None:
        """Add any missing columns to existing tables (idempotent)."""
        conn = self._get_conn()
        try:
            for table in self._ALL_TABLES:
                existing = {
                    r["name"]
                    for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
                }
                for col in ("deleted_at", "updated_at"):
                    if col not in existing:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {_q(col)} TEXT DEFAULT NULL")
            conn.commit()
        finally:
            conn.close()

    def _table_cols(self, table: str) -> List[str]:
        return {"genzai": GENZAI_COLS, "ukeoi": UKEOI_COLS, "staff": STAFF_COLS}[table]

    # ── Import ────────────────────────────────────────────────────────────

    def import_from_excel(
        self,
        excel_path: str,
        progress_callback=None,
    ) -> Dict[str, int]:
        """
        Truncate + re-import all 3 sheets from .xlsm.
        Existing soft-deleted records are also wiped (fresh start).
        Returns {table: row_count}.
        """
        path = Path(excel_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        def _prog(msg: str, frac: float):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg, frac)

        counts: Dict[str, int] = {}
        sheet_map = [
            ("DBGenzaiX", "genzai", GENZAI_COLS, "派遣社員"),
            ("DBUkeoiX",  "ukeoi",  UKEOI_COLS,  "請負社員"),
            ("DBStaffX",  "staff",  STAFF_COLS,   "スタッフ"),
        ]

        conn = self._get_conn()
        try:
            for i, (sheet, table, cols, label) in enumerate(sheet_map):
                _prog(f"{label} 読み込み中…", i / len(sheet_map))
                try:
                    df = pd.read_excel(path, sheet_name=sheet, dtype=str)
                except Exception as exc:
                    logger.warning("Sheet %s missing: %s", sheet, exc)
                    counts[table] = 0
                    continue

                # Remap first column of staff sheet
                if table == "staff" and df.columns[0] != "現在":
                    df = df.rename(columns={df.columns[0]: "現在"})

                # Drop calculated-only columns
                for drop_col in ("ｱﾗｰﾄ(ﾋﾞｻﾞ更新)",):
                    if drop_col in df.columns:
                        df = df.drop(columns=[drop_col])

                conn.execute(f"DELETE FROM {table}")

                active = [c for c in cols if c in df.columns]
                col_list = ", ".join(_q(c) for c in active)
                ph = ", ".join("?" for _ in active)
                inserted = 0

                for _, row in df.iterrows():
                    vals = [_clean(c, row.get(c)) for c in active]
                    if all(v is None for v in vals):
                        continue
                    conn.execute(
                        f"INSERT INTO {table} ({col_list}, updated_at) "
                        f"VALUES ({ph}, datetime('now','localtime'))",
                        vals,
                    )
                    inserted += 1

                conn.commit()
                counts[table] = inserted
                _prog(f"✅ {label}: {inserted} 件", (i + 1) / len(sheet_map))

            # Log import event
            conn.execute(
                "INSERT INTO audit_log (table_name, action, employee_name, changes) VALUES (?,?,?,?)",
                ("*", "IMPORT", "system",
                 json.dumps(counts, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

        return counts

    def preview_excel(self, excel_path: str) -> Dict[str, Any]:
        """Parse Excel and return counts + sample rows (no DB write)."""
        path = Path(excel_path)
        result: Dict[str, Any] = {}
        sheet_map = [
            ("DBGenzaiX", "genzai", "派遣社員"),
            ("DBUkeoiX",  "ukeoi",  "請負社員"),
            ("DBStaffX",  "staff",  "スタッフ"),
        ]
        for sheet, table, label in sheet_map:
            try:
                df = pd.read_excel(path, sheet_name=sheet, dtype=str)
                if table == "staff" and df.columns[0] != "現在":
                    df = df.rename(columns={df.columns[0]: "現在"})
                result[table] = {
                    "label": label,
                    "rows": len(df),
                    "sample": df.head(5).to_dict("records"),
                    "columns": list(df.columns),
                }
            except Exception as exc:
                result[table] = {"label": label, "rows": 0, "error": str(exc)}
        return result

    # ── Read ──────────────────────────────────────────────────────────────

    def get_all(
        self,
        table: str,
        active_only: bool = False,
        include_deleted: bool = False,
    ) -> pd.DataFrame:
        """Return rows as DataFrame. By default excludes soft-deleted rows."""
        conn = self._get_conn()
        try:
            clauses = []
            if not include_deleted:
                clauses.append("deleted_at IS NULL")
            if active_only:
                if table in ("genzai", "ukeoi"):
                    clauses.append('"現在" = \'在職中\'')
                elif table == "staff":
                    clauses.append('"入社日" IS NOT NULL AND "退社日" IS NULL')

            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            return pd.read_sql_query(f"SELECT * FROM {table} {where}", conn)
        finally:
            conn.close()

    def get_deleted(self, table: str) -> pd.DataFrame:
        """Return soft-deleted rows."""
        conn = self._get_conn()
        try:
            return pd.read_sql_query(
                f"SELECT * FROM {table} WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC",
                conn,
            )
        finally:
            conn.close()

    def get_employee(self, table: str, row_id: int) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ── Create ────────────────────────────────────────────────────────────

    def add_employee(self, table: str, data: Dict) -> int:
        cols = self._table_cols(table)
        valid = {k: _clean(k, v) for k, v in data.items() if k in cols}
        col_list = ", ".join(_q(k) for k in valid)
        ph = ", ".join("?" for _ in valid)
        values = list(valid.values())
        name = valid.get("氏名", "")

        conn = self._get_conn()
        try:
            cur = conn.execute(
                f"INSERT INTO {table} ({col_list}, updated_at) "
                f"VALUES ({ph}, datetime('now','localtime'))",
                values,
            )
            new_id = cur.lastrowid
            conn.execute(
                "INSERT INTO audit_log (table_name, row_id, action, employee_name, changes) VALUES (?,?,?,?,?)",
                (table, new_id, "INSERT", name,
                 json.dumps({k: str(v) for k, v in valid.items()}, ensure_ascii=False)),
            )
            conn.commit()
            return new_id
        finally:
            conn.close()

    # ── Update ────────────────────────────────────────────────────────────

    def update_employee(self, table: str, row_id: int, data: Dict) -> bool:
        cols = self._table_cols(table)
        valid = {k: _clean(k, v) for k, v in data.items() if k in cols}
        if not valid:
            return False

        # Capture old values for audit
        old = self.get_employee(table, row_id) or {}
        changed = {
            k: {"old": str(old.get(k, "")), "new": str(v)}
            for k, v in valid.items()
            if str(old.get(k, "")) != str(v or "")
        }

        set_clause = ", ".join(f"{_q(k)} = ?" for k in valid)
        values = list(valid.values()) + [row_id]
        name = old.get("氏名", "")

        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE {table} SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?",
                values,
            )
            if changed:
                conn.execute(
                    "INSERT INTO audit_log (table_name, row_id, action, employee_name, changes) VALUES (?,?,?,?,?)",
                    (table, row_id, "UPDATE", name,
                     json.dumps(changed, ensure_ascii=False)),
                )
            conn.commit()
            return True
        finally:
            conn.close()

    # ── Soft Delete / Restore ─────────────────────────────────────────────

    def delete_employee(self, table: str, row_id: int) -> bool:
        """Soft-delete: set deleted_at timestamp (recoverable)."""
        emp = self.get_employee(table, row_id)
        name = emp.get("氏名", "") if emp else ""
        conn = self._get_conn()
        try:
            cur = conn.execute(
                f"UPDATE {table} SET deleted_at = datetime('now','localtime') WHERE id = ?",
                (row_id,),
            )
            conn.execute(
                "INSERT INTO audit_log (table_name, row_id, action, employee_name) VALUES (?,?,?,?)",
                (table, row_id, "DELETE", name),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def restore_employee(self, table: str, row_id: int) -> bool:
        """Restore a soft-deleted record."""
        emp = self.get_employee(table, row_id)
        name = emp.get("氏名", "") if emp else ""
        conn = self._get_conn()
        try:
            cur = conn.execute(
                f"UPDATE {table} SET deleted_at = NULL, "
                f"updated_at = datetime('now','localtime') WHERE id = ?",
                (row_id,),
            )
            conn.execute(
                "INSERT INTO audit_log (table_name, row_id, action, employee_name) VALUES (?,?,?,?)",
                (table, row_id, "RESTORE", name),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def hard_delete_employee(self, table: str, row_id: int) -> bool:
        """Permanently delete a record (admin-only, irreversible)."""
        emp = self.get_employee(table, row_id)
        name = emp.get("氏名", "") if emp else ""
        conn = self._get_conn()
        try:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
            conn.execute(
                "INSERT INTO audit_log (table_name, row_id, action, employee_name) VALUES (?,?,?,?)",
                (table, row_id, "HARD_DELETE", name),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    # ── Audit Log ─────────────────────────────────────────────────────────

    def get_audit_log(
        self,
        table: Optional[str] = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        conn = self._get_conn()
        try:
            if table:
                q = "SELECT * FROM audit_log WHERE table_name = ? ORDER BY changed_at DESC LIMIT ?"
                return pd.read_sql_query(q, conn, params=(table, limit))
            else:
                q = "SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT ?"
                return pd.read_sql_query(q, conn, params=(limit,))
        finally:
            conn.close()

    # ── Stats ─────────────────────────────────────────────────────────────

    def get_summary_stats(self) -> Dict:
        conn = self._get_conn()
        try:
            result = {}
            for table, label, status_col in [
                ("genzai", "派遣社員", "現在"),
                ("ukeoi",  "請負社員", "現在"),
                ("staff",  "スタッフ",  None),
            ]:
                total = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NULL"
                ).fetchone()[0]
                if status_col:
                    active = conn.execute(
                        f'SELECT COUNT(*) FROM {table} WHERE "現在" = ? AND deleted_at IS NULL',
                        ("在職中",),
                    ).fetchone()[0]
                else:
                    active = conn.execute(
                        f'SELECT COUNT(*) FROM {table} '
                        f'WHERE "入社日" IS NOT NULL AND "退社日" IS NULL AND deleted_at IS NULL'
                    ).fetchone()[0]
                result[label] = {"total": total, "active": active, "retired": total - active}

            totals = {k: sum(v[k] for v in result.values()) for k in ("total", "active", "retired")}
            result["total"] = totals
            return result
        finally:
            conn.close()

    def get_visa_alerts(self, days: int = 90) -> List[Dict]:
        today = datetime.now()
        cutoff = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        alerts: List[Dict] = []
        conn = self._get_conn()
        try:
            for table, label, status_col in [
                ("genzai", "派遣", "現在"),
                ("ukeoi",  "請負", "現在"),
                ("staff",  "スタッフ", None),
            ]:
                where_status = f' AND "現在" = \'在職中\'' if status_col else ""
                rows = conn.execute(
                    f"""
                    SELECT id, "社員№", "氏名", "ビザ種類", "ビザ期限"
                    FROM {table}
                    WHERE "ビザ期限" IS NOT NULL
                      AND "ビザ期限" != ''
                      AND "ビザ期限" <= ?
                      AND deleted_at IS NULL
                      {where_status}
                    ORDER BY "ビザ期限"
                    """,
                    (cutoff,),
                ).fetchall()

                for row in rows:
                    try:
                        expiry = datetime.strptime(row["ビザ期限"][:10], "%Y-%m-%d")
                        days_left = (expiry - today).days
                    except (ValueError, TypeError):
                        continue

                    if days_left <= 0:
                        level, cls = "🔴 期限切れ", "expired"
                    elif days_left <= 30:
                        level, cls = "🔴 緊急", "urgent"
                    elif days_left <= 60:
                        level, cls = "🟠 警告", "warning"
                    else:
                        level, cls = "🟡 注意", "upcoming"

                    alerts.append({
                        "id": row["id"],
                        "category": label,
                        "table": table,
                        "employee_id": row["社員№"],
                        "name": row["氏名"] or "—",
                        "visa_type": row["ビザ種類"] or "—",
                        "expiry_date": row["ビザ期限"][:10],
                        "days_left": days_left,
                        "alert_level": level,
                        "alert_class": cls,
                    })
        finally:
            conn.close()

        alerts.sort(key=lambda x: x["days_left"])
        return alerts

    def get_nationality_breakdown(self) -> Dict:
        conn = self._get_conn()
        try:
            result: Dict[str, Dict[str, int]] = {}
            for table, label in [("genzai", "派遣"), ("ukeoi", "請負"), ("staff", "スタッフ")]:
                rows = conn.execute(
                    f'SELECT "国籍", COUNT(*) cnt FROM {table} '
                    f'WHERE "国籍" IS NOT NULL AND deleted_at IS NULL '
                    f'GROUP BY "国籍" ORDER BY cnt DESC'
                ).fetchall()
                result[label] = {r["国籍"]: r["cnt"] for r in rows}
            return result
        finally:
            conn.close()

    def get_hakensaki_breakdown(self, top_n: int = 15) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                f'SELECT "派遣先", COUNT(*) cnt FROM genzai '
                f'WHERE "派遣先" IS NOT NULL AND deleted_at IS NULL '
                f'GROUP BY "派遣先" ORDER BY cnt DESC LIMIT ?',
                (top_n,),
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) FROM genzai WHERE deleted_at IS NULL"
            ).fetchone()[0] or 1
            return [
                {"company": r["派遣先"], "count": r["cnt"],
                 "percentage": round(r["cnt"] / total * 100, 1)}
                for r in rows
            ]
        finally:
            conn.close()

    def has_data(self) -> bool:
        conn = self._get_conn()
        try:
            for table in self._ALL_TABLES:
                if conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NULL"
                ).fetchone()[0] > 0:
                    return True
            return False
        finally:
            conn.close()

    def db_info(self) -> Dict:
        conn = self._get_conn()
        try:
            info: Dict[str, Any] = {"path": str(self.db_path), "tables": {}}
            for table in self._ALL_TABLES:
                live = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NULL"
                ).fetchone()[0]
                deleted = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NOT NULL"
                ).fetchone()[0]
                latest = conn.execute(
                    f"SELECT MAX(updated_at) FROM {table}"
                ).fetchone()[0]
                info["tables"][table] = {
                    "rows": live, "deleted": deleted, "last_updated": latest
                }
            return info
        finally:
            conn.close()
