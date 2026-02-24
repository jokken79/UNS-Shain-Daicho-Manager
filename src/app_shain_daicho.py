#!/usr/bin/env python3
"""
UNS 社員台帳 Management Dashboard
Interactive Streamlit application for employee data management
"""

import hashlib
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shain_utils import ShainDaicho

# Configure Streamlit
st.set_page_config(
    page_title="UNS 社員台帳 Manager",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ffcccb;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-warning {
        background-color: #ffe4b5;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-info {
        background-color: #e6f3ff;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_shain_daicho(filepath: str, cache_key: str):
    """Load ShainDaicho with caching keyed by file contents."""
    _ = cache_key
    sd = ShainDaicho(filepath)
    if sd.load():
        return sd

    logger.error(f"Failed to load data file: {filepath}")
    return None


def format_number(num):
    """Format number in Japanese style"""
    if pd.isna(num):
        return "N/A"
    return f"{int(num):,}"


def main():
    # Title
    st.title("👥 UNS 社員台帳 Manager")
    st.markdown("**Employee Registry Management System**")

    sd = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # File upload
        uploaded_file = st.file_uploader(
            "📁 Upload 社員台帳 Excel file",
            type=['xlsm', 'xlsx'],
            help="Upload your employee registry file"
        )
        
        if uploaded_file:
            # Save temporary file (cross-platform)
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            safe_name = Path(uploaded_file.name).name
            suffix = Path(safe_name).suffix or '.xlsx'
            temp_path = Path(tempfile.gettempdir()) / f"shain_daicho_{file_hash[:16]}{suffix}"

            if not temp_path.exists():
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)

            # Load data
            sd = load_shain_daicho(str(temp_path), file_hash)
            
            if sd and sd._loaded:
                st.success("✅ Data loaded successfully!")
                
                # Display load info
                if sd._load_timestamp:
                    st.caption(f"Loaded: {sd._load_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Validation checks
                errors = sd.get_validation_errors()
                if errors:
                    with st.expander("⚠️ Validation Notes"):
                        for error in errors:
                            st.warning(error)
            else:
                st.error("Failed to load data file")
        else:
            st.info("👆 Upload an Excel file to get started")
            return
    
    if not sd or not sd._loaded:
        st.warning("Please upload a file first")
        return
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard",
        "👤 Search",
        "🔔 Visa Alerts",
        "💰 Salary Analysis",
        "📈 Reports",
        "⚙️ Export"
    ])
    
    # ==================== TAB 1: DASHBOARD ====================
    with tab1:
        st.header("📊 Dashboard Overview")
        
        # Get summary stats
        stats = sd.get_summary_stats()
        total_stats = stats.get('total', {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Employees",
                format_number(total_stats.get('total', 0)),
                help="Total registered employees"
            )
        
        with col2:
            active = total_stats.get('active', 0)
            total = total_stats.get('total', 1)
            percentage = (active / total * 100) if total > 0 else 0
            st.metric(
                "Active Employees",
                format_number(active),
                f"{percentage:.1f}%"
            )
        
        with col3:
            st.metric(
                "Retired/Inactive",
                format_number(total_stats.get('retired', 0))
            )
        
        with col4:
            st.metric(
                "Load Date",
                sd._load_timestamp.strftime('%Y-%m-%d') if sd._load_timestamp else "N/A"
            )
        
        # Employee breakdown by category
        st.subheader("Employee Distribution by Category")
        
        breakdown_data = {
            'Category': ['派遣社員', '請負社員', 'スタッフ'],
            'Active': [
                stats['派遣社員']['active'],
                stats['請負社員']['active'],
                stats['スタッフ']['active']
            ],
            'Retired': [
                stats['派遣社員']['retired'],
                stats['請負社員']['retired'],
                stats['スタッフ']['retired']
            ]
        }
        breakdown_df = pd.DataFrame(breakdown_data)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = go.Figure(data=[
                go.Bar(name='Active', x=breakdown_df['Category'], y=breakdown_df['Active'], marker_color='#1f77b4'),
                go.Bar(name='Retired', x=breakdown_df['Category'], y=breakdown_df['Retired'], marker_color='#d62728')
            ])
            fig.update_layout(
                barmode='stack',
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
        
        # Nationality breakdown
        st.subheader("Nationality Distribution")
        
        nationality = sd.get_nationality_breakdown()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**派遣社員**")
            nat_genzai = nationality.get('派遣', {})
            nat_genzai_sorted = dict(sorted(nat_genzai.items(), key=lambda x: x[1], reverse=True))
            st.dataframe(
                pd.DataFrame(list(nat_genzai_sorted.items()), columns=['Nationality', 'Count']),
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.write("**請負社員**")
            nat_ukeoi = nationality.get('請負', {})
            nat_ukeoi_sorted = dict(sorted(nat_ukeoi.items(), key=lambda x: x[1], reverse=True))
            st.dataframe(
                pd.DataFrame(list(nat_ukeoi_sorted.items()), columns=['Nationality', 'Count']),
                hide_index=True,
                use_container_width=True
            )
        
        with col3:
            st.write("**Staff**")
            nat_staff = nationality.get('Staff', {})
            nat_staff_sorted = dict(sorted(nat_staff.items(), key=lambda x: x[1], reverse=True))
            st.dataframe(
                pd.DataFrame(list(nat_staff_sorted.items()), columns=['Nationality', 'Count']),
                hide_index=True,
                use_container_width=True
            )
        
        # Top companies
        st.subheader("Top 派遣先 Companies")
        
        hakensaki = sd.get_hakensaki_breakdown(top_n=10)
        if hakensaki:
            haken_df = pd.DataFrame(hakensaki)
            
            fig = px.bar(
                haken_df,
                x='company',
                y='count',
                title='Employee Distribution by Dispatch Company',
                labels={'company': 'Company', 'count': 'Number of Employees'},
                height=400
            )
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Show data table"):
                st.dataframe(haken_df, hide_index=True, use_container_width=True)
    
    # ==================== TAB 2: SEARCH ====================
    with tab2:
        st.header("👤 Search Employees")
        
        search_name = st.text_input(
            "Search by name (partial match supported)",
            placeholder="e.g., NGUYEN, 田中"
        )
        
        if search_name:
            results = sd.search_employee(search_name)
            
            if results:
                st.success(f"Found {len(results)} employee(s)")
                
                for i, result in enumerate(results):
                    with st.expander(f"**{result['name']}** ({result['category']}) - ID: {result['employee_id']}", expanded=i==0):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Category:** {result['category']}")
                            st.write(f"**Status:** {result['status']}")
                            st.write(f"**Name (Kana):** {result['kana']}")
                        
                        with col2:
                            st.write(f"**Nationality:** {result['nationality']}")
                            st.write(f"**Hire Date:** {result['hire_date']}")
                        
                        with col3:
                            if result['category'] == '派遣':
                                company = result['data'].get('派遣先', 'N/A')
                                st.write(f"**派遣先:** {company}")
                                hourly = result['data'].get('時給', 'N/A')
                                st.write(f"**時給:** {hourly}")
                        
                        # Full data
                        with st.expander("View all data"):
                            st.dataframe(
                                pd.DataFrame([result['data']]).T,
                                use_container_width=True
                            )
            else:
                st.warning("No employees found matching that name")
        else:
            st.info("Enter a name to search")
    
    # ==================== TAB 3: VISA ALERTS ====================
    with tab3:
        st.header("🔔 Visa Expiration Alerts")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            days_range = st.slider(
                "Days until expiration",
                min_value=1,
                max_value=180,
                value=90,
                step=1
            )
        
        with col2:
            st.info(f"Showing visas expiring within {days_range} days")
        
        alerts = sd.get_visa_alerts(days=days_range)
        
        if alerts:
            # Group by alert level
            critical = [a for a in alerts if a['alert_level'].startswith('🔴')]
            warning = [a for a in alerts if a['alert_level'].startswith('🟠')]
            upcoming = [a for a in alerts if a['alert_level'].startswith('🟡')]
            
            # Display counts
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔴 URGENT/EXPIRED", len(critical), help="Visa expired or expiring within 30 days")
            with col2:
                st.metric("🟠 WARNING", len(warning), help="Expiring within 30-60 days")
            with col3:
                st.metric("🟡 UPCOMING", len(upcoming), help="Expiring within 60-90 days")
            with col4:
                st.metric("Total Alerts", len(alerts))
            
            # Display alerts by category
            st.subheader("Detailed Alerts")
            
            for category in ['派遣', '請負', 'Staff']:
                category_alerts = [a for a in alerts if a['category'] == category]
                
                if category_alerts:
                    with st.expander(f"{category} ({len(category_alerts)} alerts)", expanded=category=='派遣'):
                        alerts_df = pd.DataFrame(category_alerts)[
                            ['employee_id', 'name', 'visa_type', 'expiry_date', 'days_left', 'alert_level']
                        ]
                        
                        # Color code by alert level
                        st.dataframe(
                            alerts_df.rename(columns={
                                'employee_id': 'ID',
                                'name': 'Name',
                                'visa_type': 'Visa Type',
                                'expiry_date': 'Expiry Date',
                                'days_left': 'Days Left',
                                'alert_level': 'Level'
                            }),
                            hide_index=True,
                            use_container_width=True
                        )
        else:
            st.success("✅ No visa expiration alerts within the specified period")
    
    # ==================== TAB 4: SALARY ANALYSIS ====================
    with tab4:
        st.header("💰 Salary Analysis")
        
        salary_stats = sd.get_salary_stats(active_only=True)
        
        if salary_stats:
            # Get active employees for detailed analysis
            active = sd.get_active_employees('派遣')
            
            if len(active) > 0:
                # Salary statistics
                st.subheader("Hourly Rate (時給) Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                jikyu_stats = salary_stats.get('時給', {})
                
                with col1:
                    st.metric("Minimum", f"¥{jikyu_stats.get('min', 0):.0f}")
                with col2:
                    st.metric("Maximum", f"¥{jikyu_stats.get('max', 0):.0f}")
                with col3:
                    st.metric("Average", f"¥{jikyu_stats.get('avg', 0):.0f}")
                with col4:
                    st.metric("Median", f"¥{jikyu_stats.get('median', 0):.0f}")
                
                # Distribution chart
                st.subheader("Salary Distribution")
                
                fig = px.histogram(
                    active,
                    x='時給',
                    nbins=30,
                    title='Distribution of Hourly Rates',
                    labels={'時給': 'Hourly Rate (¥)'},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Billing rate analysis
                st.subheader("Billing Rate (請求単価) Analysis")
                
                seikyu_stats = salary_stats.get('請求単価', {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Minimum", f"¥{seikyu_stats.get('min', 0):.0f}")
                with col2:
                    st.metric("Maximum", f"¥{seikyu_stats.get('max', 0):.0f}")
                with col3:
                    st.metric("Average", f"¥{seikyu_stats.get('avg', 0):.0f}")
                with col4:
                    st.metric("Median", f"¥{seikyu_stats.get('median', 0):.0f}")
                
                fig = px.scatter(
                    active,
                    x='時給',
                    y='請求単価',
                    color='差額利益',
                    size='差額利益',
                    title='Hourly Rate vs Billing Rate',
                    labels={
                        '時給': 'Hourly Rate (¥)',
                        '請求単価': 'Billing Rate (¥)',
                        '差額利益': 'Profit (¥)'
                    },
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Profit analysis
                st.subheader("Profit Analysis (差額利益)")
                
                profit_stats = salary_stats.get('差額利益', {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Minimum", f"¥{profit_stats.get('min', 0):.0f}")
                with col2:
                    st.metric("Maximum", f"¥{profit_stats.get('max', 0):.0f}")
                with col3:
                    st.metric("Average", f"¥{profit_stats.get('avg', 0):.0f}")
                with col4:
                    st.metric("Total", f"¥{profit_stats.get('avg', 0) * profit_stats.get('count', 0):.0f}")
                
                fig = px.box(
                    active,
                    y='差額利益',
                    title='Profit Distribution',
                    labels={'差額利益': 'Profit (¥)'},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No active dispatch employees to analyze")
        else:
            st.warning("Could not load salary statistics")
    
    # ==================== TAB 5: REPORTS ====================
    with tab5:
        st.header("📈 Reports")
        
        report_type = st.radio(
            "Select Report Type",
            ["Employee List", "Age Distribution", "Tenure Report", "Custom Analysis"]
        )
        
        if report_type == "Employee List":
            st.subheader("Active Employees List")
            
            category = st.selectbox(
                "Filter by category",
                ["All", "派遣", "請負", "Staff"]
            )
            
            if category == "All":
                active_data = sd.get_active_employees()
                if isinstance(active_data, dict) and active_data:
                    all_employees = pd.concat(active_data.values(), ignore_index=True)
                else:
                    all_employees = pd.DataFrame()
            else:
                cat_map = {'派遣': '派遣', '請負': '請負', 'Staff': 'Staff'}
                filtered = sd.get_active_employees(cat_map[category])
                all_employees = filtered if isinstance(filtered, pd.DataFrame) else pd.DataFrame()
            
            employees_df = all_employees if isinstance(all_employees, pd.DataFrame) else pd.DataFrame()

            if len(employees_df) > 0:
                st.dataframe(employees_df, use_container_width=True, height=500)
                
                # Download option
                csv = employees_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
            else:
                st.warning("No employees found")
        
        elif report_type == "Age Distribution":
            st.subheader("Age Distribution Analysis")
            
            age_breakdown = sd.get_age_breakdown()
            
            age_data = []
            for category, age_groups in age_breakdown.items():
                for group, count in age_groups.items():
                    age_data.append({
                        'Category': category,
                        'Age Group': group,
                        'Count': count
                    })
            
            age_df = pd.DataFrame(age_data)
            
            fig = px.bar(
                age_df,
                x='Age Group',
                y='Count',
                color='Category',
                title='Employee Distribution by Age Group',
                barmode='group',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(age_df.pivot(index='Age Group', columns='Category', values='Count').fillna(0).astype(int), use_container_width=True)
        
        elif report_type == "Tenure Report":
            st.subheader("Employee Tenure Analysis")
            
            active_emp = sd.get_active_employees()
            today = pd.Timestamp.now()
            
            tenure_data = []
            for category, df in active_emp.items():
                if '入社日' in df.columns:
                    df_copy = df.copy()
                    df_copy['入社日'] = pd.to_datetime(df_copy['入社日'], errors='coerce')
                    df_copy = df_copy[df_copy['入社日'].notna()]
                    
                    df_copy['tenure_days'] = (today - df_copy['入社日']).dt.days
                    df_copy['tenure_years'] = df_copy['tenure_days'] / 365.25
                    
                    tenure_data.append(df_copy[['氏名', '入社日', 'tenure_years']].rename(columns={'氏名': 'Name'}))
            
            if tenure_data:
                tenure_df = pd.concat(tenure_data, ignore_index=True)
                tenure_df = tenure_df.sort_values('tenure_years', ascending=False)
                
                fig = px.histogram(
                    tenure_df,
                    x='tenure_years',
                    nbins=20,
                    title='Employee Tenure Distribution',
                    labels={'tenure_years': 'Tenure (Years)'},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Show top 20 longest-serving employees"):
                    st.dataframe(
                        tenure_df.head(20).rename(columns={
                            'Name': 'Employee',
                            '入社日': 'Hire Date',
                            'tenure_years': 'Tenure (Years)'
                        }),
                        hide_index=True,
                        use_container_width=True
                    )
        
        elif report_type == "Custom Analysis":
            st.subheader("Custom Analysis")
            
            st.write("Create your own analysis by selecting parameters:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                x_axis = st.selectbox(
                    "X-axis",
                    ["派遣先", "国籍", "年齢", "ビザ種類"]
                )
            
            with col2:
                y_axis = st.selectbox(
                    "Y-axis (metric)",
                    ["Count", "Average Salary", "Average Profit"]
                )
            
            try:
                active = sd.get_active_employees('派遣')
                
                if x_axis == "派遣先" and y_axis == "Count":
                    data = active[x_axis].value_counts().head(15)
                    fig = px.bar(
                        x=data.index,
                        y=data.values,
                        title=f"{x_axis} vs {y_axis}",
                        labels={'x': x_axis, 'y': y_axis},
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating chart: {e}")
    
    # ==================== TAB 6: EXPORT ====================
    with tab6:
        st.header("⚙️ Export Data")
        
        export_format = st.radio(
            "Select export format",
            ["Excel", "JSON", "CSV"]
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("📥 Generate Export"):
                with st.spinner("Generating export..."):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        if export_format == "Excel":
                            output_path = Path(tempfile.gettempdir()) / f"employees_export_{timestamp}.xlsx"
                            result = sd.export_active_employees(str(output_path), format='excel')
                            
                            if result:
                                with open(result, 'rb') as f:
                                    st.download_button(
                                        "📥 Download Excel",
                                        f.read(),
                                        f"employees_{timestamp}.xlsx",
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                        
                        elif export_format == "JSON":
                            json_data = sd.to_json_summary()
                            st.download_button(
                                "📥 Download JSON",
                                json_data,
                                f"employees_summary_{timestamp}.json",
                                "application/json"
                            )
                        
                        elif export_format == "CSV":
                            active = sd.get_active_employees()
                            if isinstance(active, dict) and active:
                                csv_frames = [
                                    df for df in active.values()
                                    if isinstance(df, pd.DataFrame)
                                ]
                                if csv_frames:
                                    csv_all = pd.concat(csv_frames, ignore_index=True).to_csv(
                                        index=False,
                                        encoding='utf-8-sig'
                                    )
                                    st.download_button(
                                        "📥 Download CSV",
                                        csv_all,
                                        f"employees_{timestamp}.csv",
                                        "text/csv"
                                    )
                                else:
                                    st.warning("No active records available for CSV export")
                            else:
                                st.warning("No active records available for CSV export")
                        
                        st.success("✅ Export ready!")
                    
                    except Exception as e:
                        st.error(f"Error during export: {e}")
        
        with col2:
            st.info(f"💡 Format: **{export_format}**")
        
        # Display statistics
        st.subheader("Export Statistics")
        
        stats = sd.get_summary_stats()
        total = stats.get('total', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", format_number(total.get('total', 0)))
        with col2:
            st.metric("Active Records", format_number(total.get('active', 0)))
        with col3:
            st.metric("Inactive Records", format_number(total.get('retired', 0)))


if __name__ == "__main__":
    main()
