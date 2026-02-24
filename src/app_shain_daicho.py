#!/usr/bin/env python3
"""
UNS 社員台帳 Manager — v3  (Full CRUD + Audit + Soft-delete + Phase 1-2-3)
Streamlit application backed by ShainDatabase (SQLite WAL).

Navigation: sidebar (replaces flat 7-tab layout)
Pages: ホーム | 社員管理 | ビザアラート | 給与分析 | 監査ログ | 設定
"""

import json
import logging
import sys
import tempfile
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Path setup ──────────────────────────────────────────────────────────────
_src = Path(__file__).parent
_root = _src.parent
for _p in (str(_src), str(_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import (
    ShainDatabase,
    GENZAI_COLS, UKEOI_COLS, STAFF_COLS,
    TABLE_GROUPS, DEFAULT_VISIBLE,
    DATE_COLS, NUMERIC_COLS,
)

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UNS 社員台帳",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = str(_root / "data" / "shain_daicho.db")
COMPANY_BURDEN_RATE = 0.1576
ADMIN_PASSWORD = "uns2024"          # Change via ⚙️ 設定 → パスワード変更

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Japanese font */
html, body, [class*="st-"] {
    font-family: "Noto Sans JP","Hiragino Sans","Meiryo",sans-serif;
}

/* Sidebar nav */
[data-testid="stSidebar"] { background:#f8f9fa; border-right:1px solid #e0e0e0; }
[data-testid="stSidebar"] .stRadio > label { font-size:15px; font-weight:600; color:#555; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    font-size:14px; padding:6px 10px; border-radius:6px; margin:2px 0;
    display:block; cursor:pointer; transition:background 0.15s;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {background:#e8f0fe;}

/* Metric card accent */
div[data-testid="stMetric"] {
    background:#fafafa; padding:12px 16px;
    border-radius:8px; border-left:4px solid #1E88E5;
    box-shadow:0 1px 3px rgba(0,0,0,.06);
}

/* Table border */
div[data-testid="stDataFrame"] { border-radius:8px; border:1px solid #e0e0e0; }

/* Alert banner */
.alert-banner {
    padding:12px 16px; border-radius:8px;
    margin:8px 0; font-weight:600;
}
.banner-critical { background:#ffebee; border-left:5px solid #c62828; color:#b71c1c; }
.banner-warning  { background:#fff8e1; border-left:5px solid #f9a825; color:#6d4c00; }
.banner-info     { background:#e3f2fd; border-left:5px solid #1565c0; color:#0d47a1; }
.banner-ok       { background:#e8f5e9; border-left:5px solid #2e7d32; color:#1b5e20; }

/* Danger zone */
.danger-zone {
    background:#fff5f5; border:1px solid #ffcdd2;
    border-left:5px solid #c62828; padding:16px;
    border-radius:8px; margin:12px 0;
}

/* Form section header */
.form-section {
    font-size:13px; font-weight:700; color:#1565c0;
    text-transform:uppercase; letter-spacing:.05em;
    margin:16px 0 4px; padding-bottom:4px;
    border-bottom:2px solid #e3f2fd;
}

/* KPI badge */
.badge-red    { background:#ffebee; color:#c62828; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:700; }
.badge-orange { background:#fff3e0; color:#e65100; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:700; }
.badge-yellow { background:#fffde7; color:#f57f17; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:700; }
.badge-green  { background:#e8f5e9; color:#2e7d32; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ─── Cached DB resource ───────────────────────────────────────────────────────

@st.cache_resource
def get_db() -> ShainDatabase:
    db = ShainDatabase(DB_PATH)
    db.init_db()
    return db


@st.cache_data(ttl=5, show_spinner=False)
def fetch_all(db_path: str, table: str, active_only: bool = False) -> pd.DataFrame:
    return ShainDatabase(db_path).get_all(table, active_only)


@st.cache_data(ttl=5, show_spinner=False)
def fetch_summary(db_path: str) -> Dict:
    return ShainDatabase(db_path).get_summary_stats()


@st.cache_data(ttl=5, show_spinner=False)
def fetch_visa(db_path: str, days: int) -> List[Dict]:
    return ShainDatabase(db_path).get_visa_alerts(days)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_nationality(db_path: str) -> Dict:
    return ShainDatabase(db_path).get_nationality_breakdown()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_hakensaki(db_path: str, top_n: int = 10) -> List[Dict]:
    return ShainDatabase(db_path).get_hakensaki_breakdown(top_n)


def _invalidate_cache() -> None:
    """Clear all read caches after a write."""
    fetch_all.clear()
    fetch_summary.clear()
    fetch_visa.clear()
    fetch_nationality.clear()
    fetch_hakensaki.clear()


# ─── Helper utilities ─────────────────────────────────────────────────────────

def fmt_yen(v) -> str:
    try:
        return f"¥{int(float(v)):,}"
    except Exception:
        return "—"


def calc_age(bd_str: Optional[str]) -> Optional[int]:
    if not bd_str:
        return None
    try:
        bd = datetime.strptime(str(bd_str)[:10], "%Y-%m-%d").date()
        t = date.today()
        return t.year - bd.year - ((t.month, t.day) < (bd.month, bd.day))
    except Exception:
        return None


def calc_profit(seikyu, jikyu) -> Optional[float]:
    try:
        s, j = float(seikyu), float(jikyu)
        return s - j - j * COMPANY_BURDEN_RATE
    except Exception:
        return None


def _date_val(v) -> Optional[date]:
    """Parse any date value to a Python date (or None)."""
    if v is None or str(v).strip() in ("", "None", "nan", "NaT"):
        return None
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def is_admin() -> bool:
    return st.session_state.get("_role") == "admin"


def _toast(msg: str, icon: str = "✅") -> None:
    """Show a toast notification (Streamlit >= 1.29) with fallback."""
    try:
        st.toast(msg, icon=icon)
    except AttributeError:
        st.success(f"{icon} {msg}")


# ─── Column config builder ────────────────────────────────────────────────────

def _col_cfg(col: str, editable: bool = True) -> Any:
    """Return a Streamlit column_config object for the given column."""
    disabled = not editable
    if col in ("id", "updated_at", "deleted_at", "年齢"):
        return st.column_config.TextColumn(col, disabled=True, width="small")
    if col == "現在":
        return st.column_config.SelectboxColumn(
            col, options=["在職中", "退社", "休職"], disabled=disabled, width="small"
        )
    if col == "性別":
        return st.column_config.SelectboxColumn(
            col, options=["男", "女"], disabled=disabled, width="small"
        )
    if col in NUMERIC_COLS - {"社員№", "年齢", "派遣先ID"}:
        return st.column_config.NumberColumn(col, format="¥%d" if col in
            {"時給", "時給改定", "請求単価", "請求改定", "差額利益",
             "標準報酬", "健康保険", "介護保険", "厚生年金", "交通費"}
            else "%g",
            disabled=disabled,
        )
    if col in DATE_COLS:
        return st.column_config.DateColumn(col, format="YYYY-MM-DD", disabled=disabled)
    return st.column_config.TextColumn(col, disabled=disabled)


# ─── Field widget renderer ────────────────────────────────────────────────────

def _field_widget(col: str, cur_val, key: str, disabled: bool = False):
    """Render the appropriate input widget for a column and return its value."""
    if col in DATE_COLS:
        dv = _date_val(cur_val)
        return st.date_input(col, value=dv, key=key, disabled=disabled)
    if col == "現在":
        opts = ["在職中", "退社", "休職"]
        idx = opts.index(cur_val) if cur_val in opts else 0
        return st.selectbox(col, opts, index=idx, key=key, disabled=disabled)
    if col == "性別":
        opts = ["男", "女"]
        idx = opts.index(cur_val) if cur_val in opts else 0
        return st.selectbox(col, opts, index=idx, key=key, disabled=disabled)
    if col in {"時給", "時給改定", "請求単価", "請求改定", "標準報酬",
               "健康保険", "介護保険", "厚生年金", "交通費", "通勤距離"}:
        try:
            nv = float(cur_val) if cur_val else 0.0
        except Exception:
            nv = 0.0
        return st.number_input(col, value=nv, step=10.0, min_value=0.0, key=key, disabled=disabled)
    if col == "年齢":
        st.text_input(col, value=str(cur_val or ""), key=key, disabled=True)
        return cur_val
    return st.text_input(col, value=str(cur_val or ""), key=key, disabled=disabled)


# ─── Detail form (grouped) ────────────────────────────────────────────────────

def render_detail_form(
    emp: Dict,
    table: str,
    key_prefix: str,
    disabled: bool = False,
) -> Dict:
    """
    Render a full grouped form pre-filled with emp data.
    Returns dict of field → new value.
    """
    groups = TABLE_GROUPS[table]
    updated: Dict = {}

    for group_name, fields in groups.items():
        with st.expander(f"📂 {group_name}", expanded=(group_name == list(groups.keys())[0])):
            cols = st.columns(3)
            for i, col_name in enumerate(fields):
                with cols[i % 3]:
                    val = emp.get(col_name)
                    result = _field_widget(
                        col_name, val,
                        key=f"{key_prefix}_det_{col_name}",
                        disabled=disabled,
                    )
                    if col_name != "年齢":
                        updated[col_name] = result
    return updated


# ─── Unsaved changes detection ────────────────────────────────────────────────

def _has_unsaved(key_prefix: str) -> bool:
    """Check if st.data_editor has pending changes via its session_state key."""
    editor_state = st.session_state.get(f"{key_prefix}_editor")
    if not editor_state:
        return False
    return bool(
        editor_state.get("edited_rows") or
        editor_state.get("added_rows") or
        editor_state.get("deleted_rows")
    )


# ─── Employee CRUD tab ────────────────────────────────────────────────────────

def render_employee_tab(db: ShainDatabase, table: str, cols: List[str], key_prefix: str):
    """Unified CRUD panel shared by 派遣/請負/スタッフ."""

    # ── Filter bar ────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 3])
    with fc1:
        search_q = st.text_input(
            "🔍 氏名・カナ検索", key=f"{key_prefix}_s",
            placeholder="例: NGUYEN, 田中",
        )
    with fc2:
        status_opts = {
            "全員": None,
            "在職中": "在職中",
            "退社": "退社",
        }
        status_lbl = st.selectbox("ステータス", list(status_opts.keys()), key=f"{key_prefix}_st")
        status_filter = status_opts[status_lbl]

    with fc3:
        df_all = fetch_all(DB_PATH, table)
        nats = ["全国籍"] + sorted(df_all["国籍"].dropna().unique().tolist()) if "国籍" in df_all.columns else ["全国籍"]
        nat_filter = st.selectbox("国籍", nats, key=f"{key_prefix}_nat")

    with fc4:
        default_visible = DEFAULT_VISIBLE.get(table, cols[:8])
        visible_cols = st.multiselect(
            "表示列",
            options=[c for c in cols if c not in ("id", "updated_at", "deleted_at")],
            default=[c for c in default_visible if c in cols],
            key=f"{key_prefix}_vis",
        )

    # ── Load + filter ─────────────────────────────────────────────────────
    with st.spinner("読み込み中…"):
        df = fetch_all(DB_PATH, table)

    if df.empty:
        st.markdown("""
        <div class="alert-banner banner-info">
            📭 データがありません。<b>⚙️ 設定・インポート</b> タブから Excel をインポートしてください。
        </div>""", unsafe_allow_html=True)
        _render_add_form(db, table, cols, key_prefix)
        return

    if search_q:
        mask = pd.Series([False] * len(df))
        for sc in ("氏名", "カナ"):
            if sc in df.columns:
                mask |= df[sc].astype(str).str.contains(search_q, case=False, na=False, regex=False)
        df = df[mask]

    if status_filter:
        if table in ("genzai", "ukeoi") and "現在" in df.columns:
            df = df[df["現在"] == status_filter]
        elif table == "staff":
            if status_filter == "在職中":
                df = df[df["入社日"].notna() & df["退社日"].isna()]
            else:
                df = df[df["退社日"].notna()]

    if nat_filter != "全国籍" and "国籍" in df.columns:
        df = df[df["国籍"] == nat_filter]

    # ── Unsaved changes banner ────────────────────────────────────────────
    if _has_unsaved(key_prefix):
        st.markdown(
            '<div class="alert-banner banner-warning">⚠️ '
            '未保存の変更があります。下の <b>💾 変更を保存</b> ボタンを押してください。'
            '</div>', unsafe_allow_html=True,
        )

    st.caption(f"{len(df)} 件表示中 (合計 {len(fetch_all(DB_PATH, table))} 件)")

    # ── Column config ──────────────────────────────────────────────────────
    show_cols = [c for c in visible_cols if c in df.columns]
    if not show_cols:
        show_cols = [c for c in DEFAULT_VISIBLE.get(table, cols[:8]) if c in df.columns]

    df_disp = df[show_cols].copy()
    for c in df_disp.columns:
        if c in DATE_COLS:
            df_disp[c] = pd.to_datetime(df_disp[c], errors="coerce").dt.date

    col_cfgs = {c: _col_cfg(c, editable=is_admin()) for c in show_cols}

    edited_df = st.data_editor(
        df_disp,
        column_config=col_cfgs,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key=f"{key_prefix}_editor",
        height=420,
        disabled=not is_admin(),
    )

    # ── Inline save ────────────────────────────────────────────────────────
    if is_admin():
        save_c, _ = st.columns([2, 8])
        with save_c:
            if st.button("💾 変更を保存", key=f"{key_prefix}_save", type="primary"):
                changes = 0
                try:
                    for idx in range(len(df_disp)):
                        row_id = int(df.iloc[idx]["id"])
                        diff: Dict = {}
                        for col in show_cols:
                            o_str = "" if pd.isna(df_disp.iloc[idx][col]) else str(df_disp.iloc[idx][col])
                            e_str = "" if pd.isna(edited_df.iloc[idx][col]) else str(edited_df.iloc[idx][col])
                            if o_str != e_str:
                                diff[col] = edited_df.iloc[idx][col]
                        if diff:
                            if "生年月日" in diff:
                                diff["年齢"] = calc_age(str(diff["生年月日"]) if diff["生年月日"] else None)
                            if table == "genzai" and ("時給" in diff or "請求単価" in diff):
                                jk = diff.get("時給") or df_disp.iloc[idx].get("時給")
                                sk = diff.get("請求単価") or df_disp.iloc[idx].get("請求単価")
                                p = calc_profit(sk, jk)
                                if p is not None:
                                    diff["差額利益"] = round(p, 0)
                            db.update_employee(table, row_id, diff)
                            changes += 1

                    if changes:
                        _invalidate_cache()
                        time.sleep(0.3)
                        _toast(f"{changes} 件を保存しました")
                        st.rerun()
                    else:
                        st.info("変更はありませんでした")
                except Exception as e:
                    st.error(f"❌ 保存エラー: {e}")
                    logger.exception("Save error")

    st.divider()

    # ── Detail edit panel ──────────────────────────────────────────────────
    with st.expander("📝 詳細編集", expanded=False):
        if is_admin():
            row_ids = df["id"].tolist()
            if not row_ids:
                st.info("表示中の行がありません")
            else:
                sel_id = st.selectbox(
                    "編集する社員を選択",
                    row_ids,
                    format_func=lambda rid: _row_label(df, rid),
                    key=f"{key_prefix}_sel",
                )
                emp = db.get_employee(table, sel_id)
                if emp:
                    st.caption(f"最終更新: {emp.get('updated_at', '—')}")
                    updated = render_detail_form(emp, table, key_prefix)
                    if st.button("💾 詳細を保存", key=f"{key_prefix}_det_save", type="primary"):
                        try:
                            if "生年月日" in updated:
                                updated["年齢"] = calc_age(str(updated["生年月日"]) if updated["生年月日"] else None)
                            if table == "genzai":
                                p = calc_profit(updated.get("請求単価"), updated.get("時給"))
                                if p is not None:
                                    updated["差額利益"] = round(p, 0)
                            db.update_employee(table, sel_id, updated)
                            _invalidate_cache()
                            time.sleep(0.3)
                            _toast("詳細を保存しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 保存エラー: {e}")
        else:
            st.warning("🔒 編集には管理者ログインが必要です。サイドバーからログインしてください。")

    # ── Delete panel ───────────────────────────────────────────────────────
    if is_admin():
        with st.expander("🗑️ 社員をゴミ箱に移動", expanded=False):
            row_ids = df["id"].tolist()
            if not row_ids:
                st.info("削除できる行がありません")
            else:
                del_id = st.selectbox(
                    "対象社員を選択",
                    row_ids,
                    format_func=lambda rid: _row_label(df, rid),
                    key=f"{key_prefix}_del_sel",
                )
                emp_del = db.get_employee(table, del_id)
                emp_name = emp_del.get("氏名", "不明") if emp_del else "不明"

                st.markdown(f"""
                <div class="danger-zone">
                    ⚠️ <b>{emp_name}</b> をゴミ箱に移動します。<br>
                    ゴミ箱から復元できます。完全削除は ⚙️ 設定 タブで行えます。<br><br>
                    確認のため社員名を入力してください:
                </div>""", unsafe_allow_html=True)

                confirm_input = st.text_input(
                    "社員名を入力", key=f"{key_prefix}_del_confirm"
                )
                if confirm_input == emp_name:
                    if st.button("🗑️ ゴミ箱に移動", key=f"{key_prefix}_del_btn", type="secondary"):
                        try:
                            db.delete_employee(table, del_id)
                            _invalidate_cache()
                            time.sleep(0.3)
                            _toast(f"{emp_name} をゴミ箱に移動しました", "🗑️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 削除エラー: {e}")
                else:
                    st.caption("社員名を正確に入力すると削除ボタンが有効になります")

    # ── Add form ───────────────────────────────────────────────────────────
    _render_add_form(db, table, cols, key_prefix)


def _row_label(df: pd.DataFrame, row_id: int) -> str:
    row = df[df["id"] == row_id]
    if row.empty:
        return str(row_id)
    r = row.iloc[0]
    return f"{r.get('社員№', '')} — {r.get('氏名', '')}"


def _render_add_form(db: ShainDatabase, table: str, cols: List[str], key_prefix: str):
    if not is_admin():
        return
    label_map = {"genzai": "派遣社員", "ukeoi": "請負社員", "staff": "スタッフ"}
    with st.expander(f"➕ 新規{label_map.get(table, '')}登録", expanded=False):
        quick = [c for c in cols if c in (
            "現在", "社員№", "氏名", "カナ", "性別", "国籍", "生年月日",
            "入社日", "時給", "請求単価", "派遣先", "請負業務", "事務所",
            "ビザ期限", "ビザ種類",
        )]
        new_data: Dict = {}
        ncols = st.columns(3)
        for i, field in enumerate(quick):
            with ncols[i % 3]:
                new_data[field] = _field_widget(field, None, f"{key_prefix}_add_{field}")

        if st.button("✅ 登録する", key=f"{key_prefix}_add_submit", type="primary"):
            errors = []
            if not str(new_data.get("氏名", "")).strip():
                errors.append("氏名は必須です")
            if not str(new_data.get("社員№", "")).strip():
                errors.append("社員№は必須です")
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                try:
                    new_data["年齢"] = calc_age(str(new_data.get("生年月日", "")) if new_data.get("生年月日") else None)
                    if table == "genzai":
                        p = calc_profit(new_data.get("請求単価"), new_data.get("時給"))
                        if p is not None:
                            new_data["差額利益"] = round(p, 0)
                    new_id = db.add_employee(table, new_data)
                    _invalidate_cache()
                    time.sleep(0.3)
                    _toast(f"登録しました (ID: {new_id})")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 登録エラー: {e}")


# ─── Pages ────────────────────────────────────────────────────────────────────

def page_home(db: ShainDatabase):
    st.header("📊 ダッシュボード")

    # ── Visa alert banner ──────────────────────────────────────────────────
    with st.spinner("アラートを確認中…"):
        alerts = fetch_visa(DB_PATH, 90)

    expired = [a for a in alerts if "期限切れ" in a["alert_level"]]
    urgent  = [a for a in alerts if "緊急" in a["alert_level"]]
    warning = [a for a in alerts if "警告" in a["alert_level"]]

    if expired:
        st.markdown(
            f'<div class="alert-banner banner-critical">🔴 '
            f'<b>ビザ期限切れ {len(expired)} 件</b> — すぐに対応が必要です！'
            f'（緊急 {len(urgent)} 件 / 警告 {len(warning)} 件含む）</div>',
            unsafe_allow_html=True,
        )
    elif urgent:
        st.markdown(
            f'<div class="alert-banner banner-critical">🔴 '
            f'<b>緊急ビザアラート {len(urgent)} 件</b>（30日以内に期限切れ）</div>',
            unsafe_allow_html=True,
        )
    elif warning:
        st.markdown(
            f'<div class="alert-banner banner-warning">🟠 '
            f'<b>ビザ警告 {len(warning)} 件</b>（60日以内に期限切れ）</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="alert-banner banner-ok">✅ '
            'ビザ期限切れアラートはありません（90日以内）</div>',
            unsafe_allow_html=True,
        )

    # ── KPIs ──────────────────────────────────────────────────────────────
    with st.spinner("統計を読み込み中…"):
        stats = fetch_summary(DB_PATH)

    total = stats.get("total", {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総登録人数", total.get("total", 0))
    with col2:
        active = total.get("active", 0)
        tot = total.get("total", 1)
        st.metric("在職中", active, f"{active/tot*100:.1f}%" if tot else "")
    with col3:
        st.metric("退社・その他", total.get("retired", 0))
    with col4:
        info = db.db_info()
        latest = max(
            (t.get("last_updated") or "" for t in info["tables"].values()),
            default="—",
        )
        st.metric("最終更新", latest[:10] if latest and latest != "—" else "—")

    # ── Category bar chart ────────────────────────────────────────────────
    st.subheader("カテゴリ別人数")
    labels = ["派遣社員", "請負社員", "スタッフ"]
    active_vals  = [stats[l]["active"]  for l in labels]
    retired_vals = [stats[l]["retired"] for l in labels]

    c_chart, c_tbl = st.columns([3, 1])
    with c_chart:
        fig = go.Figure(data=[
            go.Bar(name="在職中", x=labels, y=active_vals,  marker_color="#1E88E5"),
            go.Bar(name="退社",   x=labels, y=retired_vals, marker_color="#EF9A9A"),
        ])
        fig.update_layout(
            barmode="stack", height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Noto Sans JP,sans-serif"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)
    with c_tbl:
        st.dataframe(
            pd.DataFrame({"カテゴリ": labels, "在職中": active_vals, "退社": retired_vals}),
            hide_index=True, use_container_width=True,
        )

    # ── Nationality (horizontal bar charts instead of pie) ─────────────────
    st.subheader("国籍分布")
    with st.spinner():
        nat = fetch_nationality(DB_PATH)

    n_cols = st.columns(3)
    for i, (lbl, key) in enumerate([("派遣社員", "派遣"), ("請負社員", "請負"), ("スタッフ", "スタッフ")]):
        with n_cols[i]:
            st.write(f"**{lbl}**")
            data = nat.get(key, {})
            if data:
                fig_h = px.bar(
                    x=list(data.values()),
                    y=list(data.keys()),
                    orientation="h",
                    height=max(150, len(data) * 28),
                    labels={"x": "人数", "y": "国籍"},
                    color_discrete_sequence=["#42A5F5"],
                )
                fig_h.update_layout(
                    margin=dict(t=5, b=5, l=5, r=10),
                    yaxis=dict(autorange="reversed"),
                    showlegend=False,
                    font=dict(family="Noto Sans JP,sans-serif", size=12),
                )
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.caption("データなし")

    # ── 派遣先 top bar chart ───────────────────────────────────────────────
    st.subheader("派遣先 上位 10 社")
    with st.spinner():
        haken = fetch_hakensaki(DB_PATH, 10)
    if haken:
        hk_df = pd.DataFrame(haken)
        fig_hk = px.bar(
            hk_df, x="count", y="company", orientation="h",
            labels={"count": "人数", "company": "派遣先"},
            height=max(250, len(hk_df) * 32),
            color_discrete_sequence=["#26A69A"],
            text="count",
        )
        fig_hk.update_layout(
            margin=dict(t=5, b=10, l=5, r=10),
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            font=dict(family="Noto Sans JP,sans-serif", size=12),
        )
        fig_hk.update_traces(textposition="outside")
        st.plotly_chart(fig_hk, use_container_width=True)
    else:
        st.caption("派遣データなし")


def page_employees(db: ShainDatabase):
    st.header("👥 社員管理")

    category = st.radio(
        "区分を選択",
        ["派遣社員 (DBGenzaiX)", "請負社員 (DBUkeoiX)", "スタッフ (DBStaffX)"],
        horizontal=True,
        key="emp_cat",
    )

    if "派遣" in category:
        render_employee_tab(db, "genzai", GENZAI_COLS, "genzai")
    elif "請負" in category:
        render_employee_tab(db, "ukeoi", UKEOI_COLS, "ukeoi")
    else:
        render_employee_tab(db, "staff", STAFF_COLS, "staff")


def page_visa(db: ShainDatabase):
    st.header("🔔 ビザ期限アラート")

    c1, c2 = st.columns([2, 4])
    with c1:
        days_range = st.slider("今後 N 日以内", 1, 365, 90, key="visa_days")
    with c2:
        st.markdown(f"<br><span style='font-size:14px;color:#555;'>本日: {date.today().strftime('%Y-%m-%d')} 　表示期間: {days_range} 日以内</span>", unsafe_allow_html=True)

    with st.spinner("アラートを確認中…"):
        alerts = fetch_visa(DB_PATH, days_range)

    if not alerts:
        st.markdown(
            f'<div class="alert-banner banner-ok">✅ '
            f'{date.today().strftime("%Y-%m-%d")} 時点で、{days_range} 日以内に期限切れのビザはありません。</div>',
            unsafe_allow_html=True,
        )
        return

    expired  = [a for a in alerts if "期限切れ" in a["alert_level"]]
    urgent   = [a for a in alerts if "緊急" in a["alert_level"]]
    warning  = [a for a in alerts if "警告" in a["alert_level"]]
    upcoming = [a for a in alerts if "注意" in a["alert_level"]]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🔴 期限切れ", len(expired))
    m2.metric("🔴 緊急 (30日以内)", len(urgent))
    m3.metric("🟠 警告 (60日以内)", len(warning))
    m4.metric("🟡 注意", len(upcoming))

    # Group by severity level with expanders
    levels = [
        ("🔴 期限切れ・緊急", expired + urgent, True),
        ("🟠 警告 (31–60日)", warning, bool(expired or urgent) == False),
        ("🟡 注意 (61日以降)", upcoming, False),
    ]

    for level_label, level_alerts, expanded in levels:
        if level_alerts:
            with st.expander(f"{level_label} — {len(level_alerts)} 件", expanded=expanded):
                df_a = pd.DataFrame(level_alerts)[[
                    "alert_level", "category", "employee_id", "name",
                    "visa_type", "expiry_date", "days_left",
                ]].rename(columns={
                    "alert_level": "レベル", "category": "区分", "employee_id": "社員№",
                    "name": "氏名", "visa_type": "ビザ種類",
                    "expiry_date": "期限日", "days_left": "残日数",
                })
                st.dataframe(df_a, hide_index=True, use_container_width=True)

    # Full table + export
    st.divider()
    all_df = pd.DataFrame(alerts)[[
        "alert_level", "category", "employee_id", "name",
        "visa_type", "expiry_date", "days_left",
    ]].rename(columns={
        "alert_level": "レベル", "category": "区分", "employee_id": "社員№",
        "name": "氏名", "visa_type": "ビザ種類",
        "expiry_date": "期限日", "days_left": "残日数",
    })
    csv_b = all_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 アラートリストを CSV 出力",
        csv_b,
        f"visa_alerts_{date.today()}.csv",
        "text/csv",
    )


def page_salary(db: ShainDatabase):
    st.header("💰 給与・利益分析")

    with st.spinner("給与データを読み込み中…"):
        df_g = fetch_all(DB_PATH, "genzai", active_only=True)

    if df_g.empty:
        st.info("在職中の派遣社員データがありません")
        return

    for c in ("時給", "請求単価", "差額利益"):
        df_g[c] = pd.to_numeric(df_g[c], errors="coerce")

    # ── 時給 stats ────────────────────────────────────────────────────────
    st.subheader("時給 統計")
    jikyu = df_g["時給"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最低", fmt_yen(jikyu.min()) if len(jikyu) else "—")
    c2.metric("最高", fmt_yen(jikyu.max()) if len(jikyu) else "—")
    c3.metric("平均", fmt_yen(jikyu.mean()) if len(jikyu) else "—")
    c4.metric("中央値", fmt_yen(jikyu.median()) if len(jikyu) else "—")

    col_hist, col_box = st.columns(2)
    with col_hist:
        fig_hist = px.histogram(
            df_g.dropna(subset=["時給"]), x="時給",
            nbins=25, title="時給 分布",
            labels={"時給": "時給 (¥)"},
            color_discrete_sequence=["#42A5F5"],
            height=300,
        )
        fig_hist.update_layout(margin=dict(t=30, b=10), showlegend=False,
                                font=dict(family="Noto Sans JP,sans-serif"))
        st.plotly_chart(fig_hist, use_container_width=True)
    with col_box:
        fig_box = px.box(
            df_g.dropna(subset=["時給"]), y="時給",
            title="時給 箱ひげ図", color_discrete_sequence=["#42A5F5"], height=300,
        )
        fig_box.update_layout(margin=dict(t=30, b=10),
                               font=dict(family="Noto Sans JP,sans-serif"))
        st.plotly_chart(fig_box, use_container_width=True)

    # ── 請求単価 stats ────────────────────────────────────────────────────
    st.subheader("請求単価 統計")
    seikyu = df_g["請求単価"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最低", fmt_yen(seikyu.min()) if len(seikyu) else "—")
    c2.metric("最高", fmt_yen(seikyu.max()) if len(seikyu) else "—")
    c3.metric("平均", fmt_yen(seikyu.mean()) if len(seikyu) else "—")
    c4.metric("中央値", fmt_yen(seikyu.median()) if len(seikyu) else "—")

    # Scatter only with positive profit (use numeric shape for negatives)
    scatter_pos = df_g.dropna(subset=["時給", "請求単価", "差額利益"])
    scatter_pos = scatter_pos[scatter_pos["差額利益"] > 0].copy()
    if len(scatter_pos) > 0:
        fig_sc = px.scatter(
            scatter_pos, x="時給", y="請求単価",
            color="差額利益", size="差額利益",
            title="時給 vs 請求単価（差額利益でサイズ付け）",
            labels={"時給": "時給 (¥)", "請求単価": "請求単価 (¥)", "差額利益": "利益 (¥)"},
            height=420,
            color_continuous_scale="Blues",
        )
        fig_sc.update_layout(font=dict(family="Noto Sans JP,sans-serif"),
                              margin=dict(t=30, b=10))
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── 差額利益 stats ─────────────────────────────────────────────────────
    st.subheader("差額利益 統計")
    profit = df_g["差額利益"].dropna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最低", fmt_yen(profit.min()) if len(profit) else "—")
    c2.metric("最高", fmt_yen(profit.max()) if len(profit) else "—")
    c3.metric("平均", fmt_yen(profit.mean()) if len(profit) else "—")
    c4.metric("合計 (月次推定)", fmt_yen(profit.sum() * 160) if len(profit) else "—",
              help="平均 160時間/月 × 人数合計で試算")

    # ── Profit simulator ─────────────────────────────────────────────────
    st.subheader("💡 利益率シミュレーター")
    s1, s2 = st.columns(2)
    with s1:
        sim_j = st.number_input("時給 (¥)", value=1_200, step=50, min_value=0, key="sim_j")
    with s2:
        sim_s = st.number_input("請求単価 (¥)", value=1_800, step=50, min_value=0, key="sim_s")

    if sim_s > 0:
        burden = sim_j * COMPANY_BURDEN_RATE
        gross  = sim_s - sim_j
        net    = sim_s - sim_j - burden
        margin = net / sim_s * 100
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("会社負担", fmt_yen(burden))
        r2.metric("差額利益 (粗)", fmt_yen(gross))
        r3.metric("差額利益 (純)", fmt_yen(net))
        r4.metric("利益率", f"{margin:.1f}%",
                  delta="良好" if margin >= 15 else "要確認",
                  delta_color="normal" if margin >= 15 else "inverse")


def page_audit(db: ShainDatabase):
    st.header("📋 監査ログ")
    st.caption("全ての追加・更新・削除・インポート操作が記録されます")

    c1, c2 = st.columns([2, 2])
    with c1:
        table_filter = st.selectbox(
            "テーブル絞り込み",
            ["全て", "genzai (派遣)", "ukeoi (請負)", "staff (スタッフ)", "* (システム)"],
            key="audit_table",
        )
    with c2:
        limit = st.number_input("表示件数", value=100, step=50, min_value=10, max_value=1000, key="audit_limit")

    table_map = {
        "genzai (派遣)": "genzai",
        "ukeoi (請負)":  "ukeoi",
        "staff (スタッフ)": "staff",
        "* (システム)": "*",
    }
    tbl = table_map.get(table_filter)

    with st.spinner("ログを読み込み中…"):
        df_log = db.get_audit_log(table=tbl, limit=int(limit))

    if df_log.empty:
        st.info("ログがありません")
        return

    action_colors = {
        "INSERT":      "🟢",
        "UPDATE":      "🔵",
        "DELETE":      "🟠",
        "RESTORE":     "🟣",
        "HARD_DELETE": "🔴",
        "IMPORT":      "⚪",
    }
    df_log["icon"] = df_log["action"].map(lambda x: action_colors.get(x, "⬛"))
    df_log["操作"] = df_log["icon"] + " " + df_log["action"]

    display = df_log[["changed_at", "操作", "table_name", "row_id", "employee_name", "changes"]].rename(columns={
        "changed_at":    "日時",
        "table_name":    "テーブル",
        "row_id":        "ID",
        "employee_name": "社員名",
        "changes":       "変更内容",
    })

    st.dataframe(display, hide_index=True, use_container_width=True, height=500)

    csv_b = display.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥 ログを CSV 出力", csv_b, "audit_log.csv", "text/csv")


def page_settings(db: ShainDatabase):
    st.header("⚙️ 設定・インポート")

    # ── DB info ──────────────────────────────────────────────────────────
    st.subheader("データベース情報")
    info = db.db_info()
    i1, i2, i3 = st.columns(3)
    labels_t = {"genzai": "派遣社員", "ukeoi": "請負社員", "staff": "スタッフ"}
    for col_w, tbl in zip([i1, i2, i3], ("genzai", "ukeoi", "staff")):
        ti = info["tables"].get(tbl, {})
        with col_w:
            st.metric(labels_t[tbl], f"{ti.get('rows', 0)} 件")
            if ti.get("deleted"):
                st.caption(f"ゴミ箱: {ti['deleted']} 件")
            st.caption(f"更新: {ti.get('last_updated', '—')}")
    st.caption(f"DB: `{info['path']}`")

    st.divider()

    # ── Excel import ──────────────────────────────────────────────────────
    st.subheader("📥 Excel インポート")
    st.warning(
        "⚠️ インポートすると、既存の全データ（ゴミ箱も含む）が上書きされます。"
        "定期的にエクスポートしてバックアップを取ることを推奨します。"
    )

    uploaded = st.file_uploader(
        "社員台帳 Excel (.xlsm / .xlsx)", type=["xlsm", "xlsx"], key="imp_upload"
    )

    if uploaded:
        st.write(f"**{uploaded.name}** ({uploaded.size:,} bytes)")

        # Preview step
        if st.button("🔍 プレビュー（インポート前確認）", key="imp_preview"):
            with st.spinner("解析中…"):
                suffix = Path(uploaded.name).suffix
                tmp = Path(tempfile.gettempdir()) / f"preview_{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"
                tmp.write_bytes(uploaded.getvalue())
                try:
                    preview = db.preview_excel(str(tmp))
                    st.session_state["_import_preview"] = preview
                    st.session_state["_import_tmp"] = str(tmp)
                except Exception as e:
                    st.error(f"❌ 解析エラー: {e}")
                finally:
                    pass  # keep tmp for import

        if "_import_preview" in st.session_state:
            preview = st.session_state["_import_preview"]
            st.write("**📋 インポート内容プレビュー**")
            for tbl, data in preview.items():
                lbl = data.get("label", tbl)
                rows = data.get("rows", 0)
                err = data.get("error")
                if err:
                    st.error(f"{lbl}: ⚠️ {err}")
                else:
                    with st.expander(f"{lbl} — {rows} 件（先頭5行プレビュー）"):
                        sample = data.get("sample", [])
                        if sample:
                            st.dataframe(pd.DataFrame(sample), use_container_width=True, height=200)

            st.error("**この操作は元に戻せません。**")
            confirm_import = st.checkbox("上書きを確認しました", key="imp_confirm")
            if confirm_import and st.button("🚀 インポート実行", type="primary", key="imp_go"):
                tmp_path = st.session_state.get("_import_tmp")
                if tmp_path:
                    prog = st.progress(0.0, text="インポート開始…")
                    status = st.empty()
                    def on_prog(msg, frac):
                        prog.progress(min(frac, 1.0), text=msg)
                        status.write(msg)
                    try:
                        counts = db.import_from_excel(tmp_path, progress_callback=on_prog)
                        prog.progress(1.0, text="完了！")
                        _invalidate_cache()
                        del st.session_state["_import_preview"]
                        del st.session_state["_import_tmp"]
                        st.success(
                            f"✅ インポート完了！\n"
                            f"- 派遣社員: **{counts.get('genzai', 0)}** 件\n"
                            f"- 請負社員: **{counts.get('ukeoi', 0)}** 件\n"
                            f"- スタッフ: **{counts.get('staff', 0)}** 件"
                        )
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ インポートエラー: {e}")
                        logger.exception("Import failed")

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────
    st.subheader("📤 データエクスポート")
    ec1, ec2 = st.columns(2)
    with ec1:
        exp_fmt = st.radio("フォーマット", ["CSV", "Excel"], horizontal=True)
    with ec2:
        exp_tbl = st.selectbox("対象", ["全テーブル", "派遣社員", "請負社員", "スタッフ"])

    tbl_map = {"派遣社員": "genzai", "請負社員": "ukeoi", "スタッフ": "staff"}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if exp_tbl == "全テーブル":
        dfs = {l: fetch_all(DB_PATH, t) for t, l in [("genzai","派遣"),("ukeoi","請負"),("staff","スタッフ")]}
    else:
        t = tbl_map[exp_tbl]
        dfs = {exp_tbl: fetch_all(DB_PATH, t)}

    if exp_fmt == "CSV":
        for lbl, df_e in dfs.items():
            csv_b = df_e.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(f"📥 {lbl} CSV", csv_b, f"{lbl}_{ts}.csv", "text/csv", key=f"dl_{lbl}")
    else:
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for lbl, df_e in dfs.items():
                df_e.to_excel(writer, sheet_name=lbl[:31], index=False)
        st.download_button(
            "📥 Excel ダウンロード", buf.getvalue(),
            f"shain_daicho_{ts}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.divider()

    # ── Recycle bin ───────────────────────────────────────────────────────
    st.subheader("🗑️ ゴミ箱")
    if is_admin():
        rb_tbl = st.selectbox(
            "テーブル", ["genzai (派遣)", "ukeoi (請負)", "staff (スタッフ)"],
            key="rb_tbl",
        )
        tbl_key = rb_tbl.split(" ")[0]
        df_del = db.get_deleted(tbl_key)

        if df_del.empty:
            st.caption("ゴミ箱は空です")
        else:
            st.dataframe(
                df_del[["id","社員№","氏名","deleted_at"]].rename(columns={"deleted_at":"削除日時"}),
                hide_index=True, use_container_width=True,
            )
            restore_id = st.selectbox(
                "復元する ID", df_del["id"].tolist(),
                format_func=lambda rid: f"{rid} — {df_del[df_del['id']==rid].iloc[0].get('氏名','?')}",
                key="rb_restore_id",
            )
            rc1, rc2 = st.columns([2, 2])
            with rc1:
                if st.button("♻️ 復元", key="rb_restore_btn"):
                    db.restore_employee(tbl_key, restore_id)
                    _invalidate_cache()
                    _toast("復元しました", "♻️")
                    st.rerun()
            with rc2:
                if st.button("💥 完全削除", key="rb_hard_del", type="secondary"):
                    db.hard_delete_employee(tbl_key, restore_id)
                    _invalidate_cache()
                    _toast("完全削除しました", "💥")
                    st.rerun()
    else:
        st.warning("🔒 ゴミ箱の操作には管理者ログインが必要です。")

    st.divider()

    # ── Admin auth ────────────────────────────────────────────────────────
    st.subheader("🔐 管理者ログイン")
    if is_admin():
        st.markdown('<div class="alert-banner banner-ok">✅ 管理者としてログイン中</div>', unsafe_allow_html=True)
        if st.button("ログアウト", key="logout"):
            st.session_state["_role"] = "viewer"
            _toast("ログアウトしました", "👋")
            st.rerun()
    else:
        pwd = st.text_input("パスワード", type="password", key="admin_pwd")
        if st.button("ログイン", key="login_btn"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["_role"] = "admin"
                _toast("管理者としてログインしました", "🔓")
                st.rerun()
            else:
                st.error("❌ パスワードが違います")


# ─── Sidebar nav ──────────────────────────────────────────────────────────────

def sidebar_nav(db: ShainDatabase) -> str:
    with st.sidebar:
        st.markdown("## 👥 社員台帳")
        st.caption("UNS Manager v3")
        st.divider()

        # Live alert count badge
        try:
            alerts = fetch_visa(DB_PATH, 90)
            urgent_n = sum(1 for a in alerts if a["alert_class"] in ("expired", "urgent"))
        except Exception:
            urgent_n = 0

        visa_label = f"🔔 ビザアラート  🔴{urgent_n}" if urgent_n else "🔔 ビザアラート"

        pages = [
            "🏠 ホーム",
            "👥 社員管理",
            visa_label,
            "💰 給与・利益分析",
            "📋 監査ログ",
            "⚙️ 設定・インポート",
        ]

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = pages[0]

        choice = st.radio("メニュー", pages, key="nav_radio",
                          index=pages.index(st.session_state["current_page"])
                          if st.session_state["current_page"] in pages else 0)
        st.session_state["current_page"] = choice

        st.divider()
        if is_admin():
            st.success("🔓 管理者モード")
        else:
            st.info("👁️ 閲覧モード")
            st.caption("編集するには ⚙️ 設定 からログイン")

    return choice


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    db = get_db()

    if not db.has_data():
        with st.sidebar:
            st.markdown("## 👥 社員台帳")
            st.warning("データがありません")
        st.markdown("""
        <div class="alert-banner banner-info" style="margin-top:40px;font-size:16px;">
            📭 <b>データベースが空です。</b><br><br>
            左サイドバーの <b>⚙️ 設定・インポート</b> から Excel ファイルをインポートして始めましょう。
        </div>""", unsafe_allow_html=True)
        if st.button("⚙️ インポート画面を開く", type="primary"):
            st.session_state["current_page"] = "⚙️ 設定・インポート"
            st.rerun()

    page = sidebar_nav(db)

    if "ホーム" in page:
        page_home(db)
    elif "社員管理" in page:
        page_employees(db)
    elif "ビザ" in page:
        page_visa(db)
    elif "給与" in page:
        page_salary(db)
    elif "監査" in page:
        if is_admin():
            page_audit(db)
        else:
            st.header("📋 監査ログ")
            st.warning("🔒 監査ログの閲覧には管理者ログインが必要です。⚙️ 設定 からログインしてください。")
    elif "設定" in page:
        page_settings(db)


if __name__ == "__main__":
    main()
