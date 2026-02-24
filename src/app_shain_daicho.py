#!/usr/bin/env python3
"""
UNS 社員台帳 Manager — Full CRUD Dashboard
Streamlit application backed by SQLite (ShainDatabase).
"""

import logging
import sys
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure src/ is importable when run as `streamlit run src/app_shain_daicho.py`
_src = Path(__file__).parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
_root = _src.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from database import ShainDatabase, GENZAI_COLS, UKEOI_COLS, STAFF_COLS
from shain_utils import ShainDaicho

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="UNS 社員台帳 Manager",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = str(_root / "data" / "shain_daicho.db")
COMPANY_BURDEN_RATE = 0.1576

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.kpi-card { background:#f0f2f6; padding:16px 20px; border-radius:10px; margin:4px 0; }
.alert-expired  { background:#ffe0e0; padding:8px 12px; border-radius:6px; margin:4px 0; }
.alert-urgent   { background:#ffcccc; padding:8px 12px; border-radius:6px; margin:4px 0; }
.alert-warning  { background:#ffe4b5; padding:8px 12px; border-radius:6px; margin:4px 0; }
.alert-upcoming { background:#fffacd; padding:8px 12px; border-radius:6px; margin:4px 0; }
div[data-testid="stDataFrame"] { border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Shared DB resource
# ---------------------------------------------------------------------------


@st.cache_resource
def get_db() -> ShainDatabase:
    db = ShainDatabase(DB_PATH)
    db.init_db()
    return db


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def fmt_yen(v) -> str:
    try:
        return f"¥{int(float(v)):,}"
    except Exception:
        return "—"


def fmt_date(v) -> str:
    if v is None or str(v).strip() in ("", "None", "nan"):
        return "—"
    return str(v)[:10]


def calc_age(birthdate_str: Optional[str]) -> Optional[int]:
    if not birthdate_str:
        return None
    try:
        bd = datetime.strptime(str(birthdate_str)[:10], "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        return None


def calc_profit(seikyu, jikyu) -> Optional[float]:
    try:
        s, j = float(seikyu), float(jikyu)
        return s - j - j * COMPANY_BURDEN_RATE
    except Exception:
        return None


def visa_color(days_left) -> str:
    try:
        d = int(days_left)
        if d <= 0:
            return "🔴"
        if d <= 30:
            return "🔴"
        if d <= 60:
            return "🟠"
        return "🟡"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# CRUD Employee Tab renderer
# ---------------------------------------------------------------------------


def render_employee_tab(
    db: ShainDatabase,
    table: str,
    label: str,
    cols: list,
    key_prefix: str,
):
    """Reusable CRUD panel for genzai / ukeoi / staff."""

    # ---- Top filter bar ------------------------------------------------
    filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 2])
    with filter_col1:
        search_q = st.text_input(
            "🔍 氏名・カナ検索", key=f"{key_prefix}_search", placeholder="例: NGUYEN, 田中"
        )
    with filter_col2:
        if table in ("genzai", "ukeoi"):
            status_opts = ["全員", "在職中", "退社"]
        else:
            status_opts = ["全員", "在職中", "退社"]
        status_filter = st.selectbox("ステータス", status_opts, key=f"{key_prefix}_status")
    with filter_col3:
        nat_opts = ["全国籍"]
        df_nat = db.get_all(table)
        if "国籍" in df_nat.columns:
            nats = sorted(df_nat["国籍"].dropna().unique().tolist())
            nat_opts += nats
        nat_filter = st.selectbox("国籍", nat_opts, key=f"{key_prefix}_nat")

    # ---- Load data -------------------------------------------------------
    df = db.get_all(table)
    if df.empty:
        st.info("データがありません。⚙️ インポート・設定 タブからExcelをインポートしてください。")
        _render_add_form(db, table, cols, key_prefix)
        return

    # Apply filters
    if search_q:
        mask = pd.Series([False] * len(df))
        for col in ["氏名", "カナ"]:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(search_q, case=False, na=False, regex=False)
        df = df[mask]

    if status_filter != "全員":
        if table in ("genzai", "ukeoi") and "現在" in df.columns:
            df = df[df["現在"] == status_filter]
        elif table == "staff":
            if status_filter == "在職中":
                df = df[df["入社日"].notna() & df["退社日"].isna()]
            else:
                df = df[df["退社日"].notna()]

    if nat_filter != "全国籍" and "国籍" in df.columns:
        df = df[df["国籍"] == nat_filter]

    st.caption(f"{len(df)} 件表示中")

    # ---- Column config for data_editor -----------------------------------
    col_cfg = {}
    for c in df.columns:
        if c == "id":
            col_cfg[c] = st.column_config.NumberColumn("id", disabled=True, width="small")
        elif c == "updated_at":
            col_cfg[c] = st.column_config.TextColumn("更新日時", disabled=True, width="medium")
        elif c in ("現在",):
            col_cfg[c] = st.column_config.SelectboxColumn(
                c, options=["在職中", "退社", "休職"], width="small"
            )
        elif c == "性別":
            col_cfg[c] = st.column_config.SelectboxColumn(c, options=["男", "女"], width="small")
        elif c in ("時給", "請求単価", "差額利益", "標準報酬", "健康保険", "介護保険", "厚生年金", "交通費"):
            col_cfg[c] = st.column_config.NumberColumn(c, format="¥%d", min_value=0)
        elif c in ("生年月日", "ビザ期限", "入社日", "退社日", "入居", "退去", "免許期限", "任意保険期限"):
            col_cfg[c] = st.column_config.DateColumn(c, format="YYYY-MM-DD")
        elif c == "年齢":
            col_cfg[c] = st.column_config.NumberColumn(c, disabled=True, width="small")

    # Determine display columns (hide id, updated_at from inline editor)
    display_cols = [c for c in df.columns if c not in ("id", "updated_at")]
    df_display = df[display_cols].copy()

    # Convert date strings to actual date objects for DateColumn
    for c in df_display.columns:
        if c in ("生年月日", "ビザ期限", "入社日", "退社日", "入居", "退去", "免許期限", "任意保険期限"):
            df_display[c] = pd.to_datetime(df_display[c], errors="coerce").dt.date

    # ---- Inline data_editor ----------------------------------------------
    edited_df = st.data_editor(
        df_display,
        column_config=col_cfg,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key=f"{key_prefix}_editor",
        height=400,
    )

    # ---- Save inline edits -----------------------------------------------
    save_col, del_col, _ = st.columns([2, 2, 6])
    with save_col:
        if st.button("💾 変更を保存", key=f"{key_prefix}_save", type="primary"):
            changes = 0
            for idx in range(len(df_display)):
                row_id = int(df.iloc[idx]["id"])
                orig = df_display.iloc[idx]
                edit = edited_df.iloc[idx]
                diff = {}
                for col in display_cols:
                    o_val = orig[col]
                    e_val = edit[col]
                    # Normalise for comparison
                    o_str = "" if pd.isna(o_val) or o_val is None else str(o_val)
                    e_str = "" if pd.isna(e_val) or e_val is None else str(e_val)
                    if o_str != e_str:
                        diff[col] = e_val
                if diff:
                    # Auto-recalculate derived fields
                    if "生年月日" in diff:
                        diff["年齢"] = calc_age(str(diff["生年月日"]) if diff["生年月日"] else None)
                    if table == "genzai" and ("時給" in diff or "請求単価" in diff):
                        try:
                            jk = diff.get("時給") or edit.get("時給") or orig.get("時給")
                            sk = diff.get("請求単価") or edit.get("請求単価") or orig.get("請求単価")
                            profit = calc_profit(sk, jk)
                            if profit is not None:
                                diff["差額利益"] = round(profit, 0)
                        except Exception:
                            pass
                    db.update_employee(table, row_id, diff)
                    changes += 1
            if changes:
                st.success(f"✅ {changes} 件更新しました")
                st.rerun()
            else:
                st.info("変更はありませんでした")

    # ---- Detail edit / delete panel ---------------------------------------
    with st.expander("📝 詳細編集 / 🗑️ 削除", expanded=False):
        row_ids = df["id"].tolist()
        if not row_ids:
            st.info("行がありません")
        else:
            selected_id = st.selectbox(
                "編集する社員を選択",
                options=row_ids,
                format_func=lambda rid: _row_label(df, rid),
                key=f"{key_prefix}_select_id",
            )
            emp = db.get_employee(table, selected_id)
            if emp:
                updated = _render_detail_form(emp, table, cols, key_prefix)
                detail_col1, detail_col2 = st.columns([2, 8])
                with detail_col1:
                    if st.button("💾 詳細を保存", key=f"{key_prefix}_detail_save"):
                        # Recalc derived fields
                        if "生年月日" in updated:
                            updated["年齢"] = calc_age(updated.get("生年月日"))
                        if table == "genzai":
                            profit = calc_profit(updated.get("請求単価"), updated.get("時給"))
                            if profit is not None:
                                updated["差額利益"] = round(profit, 0)
                        db.update_employee(table, selected_id, updated)
                        st.success("✅ 保存しました")
                        st.rerun()

                st.divider()
                st.warning(f"⚠️ 削除確認: **{emp.get('氏名', '?')}** (ID: {selected_id})")
                if st.checkbox("削除を確定する", key=f"{key_prefix}_del_confirm"):
                    if st.button("🗑️ 削除実行", key=f"{key_prefix}_delete", type="secondary"):
                        db.delete_employee(table, selected_id)
                        st.success("✅ 削除しました")
                        st.rerun()

    # ---- Add new employee ------------------------------------------------
    _render_add_form(db, table, cols, key_prefix)


def _row_label(df: pd.DataFrame, row_id: int) -> str:
    row = df[df["id"] == row_id]
    if row.empty:
        return str(row_id)
    name = row.iloc[0].get("氏名", "")
    emp_no = row.iloc[0].get("社員№", "")
    return f"{emp_no} — {name}" if emp_no else str(name)


def _render_detail_form(emp: dict, table: str, cols: list, key_prefix: str) -> dict:
    """Render full-field form pre-filled with emp data. Returns dict of field values."""
    updated = {}
    field_cols = [c for c in cols if c not in ("id", "updated_at")]

    # Group into rows of 3
    i = 0
    while i < len(field_cols):
        fcols = st.columns(3)
        for j in range(3):
            if i + j >= len(field_cols):
                break
            col_name = field_cols[i + j]
            cur_val = emp.get(col_name, "")
            with fcols[j]:
                if col_name in ("生年月日", "ビザ期限", "入社日", "退社日", "入居", "退去", "免許期限", "任意保険期限"):
                    try:
                        dv = datetime.strptime(str(cur_val)[:10], "%Y-%m-%d").date() if cur_val else None
                    except Exception:
                        dv = None
                    updated[col_name] = st.date_input(col_name, value=dv, key=f"{key_prefix}_det_{col_name}")
                elif col_name == "現在":
                    opts = ["在職中", "退社", "休職"]
                    idx = opts.index(cur_val) if cur_val in opts else 0
                    updated[col_name] = st.selectbox(col_name, opts, index=idx, key=f"{key_prefix}_det_{col_name}")
                elif col_name == "性別":
                    opts = ["男", "女"]
                    idx = opts.index(cur_val) if cur_val in opts else 0
                    updated[col_name] = st.selectbox(col_name, opts, index=idx, key=f"{key_prefix}_det_{col_name}")
                elif col_name in ("時給", "請求単価", "差額利益", "標準報酬", "健康保険", "介護保険", "厚生年金", "交通費"):
                    try:
                        nv = float(cur_val) if cur_val else 0.0
                    except Exception:
                        nv = 0.0
                    updated[col_name] = st.number_input(col_name, value=nv, step=10.0, key=f"{key_prefix}_det_{col_name}")
                elif col_name == "年齢":
                    # Read-only display
                    st.text_input(col_name, value=str(cur_val or ""), disabled=True, key=f"{key_prefix}_det_{col_name}")
                else:
                    updated[col_name] = st.text_input(col_name, value=str(cur_val or ""), key=f"{key_prefix}_det_{col_name}")
        i += 3
    return updated


def _render_add_form(db: ShainDatabase, table: str, cols: list, key_prefix: str):
    """Sidebar-style new employee registration form."""
    with st.expander("➕ 新規社員登録", expanded=False):
        st.write("必要項目を入力して登録してください")
        new_data = {}

        # Only show key fields in compact form; users can edit details after
        quick_fields = [c for c in cols if c in (
            "現在", "社員№", "氏名", "カナ", "性別", "国籍", "生年月日",
            "入社日", "時給", "請求単価", "派遣先", "請負業務", "事務所",
            "ビザ期限", "ビザ種類",
        )]

        ncols = st.columns(3)
        for idx, field in enumerate(quick_fields):
            with ncols[idx % 3]:
                if field == "現在":
                    new_data[field] = st.selectbox(field, ["在職中", "退社", "休職"], key=f"{key_prefix}_add_{field}")
                elif field == "性別":
                    new_data[field] = st.selectbox(field, ["男", "女"], key=f"{key_prefix}_add_{field}")
                elif field in ("生年月日", "ビザ期限", "入社日", "退社日"):
                    new_data[field] = st.date_input(field, value=None, key=f"{key_prefix}_add_{field}")
                elif field in ("時給", "請求単価"):
                    new_data[field] = st.number_input(field, value=0.0, step=10.0, min_value=0.0, key=f"{key_prefix}_add_{field}")
                else:
                    new_data[field] = st.text_input(field, key=f"{key_prefix}_add_{field}")

        if st.button("✅ 登録する", key=f"{key_prefix}_add_submit", type="primary"):
            # Derived fields
            new_data["年齢"] = calc_age(str(new_data.get("生年月日", "")) if new_data.get("生年月日") else None)
            if table == "genzai":
                profit = calc_profit(new_data.get("請求単価"), new_data.get("時給"))
                if profit is not None:
                    new_data["差額利益"] = round(profit, 0)
            new_id = db.add_employee(table, new_data)
            st.success(f"✅ 登録しました (id={new_id})")
            st.rerun()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main():
    st.title("👥 UNS 社員台帳 Manager")

    db = get_db()

    if not db.has_data():
        st.warning("⚠️ データベースが空です。まず **⚙️ インポート・設定** タブからExcelファイルをインポートしてください。")

    tabs = st.tabs([
        "📊 ダッシュボード",
        "👥 派遣社員",
        "📋 請負社員",
        "🏢 スタッフ",
        "🔔 ビザアラート",
        "💰 給与・利益分析",
        "⚙️ インポート・設定",
    ])

    # ============================================================
    # TAB 1: ダッシュボード
    # ============================================================
    with tabs[0]:
        st.header("📊 ダッシュボード")

        stats = db.get_summary_stats()
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
                default="—"
            )
            st.metric("最終更新", latest[:10] if latest and latest != "—" else "—")

        # Category breakdown chart
        st.subheader("カテゴリ別人数")
        labels = ["派遣社員", "請負社員", "スタッフ"]
        active_vals = [stats[l]["active"] for l in labels]
        retired_vals = [stats[l]["retired"] for l in labels]

        col_chart, col_tbl = st.columns([3, 1])
        with col_chart:
            fig = go.Figure(data=[
                go.Bar(name="在職中", x=labels, y=active_vals, marker_color="#2196F3"),
                go.Bar(name="退社", x=labels, y=retired_vals, marker_color="#F44336"),
            ])
            fig.update_layout(barmode="stack", height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with col_tbl:
            st.dataframe(
                pd.DataFrame({"カテゴリ": labels, "在職中": active_vals, "退社": retired_vals}),
                hide_index=True, use_container_width=True,
            )

        # Nationality pie charts
        st.subheader("国籍分布")
        nat = db.get_nationality_breakdown()
        nat_cols = st.columns(3)
        for i, (lbl, key) in enumerate([("派遣社員", "派遣"), ("請負社員", "請負"), ("スタッフ", "スタッフ")]):
            with nat_cols[i]:
                st.write(f"**{lbl}**")
                data = nat.get(key, {})
                if data:
                    fig_pie = px.pie(
                        values=list(data.values()),
                        names=list(data.keys()),
                        height=250,
                    )
                    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.caption("データなし")

        # Top hakensaki
        st.subheader("派遣先 上位")
        haken = db.get_hakensaki_breakdown(top_n=10)
        if haken:
            haken_df = pd.DataFrame(haken)
            fig_h = px.bar(
                haken_df, x="company", y="count",
                labels={"company": "派遣先", "count": "人数"},
                height=350,
            )
            fig_h.update_xaxes(tickangle=-40)
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.caption("派遣データなし")

    # ============================================================
    # TAB 2: 派遣社員
    # ============================================================
    with tabs[1]:
        st.header("👥 派遣社員 管理")
        render_employee_tab(db, "genzai", "派遣社員", GENZAI_COLS, "genzai")

    # ============================================================
    # TAB 3: 請負社員
    # ============================================================
    with tabs[2]:
        st.header("📋 請負社員 管理")
        render_employee_tab(db, "ukeoi", "請負社員", UKEOI_COLS, "ukeoi")

    # ============================================================
    # TAB 4: スタッフ
    # ============================================================
    with tabs[3]:
        st.header("🏢 スタッフ 管理")
        render_employee_tab(db, "staff", "スタッフ", STAFF_COLS, "staff")

    # ============================================================
    # TAB 5: ビザアラート
    # ============================================================
    with tabs[4]:
        st.header("🔔 ビザ期限アラート")

        days_range = st.slider("表示する日数（今後 N 日以内）", 1, 365, 90, key="visa_days")
        alerts = db.get_visa_alerts(days=days_range)

        expired = [a for a in alerts if "EXPIRED" in a["alert_level"]]
        urgent  = [a for a in alerts if "URGENT" in a["alert_level"] and "EXPIRED" not in a["alert_level"]]
        warning = [a for a in alerts if "WARNING" in a["alert_level"]]
        upcoming = [a for a in alerts if "UPCOMING" in a["alert_level"]]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 期限切れ", len(expired))
        m2.metric("🔴 緊急 (30日以内)", len(urgent))
        m3.metric("🟠 警告 (60日以内)", len(warning))
        m4.metric("🟡 注意 (90日以内)", len(upcoming))

        if alerts:
            alert_df = pd.DataFrame(alerts)[
                ["alert_level", "category", "employee_id", "name", "visa_type", "expiry_date", "days_left"]
            ].rename(columns={
                "alert_level": "レベル", "category": "区分", "employee_id": "社員№",
                "name": "氏名", "visa_type": "ビザ種類", "expiry_date": "期限", "days_left": "残日数",
            })
            st.dataframe(alert_df, hide_index=True, use_container_width=True, height=500)

            csv = alert_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "📥 アラートリストをCSV出力",
                csv,
                f"visa_alerts_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
            )
        else:
            st.success(f"✅ {days_range} 日以内に期限が切れるビザはありません")

    # ============================================================
    # TAB 6: 給与・利益分析
    # ============================================================
    with tabs[5]:
        st.header("💰 給与・利益分析")

        df_g = db.get_all("genzai", active_only=True)

        if df_g.empty:
            st.info("派遣社員データがありません")
        else:
            # Coerce numeric columns
            for c in ("時給", "請求単価", "差額利益"):
                df_g[c] = pd.to_numeric(df_g[c], errors="coerce")

            st.subheader("時給 統計")
            jikyu = df_g["時給"].dropna()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("最低", fmt_yen(jikyu.min()) if len(jikyu) else "—")
            c2.metric("最高", fmt_yen(jikyu.max()) if len(jikyu) else "—")
            c3.metric("平均", fmt_yen(jikyu.mean()) if len(jikyu) else "—")
            c4.metric("中央値", fmt_yen(jikyu.median()) if len(jikyu) else "—")

            fig_hist = px.histogram(
                df_g.dropna(subset=["時給"]), x="時給",
                nbins=30, title="時給 分布",
                labels={"時給": "時給 (¥)"},
                height=350,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            st.subheader("請求単価 統計")
            seikyu = df_g["請求単価"].dropna()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("最低", fmt_yen(seikyu.min()) if len(seikyu) else "—")
            c2.metric("最高", fmt_yen(seikyu.max()) if len(seikyu) else "—")
            c3.metric("平均", fmt_yen(seikyu.mean()) if len(seikyu) else "—")
            c4.metric("中央値", fmt_yen(seikyu.median()) if len(seikyu) else "—")

            # Scatter: hourly vs billing (positive profit only for size)
            scatter_df = df_g.dropna(subset=["時給", "請求単価"]).copy()
            scatter_pos = scatter_df[scatter_df["差額利益"] > 0].copy()

            if len(scatter_pos) > 0:
                fig_scatter = px.scatter(
                    scatter_pos, x="時給", y="請求単価",
                    color="差額利益", size="差額利益",
                    title="時給 vs 請求単価 (差額利益でサイズ付け)",
                    labels={"時給": "時給 (¥)", "請求単価": "請求単価 (¥)", "差額利益": "利益 (¥)"},
                    height=450,
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            # Profit margin calculator
            st.subheader("利益率 シミュレーター")
            sc1, sc2 = st.columns(2)
            with sc1:
                sim_jikyu = st.number_input("時給 (¥)", value=1200, step=50, min_value=0)
            with sc2:
                sim_seikyu = st.number_input("請求単価 (¥)", value=1800, step=50, min_value=0)

            if sim_seikyu > 0:
                burden = sim_jikyu * COMPANY_BURDEN_RATE
                net = sim_seikyu - sim_jikyu - burden
                margin = net / sim_seikyu * 100
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("会社負担", fmt_yen(burden))
                r2.metric("差額利益 (粗)", fmt_yen(sim_seikyu - sim_jikyu))
                r3.metric("差額利益 (純)", fmt_yen(net))
                r4.metric("利益率", f"{margin:.1f}%")

    # ============================================================
    # TAB 7: インポート・設定
    # ============================================================
    with tabs[6]:
        st.header("⚙️ インポート・設定")

        # DB info
        info = db.db_info()
        st.subheader("データベース情報")
        info_cols = st.columns(3)
        for i, (tbl, lbl) in enumerate([("genzai", "派遣社員"), ("ukeoi", "請負社員"), ("staff", "スタッフ")]):
            with info_cols[i]:
                tbl_info = info["tables"].get(tbl, {})
                st.metric(lbl, f"{tbl_info.get('rows', 0)} 件")
                st.caption(f"最終更新: {tbl_info.get('last_updated', '—')}")
        st.caption(f"DB パス: `{info['path']}`")

        st.divider()

        # Import section
        st.subheader("Excelインポート")
        st.info(
            "既存の .xlsm / .xlsx ファイルから全データをインポートします。\n"
            "**⚠️ 既存のDBデータは全て上書きされます。**"
        )

        uploaded = st.file_uploader(
            "社員台帳 Excelファイルをアップロード",
            type=["xlsm", "xlsx"],
            key="import_uploader",
        )

        if uploaded:
            st.write(f"ファイル名: **{uploaded.name}** ({uploaded.size:,} bytes)")

            confirm_import = st.checkbox("上書きを確認しました", key="import_confirm")

            if confirm_import and st.button("🚀 インポート開始", type="primary"):
                # Save to temp file
                suffix = Path(uploaded.name).suffix
                tmp = Path(tempfile.gettempdir()) / f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"
                tmp.write_bytes(uploaded.getvalue())

                progress_bar = st.progress(0.0, text="インポート準備中…")
                status_text = st.empty()

                def on_progress(msg: str, frac: float):
                    progress_bar.progress(min(frac, 1.0), text=msg)
                    status_text.write(msg)

                try:
                    counts = db.import_from_excel(str(tmp), progress_callback=on_progress)
                    progress_bar.progress(1.0, text="完了！")
                    st.success(
                        f"✅ インポート完了！\n"
                        f"- 派遣社員: {counts.get('genzai', 0)} 件\n"
                        f"- 請負社員: {counts.get('ukeoi', 0)} 件\n"
                        f"- スタッフ: {counts.get('staff', 0)} 件"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ インポートエラー: {e}")
                    logger.exception("Import failed")
                finally:
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

        st.divider()

        # Export section
        st.subheader("データエクスポート")
        exp_format = st.radio("フォーマット", ["CSV", "Excel"], horizontal=True)
        exp_table = st.selectbox("対象テーブル", ["全員", "派遣社員", "請負社員", "スタッフ"])

        if st.button("📥 エクスポート準備"):
            table_map = {"派遣社員": "genzai", "請負社員": "ukeoi", "スタッフ": "staff"}
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            if exp_table == "全員":
                dfs = {lbl: db.get_all(tbl) for tbl, lbl in [("genzai","派遣"), ("ukeoi","請負"), ("staff","スタッフ")]}
            else:
                tbl = table_map[exp_table]
                dfs = {exp_table: db.get_all(tbl)}

            if exp_format == "CSV":
                for lbl, df in dfs.items():
                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button(
                        f"📥 {lbl} CSV",
                        csv_bytes,
                        f"{lbl}_{ts}.csv",
                        "text/csv",
                        key=f"dl_{lbl}",
                    )
            else:
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    for lbl, df in dfs.items():
                        df.to_excel(writer, sheet_name=lbl[:31], index=False)
                st.download_button(
                    "📥 Excel ダウンロード",
                    buf.getvalue(),
                    f"shain_daicho_{ts}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


if __name__ == "__main__":
    main()
