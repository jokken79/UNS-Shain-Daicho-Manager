#!/usr/bin/env python3
"""
UNS 社員台帳 Parser & Manager
Utility functions for parsing and managing UNS employee registry data.

Usage:
    from shain_utils import ShainDaicho
    
    sd = ShainDaicho('/path/to/社員台帳.xlsm')
    sd.load()
    
    # Get active employees
    active = sd.get_active_employees()
    
    # Search employee
    results = sd.search_employee('NGUYEN')
    
    # Get visa alerts
    alerts = sd.get_visa_alerts(days=90)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Union
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShainDaicho:
    """Main class for managing 社員台帳 data"""
    
    # Sheet names
    SHEET_GENZAI = 'DBGenzaiX'  # Dispatch workers (派遣社員)
    SHEET_UKEOI = 'DBUkeoiX'     # Contract workers (請負社員)
    SHEET_STAFF = 'DBStaffX'     # Staff (スタッフ)
    SHEET_TAISHA = 'DBTaishaX'   # Former employees (退社者)
    
    # Company burden rate for profit calculation
    COMPANY_BURDEN_RATE = 0.1576
    
    def __init__(self, filepath: str):
        """Initialize with Excel file path"""
        self.filepath = Path(filepath)
        self.df_genzai = None
        self.df_ukeoi = None
        self.df_staff = None
        self.df_taisha = None
        self._loaded = False
        self._load_timestamp = None
        self._validation_errors = []
        
    @classmethod
    def from_dataframes(
        cls,
        df_genzai: pd.DataFrame,
        df_ukeoi: pd.DataFrame,
        df_staff: pd.DataFrame,
        df_taisha: Optional[pd.DataFrame] = None,
    ) -> 'ShainDaicho':
        """
        Construct a ShainDaicho instance from pre-loaded DataFrames.
        Useful when data is sourced from SQLite rather than Excel.

        Example::

            db = ShainDatabase('data/shain_daicho.db')
            sd = ShainDaicho.from_dataframes(
                db.get_all('genzai'),
                db.get_all('ukeoi'),
                db.get_all('staff'),
            )
            print(sd.get_summary_stats())
        """
        instance = cls.__new__(cls)
        instance.filepath = Path('<in-memory>')
        instance.df_genzai = df_genzai.copy()
        instance.df_ukeoi = df_ukeoi.copy()
        instance.df_staff = df_staff.copy()
        instance.df_taisha = df_taisha.copy() if df_taisha is not None else None
        instance._loaded = True
        instance._load_timestamp = datetime.now()
        instance._validation_errors = []
        instance._validate_data()
        return instance

    def load(self) -> bool:
        """Load all sheets from the Excel file with error handling"""
        try:
            if not self.filepath.exists():
                logger.error(f"File not found: {self.filepath}")
                return False
            
            logger.info(f"Loading data from {self.filepath.name}")
            
            # Load main sheets
            self.df_genzai = pd.read_excel(
                self.filepath, 
                sheet_name=self.SHEET_GENZAI
            )
            self.df_ukeoi = pd.read_excel(
                self.filepath, 
                sheet_name=self.SHEET_UKEOI
            )
            self.df_staff = pd.read_excel(
                self.filepath, 
                sheet_name=self.SHEET_STAFF
            )
            
            # Try to load former employees sheet
            try:
                self.df_taisha = pd.read_excel(
                    self.filepath, 
                    sheet_name=self.SHEET_TAISHA
                )
            except Exception as e:
                logger.warning(f"Could not load {self.SHEET_TAISHA}: {e}")
                self.df_taisha = None
            
            # Validate data
            self._validate_data()
            
            self._loaded = True
            self._load_timestamp = datetime.now()
            
            logger.info(
                f"✅ Loaded: {len(self.df_genzai)} 派遣, "
                f"{len(self.df_ukeoi)} 請負, {len(self.df_staff)} Staff"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self._loaded = False
            return False
    
    def _validate_data(self) -> None:
        """Validate data integrity"""
        self._validation_errors = []
        
        # Check required columns in each sheet
        required_cols = {
            'genzai': ['社員№', '氏名', '現在', '派遣先'],
            'ukeoi': ['社員№', '氏名', '現在'],
            'staff': ['社員№', '氏名']
        }
        
        for sheet_name, cols in required_cols.items():
            if sheet_name == 'genzai':
                df = self.df_genzai
            elif sheet_name == 'ukeoi':
                df = self.df_ukeoi
            else:
                df = self.df_staff
            
            missing = [col for col in cols if col not in df.columns]
            if missing:
                self._validation_errors.append(
                    f"Sheet {sheet_name}: missing columns {missing}"
                )
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self._validation_errors
    
    def _ensure_loaded(self) -> None:
        """Ensure data is loaded"""
        if not self._loaded:
            raise RuntimeError(
                "Data not loaded. Call load() first. "
                "Use: sd = ShainDaicho('path'); sd.load()"
            )

    @staticmethod
    def _coerce_float(value: Optional[Union[float, int, str]]) -> Optional[float]:
        """Safely coerce numeric values to float."""
        if value is None:
            return None

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None

        if np.isnan(parsed):
            return None

        return parsed
    
    # ==================== EMPLOYEE QUERIES ====================
    
    def get_active_employees(
        self, 
        category: str = 'all'
    ) -> Union[Dict[str, pd.DataFrame], pd.DataFrame]:
        """Get active employees (在職中) by category"""
        self._ensure_loaded()
        
        results = {}
        
        try:
            if category in ['all', 'genzai', '派遣']:
                active_genzai = self.df_genzai[
                    self.df_genzai['現在'] == '在職中'
                ].copy()
                results['派遣'] = active_genzai
            
            if category in ['all', 'ukeoi', '請負']:
                active_ukeoi = self.df_ukeoi[
                    self.df_ukeoi['現在'] == '在職中'
                ].copy()
                results['請負'] = active_ukeoi
            
            if category in ['all', 'staff', 'スタッフ']:
                # For staff, check if they have an 入社日 but no 退社日
                if '入社日' in self.df_staff.columns and '退社日' in self.df_staff.columns:
                    active_staff = self.df_staff[
                        (self.df_staff['入社日'].notna()) & 
                        (self.df_staff['退社日'].isna())
                    ].copy()
                else:
                    # Fallback: all staff records
                    active_staff = self.df_staff.copy()
                results['Staff'] = active_staff
            
            if category == 'all':
                return results
            
            # Return single category
            if category in ['genzai', '派遣']:
                return results.get('派遣', pd.DataFrame())
            elif category in ['ukeoi', '請負']:
                return results.get('請負', pd.DataFrame())
            elif category in ['staff', 'スタッフ']:
                return results.get('Staff', pd.DataFrame())
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting active employees: {e}")
            return {} if category == 'all' else pd.DataFrame()
    
    def search_employee(
        self, 
        name: str, 
        active_only: bool = False
    ) -> List[Dict]:
        """Search employee by name across all categories"""
        self._ensure_loaded()
        
        results = []
        
        try:
            datasets = [
                (self.df_genzai, '派遣', '現在'),
                (self.df_ukeoi, '請負', '現在'),
                (self.df_staff, 'Staff', None)
            ]
            
            for df, category, status_col in datasets:
                search_df = df
                
                # Filter by status if specified
                if active_only and status_col and status_col in df.columns:
                    search_df = df[df[status_col] == '在職中']
                
                # Search by name (case-insensitive, partial match)
                if '氏名' in search_df.columns:
                    matches = search_df[
                        search_df['氏名'].astype(str).str.contains(
                            name, na=False, case=False, regex=False
                        )
                    ]
                    
                    for _, row in matches.iterrows():
                        results.append({
                            'category': category,
                            'status': row.get(status_col, 'Unknown') if status_col else 'N/A',
                            'employee_id': row.get('社員№'),
                            'name': row.get('氏名'),
                            'kana': row.get('カナ'),
                            'nationality': row.get('国籍'),
                            'hire_date': row.get('入社日'),
                            'data': row.to_dict()
                        })
            
            logger.info(f"Found {len(results)} employees matching '{name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching employee: {e}")
            return []
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict]:
        """Get employee by 社員№"""
        self._ensure_loaded()
        
        try:
            datasets = [
                (self.df_genzai, '派遣'),
                (self.df_ukeoi, '請負'),
                (self.df_staff, 'Staff')
            ]
            
            for df, category in datasets:
                if '社員№' not in df.columns:
                    continue
                    
                matches = df[df['社員№'] == employee_id]
                if len(matches) > 0:
                    row = matches.iloc[0]
                    return {
                        'category': category,
                        'status': row.get('現在', 'Unknown'),
                        'data': row.to_dict()
                    }
            
            logger.warning(f"Employee ID {employee_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting employee by ID: {e}")
            return None
    
    # ==================== STATISTICS ====================
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        self._ensure_loaded()
        
        def count_status(df: pd.DataFrame, status_col: Optional[str]) -> Dict:
            """Count employees by status"""
            if status_col and status_col in df.columns:
                active = len(df[df[status_col] == '在職中'])
            else:
                # For staff without explicit status, count all
                active = len(df)
            
            total = len(df)
            return {'total': total, 'active': active, 'retired': total - active}
        
        try:
            genzai_stats = count_status(self.df_genzai, '現在')
            ukeoi_stats = count_status(self.df_ukeoi, '現在')
            staff_stats = count_status(self.df_staff, None)
            
            return {
                '派遣社員': genzai_stats,
                '請負社員': ukeoi_stats,
                'スタッフ': staff_stats,
                'total': {
                    'total': (genzai_stats['total'] + ukeoi_stats['total'] + 
                             staff_stats['total']),
                    'active': (genzai_stats['active'] + ukeoi_stats['active'] + 
                              staff_stats['active']),
                    'retired': (genzai_stats['retired'] + ukeoi_stats['retired'] + 
                               staff_stats['retired'])
                }
            }
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}
    
    def get_salary_stats(self, active_only: bool = True) -> Dict:
        """Get salary statistics for 派遣社員"""
        self._ensure_loaded()
        
        try:
            df = self.df_genzai
            if active_only:
                df = df[df['現在'] == '在職中']
            
            # Extract salary columns with error handling
            jikyu = pd.to_numeric(df['時給'], errors='coerce').dropna()
            seikyu = pd.to_numeric(df['請求単価'], errors='coerce').dropna()
            profit = pd.to_numeric(df['差額利益'], errors='coerce').dropna()
            
            def stats_for_series(series: pd.Series) -> Dict:
                """Calculate min, max, avg for a series"""
                if len(series) == 0:
                    return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
                return {
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'avg': float(series.mean()),
                    'median': float(series.median()),
                    'count': len(series)
                }
            
            return {
                '時給': stats_for_series(jikyu),
                '請求単価': stats_for_series(seikyu),
                '差額利益': stats_for_series(profit)
            }
        except Exception as e:
            logger.error(f"Error getting salary stats: {e}")
            return {}
    
    def get_hakensaki_breakdown(self, top_n: int = 15) -> List[Dict]:
        """Get breakdown by 派遣先 company"""
        self._ensure_loaded()
        
        try:
            if '派遣先' not in self.df_genzai.columns:
                logger.warning("派遣先 column not found")
                return []
            
            counts = self.df_genzai['派遣先'].value_counts().head(top_n)
            return [
                {
                    'company': str(name), 
                    'count': int(count),
                    'percentage': round((count / len(self.df_genzai)) * 100, 1)
                } 
                for name, count in counts.items() 
                if pd.notna(name)
            ]
        except Exception as e:
            logger.error(f"Error getting hakensaki breakdown: {e}")
            return []
    
    def get_nationality_breakdown(self) -> Dict:
        """Get breakdown by nationality"""
        self._ensure_loaded()
        
        try:
            result = {}
            for df, category in [
                (self.df_genzai, '派遣'),
                (self.df_ukeoi, '請負'),
                (self.df_staff, 'Staff')
            ]:
                if '国籍' not in df.columns:
                    result[category] = {}
                    continue
                
                counts = df['国籍'].value_counts().to_dict()
                result[category] = {
                    str(k): int(v) 
                    for k, v in counts.items() 
                    if pd.notna(k)
                }
            return result
        except Exception as e:
            logger.error(f"Error getting nationality breakdown: {e}")
            return {}
    
    def get_age_breakdown(self) -> Dict:
        """Get breakdown by age group"""
        self._ensure_loaded()
        
        try:
            result = {}
            age_bins = [0, 20, 30, 40, 50, 60, 100]
            age_labels = ['<20', '20-29', '30-39', '40-49', '50-59', '60+']
            
            for df, category in [
                (self.df_genzai, '派遣'),
                (self.df_ukeoi, '請負'),
                (self.df_staff, 'Staff')
            ]:
                if '年齢' not in df.columns:
                    result[category] = {}
                    continue
                
                ages = pd.to_numeric(df['年齢'], errors='coerce')
                age_groups = pd.cut(ages, bins=age_bins, labels=age_labels)
                counts = age_groups.value_counts().sort_index().to_dict()
                
                result[category] = {str(k): int(v) for k, v in counts.items()}
            
            return result
        except Exception as e:
            logger.error(f"Error getting age breakdown: {e}")
            return {}
    
    # ==================== VISA MANAGEMENT ====================
    
    def get_visa_alerts(
        self, 
        days: int = 90, 
        active_only: bool = True
    ) -> List[Dict]:
        """Get employees with visa expiring within specified days"""
        self._ensure_loaded()

        days = max(int(days), 0)
        reference_now = datetime.now()
        cutoff = reference_now + timedelta(days=days)
        alerts = []
        
        try:
            datasets = [
                (self.df_genzai, '派遣', '現在'),
                (self.df_ukeoi, '請負', '現在'),
                (self.df_staff, 'Staff', None)
            ]
            
            for df, category, status_col in datasets:
                work_df = df
                
                # Filter by status if specified
                if active_only and status_col and status_col in df.columns:
                    work_df = df[df[status_col] == '在職中']
                
                if 'ビザ期限' not in work_df.columns:
                    continue
                
                work_df = work_df.copy()
                work_df['visa_date'] = pd.to_datetime(
                    work_df['ビザ期限'], 
                    errors='coerce'
                )
                
                expiring = work_df[
                    (work_df['visa_date'].notna()) & 
                    (work_df['visa_date'] <= cutoff)
                ]
                
                for _, row in expiring.iterrows():
                    visa_date = row['visa_date']
                    days_left = (visa_date - reference_now).days
                    
                    # Alert level based on days remaining
                    if days_left <= 0:
                        alert_level = '🔴 EXPIRED'
                    elif days_left <= 30:
                        alert_level = '🔴 URGENT'
                    elif days_left <= 60:
                        alert_level = '🟠 WARNING'
                    else:
                        alert_level = '🟡 UPCOMING'
                    
                    alerts.append({
                        'category': category,
                        'employee_id': row.get('社員№'),
                        'name': row.get('氏名'),
                        'visa_type': row.get('ビザ種類', 'Unknown'),
                        'expiry_date': visa_date.strftime('%Y-%m-%d'),
                        'days_left': days_left,
                        'alert_level': alert_level
                    })
            
            # Sort by days left
            alerts.sort(key=lambda x: x['days_left'])
            logger.info(f"Found {len(alerts)} visa alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting visa alerts: {e}")
            return []
    
    # ==================== PROFIT CALCULATION ====================
    
    def calculate_profit_margin(
        self, 
        employee_id: Optional[int] = None, 
        seikyu: Optional[float] = None, 
        jikyu: Optional[float] = None
    ) -> Dict:
        """Calculate profit margin for dispatch employee"""
        self._ensure_loaded()
        
        try:
            if employee_id:
                emp = self.get_employee_by_id(employee_id)
                if emp and emp['category'] == '派遣':
                    seikyu = emp['data'].get('請求単価')
                    jikyu = emp['data'].get('時給')

            seikyu_value = self._coerce_float(seikyu)
            jikyu_value = self._coerce_float(jikyu)

            if seikyu_value is None or jikyu_value is None:
                return {'error': 'Missing 請求単価 or 時給 data'}

            company_burden = jikyu_value * self.COMPANY_BURDEN_RATE
            gross_profit = seikyu_value - jikyu_value
            net_profit = seikyu_value - jikyu_value - company_burden

            if seikyu_value > 0:
                margin_rate = (gross_profit / seikyu_value) * 100
            else:
                margin_rate = 0

            return {
                '請求単価': round(seikyu_value, 0),
                '時給': round(jikyu_value, 0),
                '差額利益_gross': round(gross_profit, 0),
                '会社負担': round(company_burden, 0),
                '差額利益_net': round(net_profit, 0),
                'margin_rate_percent': round(margin_rate, 1)
            }
        except Exception as e:
            logger.error(f"Error calculating profit margin: {e}")
            return {'error': str(e)}
    
    # ==================== EXPORT ====================
    
    def export_active_employees(
        self, 
        output_path: str, 
        format: str = 'excel'
    ) -> Optional[str]:
        """Export active employees to file"""
        self._ensure_loaded()
        
        try:
            active = self.get_active_employees()
            if not isinstance(active, dict):
                logger.error("Expected a category DataFrame map for active employees")
                return None

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            export_format = format.lower()

            if export_format == 'excel':
                if output_path.suffix.lower() not in ['.xlsx', '.xlsm']:
                    output_path = output_path.with_suffix('.xlsx')

                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for category, df in active.items():
                        df.to_excel(
                            writer, 
                            sheet_name=category[:31],  # Excel sheet name limit
                            index=False
                        )
                logger.info(f"Exported to {output_path}")
                return str(output_path)

            if export_format == 'json':
                if output_path.suffix.lower() != '.json':
                    output_path = output_path.with_suffix('.json')

                result = {
                    cat: df.to_dict('records') 
                    for cat, df in active.items()
                }
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"Exported to {output_path}")
                return str(output_path)

            if export_format == 'csv':
                prefix = output_path.stem if output_path.suffix else output_path.name
                for category, df in active.items():
                    csv_path = output_path.parent / f"{prefix}_{category}.csv"
                    df.to_csv(csv_path, index=False, encoding='utf-8')
                logger.info(f"Exported CSVs to {output_path.parent}")
                return str(output_path.parent)

            logger.error(f"Unsupported export format: {format}")
            return None
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None
    
    def to_json_summary(self) -> str:
        """Export summary as JSON string"""
        self._ensure_loaded()
        
        try:
            return json.dumps(
                {
                    'summary': self.get_summary_stats(),
                    'salary_stats': self.get_salary_stats(),
                    'top_hakensaki': self.get_hakensaki_breakdown(),
                    'nationality': self.get_nationality_breakdown(),
                    'age_groups': self.get_age_breakdown(),
                    'load_timestamp': self._load_timestamp.isoformat() if self._load_timestamp else None
                },
                ensure_ascii=False,
                indent=2,
                default=str
            )
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            return '{}'


# ==================== CLI USAGE ====================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python src/shain_utils.py <path_to_社員台帳.xlsm> [command]")
        print("\nCommands:")
        print("  summary               - Show summary statistics")
        print("  active                - Count active employees")
        print("  visa-alerts [days]    - Show visa expiration alerts (default: 90)")
        print("  search <name>         - Search employee by name")
        print("  export <format>       - Export data (excel|json|csv)")
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print("Usage: python src/shain_utils.py <path_to_社員台帳.xlsm> [command]")
        print("\nCommands:")
        print("  summary               - Show summary statistics")
        print("  active                - Count active employees")
        print("  visa-alerts [days]    - Show visa expiration alerts (default: 90)")
        print("  search <name>         - Search employee by name")
        print("  export <format>       - Export data (excel|json|csv)")
        sys.exit(1)
    
    filepath = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    
    sd = ShainDaicho(filepath)
    if not sd.load():
        sys.exit(1)
    
    # Validation check
    errors = sd.get_validation_errors()
    if errors:
        print("⚠️  Validation warnings:")
        for error in errors:
            print(f"  - {error}")
    
    if command == 'summary':
        print(sd.to_json_summary())
    
    elif command == 'active':
        stats = sd.get_summary_stats()
        total = stats.get('total', {})
        print(f"Active employees: {total.get('active', 0)}/{total.get('total', 0)}")
    
    elif command == 'visa-alerts':
        days = 90
        if len(sys.argv) > 3:
            try:
                days = max(int(sys.argv[3]), 0)
            except ValueError:
                print("❌ Invalid days argument for visa-alerts. Use an integer.")
                sys.exit(1)

        alerts = sd.get_visa_alerts(days=days)
        print(f"Visa alerts (next {days} days): {len(alerts)}\n")
        for alert in alerts[:15]:
            print(f"  {alert['alert_level']} {alert['name']:20} "
                  f"- {alert['expiry_date']} ({alert['days_left']} days)")
    
    elif command == 'search' and len(sys.argv) > 3:
        name = sys.argv[3]
        results = sd.search_employee(name)
        print(f"Found {len(results)} employees matching '{name}':\n")
        for r in results:
            print(f"  [{r['category']}] {r['name']:20} "
                  f"(ID: {r['employee_id']}, {r['nationality']})")

    elif command == 'search':
        print("❌ Missing search name argument")
        sys.exit(1)

    elif command == 'export' and len(sys.argv) > 3:
        format_type = sys.argv[3].lower()
        suffix_map = {'excel': '.xlsx', 'json': '.json', 'csv': ''}

        if format_type not in suffix_map:
            print(f"❌ Unsupported export format: {format_type}")
            sys.exit(1)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suffix = suffix_map[format_type]
        output = f"export_{timestamp}{suffix}" if suffix else f"export_{timestamp}"
        result = sd.export_active_employees(output, format=format_type)
        if result:
            print(f"✅ Exported to {result}")
        else:
            print("❌ Export failed")

    elif command == 'export':
        print("❌ Missing export format argument (excel|json|csv)")
        sys.exit(1)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
