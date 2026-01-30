// Column mappings: Japanese to English
export const COLUMN_MAPPINGS = {
  '社員№': 'employeeId',
  '氏名': 'name',
  'カナ': 'nameKana',
  '現在': 'currentStatus',
  '国籍': 'nationality',
  '入社日': 'hireDate',
  '退社日': 'resignationDate',
  'ビザ期限': 'visaExpiry',
  'ビザ種類': 'visaType',
  '時給': 'hourlyRate',
  '請求単価': 'billingRate',
  '差額利益': 'profitMargin',
  '派遣先': 'dispatchCompany',
  '年齢': 'age',
} as const;

// Sheet names in Excel files
export const SHEET_NAMES = {
  DISPATCH: 'DBGenzaiX',    // 派遣社員 - Dispatch workers
  CONTRACT: 'DBUkeoiX',     // 請負社員 - Contract workers
  STAFF: 'DBStaffX',        // スタッフ - Administrative staff
  FORMER: 'DBTaishaX',      // 退社者 - Former employees
} as const;

// Status values
export const STATUS = {
  ACTIVE: '在職中',          // Currently employed
  INACTIVE: '退社',         // Resigned/Left
} as const;

// Configuration values
export const CONFIG = {
  COMPANY_BURDEN_RATE: 15.76, // Percentage for profit calculation
  VISA_THRESHOLDS: {
    CRITICAL: 30,   // days - 🔴 URGENT
    WARNING: 60,    // days - 🟠 WARNING
    UPCOMING: 90,   // days - 🟡 UPCOMING
  },
  AGE_GROUPS: [
    { min: 0, max: 19, label: 'Under 20' },
    { min: 20, max: 29, label: '20-29' },
    { min: 30, max: 39, label: '30-39' },
    { min: 40, max: 49, label: '40-49' },
    { min: 50, max: 59, label: '50-59' },
    { min: 60, max: 999, label: '60+' },
  ],
  DEFAULT_TOP_N: 15,
} as const;

// Category labels
export const CATEGORY_LABELS = {
  '派遣社員': 'Dispatch Workers',
  '請負社員': 'Contract Workers',
  'スタッフ': 'Staff',
  '退社者': 'Former Employees',
} as const;
