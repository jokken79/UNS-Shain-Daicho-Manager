#!/usr/bin/env python3
"""Unit tests for ShainDaicho core behavior."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / 'src'))

from shain_utils import ShainDaicho


class TestShainDaicho(unittest.TestCase):
    """Covers core loading, querying, and export behavior."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.work_dir = Path(cls.temp_dir.name)
        cls.excel_path = cls.work_dir / 'sample_employees.xlsx'

        df_genzai = pd.DataFrame([
            {
                '社員№': 1001,
                '氏名': 'NGUYEN TEST',
                'カナ': 'グエン テスト',
                '現在': '在職中',
                '派遣先': 'Company A',
                '国籍': 'ベトナム',
                '入社日': '2024-01-01',
                'ビザ期限': '2099-12-31',
                'ビザ種類': 'Engineer',
                '時給': 1200,
                '請求単価': 1800,
                '差額利益': 600,
                '年齢': 27,
            },
            {
                '社員№': 1002,
                '氏名': 'SATO RETIRED',
                'カナ': 'サトウ',
                '現在': '退職',
                '派遣先': 'Company B',
                '国籍': '日本',
                '入社日': '2020-01-01',
                'ビザ期限': None,
                'ビザ種類': None,
                '時給': 1100,
                '請求単価': 1600,
                '差額利益': 500,
                '年齢': 44,
            },
        ])

        df_ukeoi = pd.DataFrame([
            {
                '社員№': 2001,
                '氏名': 'TANAKA CONTRACT',
                'カナ': 'タナカ',
                '現在': '在職中',
                '国籍': '日本',
                '入社日': '2022-03-01',
                'ビザ期限': None,
                'ビザ種類': None,
                '年齢': 36,
            }
        ])

        df_staff = pd.DataFrame([
            {
                '社員№': 3001,
                '氏名': 'STAFF ONE',
                'カナ': 'スタッフ',
                '国籍': '日本',
                '入社日': '2021-05-01',
                '退社日': pd.NaT,
                'ビザ期限': None,
                'ビザ種類': None,
                '年齢': 33,
            }
        ])

        with pd.ExcelWriter(cls.excel_path, engine='openpyxl') as writer:
            df_genzai.to_excel(writer, sheet_name='DBGenzaiX', index=False)
            df_ukeoi.to_excel(writer, sheet_name='DBUkeoiX', index=False)
            df_staff.to_excel(writer, sheet_name='DBStaffX', index=False)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def _load_daicho(self) -> ShainDaicho:
        sd = ShainDaicho(str(self.excel_path))
        self.assertTrue(sd.load())
        return sd

    def test_summary_counts(self):
        sd = self._load_daicho()
        stats = sd.get_summary_stats()

        self.assertEqual(stats['total']['total'], 4)
        self.assertEqual(stats['total']['active'], 3)
        self.assertEqual(stats['total']['retired'], 1)

    def test_search_employee_case_insensitive(self):
        sd = self._load_daicho()
        results = sd.search_employee('nguyen')

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'NGUYEN TEST')

    def test_calculate_profit_margin_handles_zero_values(self):
        sd = self._load_daicho()
        result = sd.calculate_profit_margin(seikyu=0, jikyu=0)

        self.assertNotIn('error', result)
        self.assertEqual(result['margin_rate_percent'], 0)

    def test_export_excel_adds_extension(self):
        sd = self._load_daicho()
        export_base = self.work_dir / 'exports' / 'active_employees'

        result = sd.export_active_employees(str(export_base), format='excel')

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.xlsx'))
        self.assertTrue(Path(result).exists())

    def test_export_csv_writes_category_files(self):
        sd = self._load_daicho()
        export_base = self.work_dir / 'exports' / 'active_employees.csv'

        result = sd.export_active_employees(str(export_base), format='csv')

        self.assertIsNotNone(result)
        export_dir = Path(result)
        self.assertTrue((export_dir / 'active_employees_派遣.csv').exists())
        self.assertTrue((export_dir / 'active_employees_請負.csv').exists())
        self.assertTrue((export_dir / 'active_employees_Staff.csv').exists())


if __name__ == '__main__':
    unittest.main()
