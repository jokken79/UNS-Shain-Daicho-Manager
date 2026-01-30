export interface Employee {
  employeeId: number;           // 社員№
  name: string;                 // 氏名
  nameKana: string;             // カナ
  currentStatus: string;        // 現在 (在職中/退社)
  nationality: string;          // 国籍
  hireDate: Date | null;        // 入社日
  resignationDate: Date | null; // 退社日
  visaExpiry: Date | null;      // ビザ期限
  visaType: string;             // ビザ種類
  hourlyRate: number | null;    // 時給
  billingRate: number | null;   // 請求単価
  profitMargin: number | null;  // 差額利益
  dispatchCompany: string;      // 派遣先
  age: number | null;           // 年齢
  category: EmployeeCategory;   // Categoría del empleado
}

export enum EmployeeCategory {
  DISPATCH = '派遣社員',    // Dispatch workers
  CONTRACT = '請負社員',    // Contract workers
  STAFF = 'スタッフ',       // Administrative staff
  FORMER = '退社者',        // Former employees
}

export interface EmployeeStats {
  total: number;
  active: number;
  inactive: number;
  byCategory: CategoryCount[];
  byNationality: NationalityCount[];
}

export interface CategoryCount {
  category: string;
  total: number;
  active: number;
}

export interface NationalityCount {
  nationality: string;
  count: number;
  percentage: number;
}

export interface VisaAlert {
  employee: Employee;
  daysUntilExpiry: number;
  urgencyLevel: 'critical' | 'warning' | 'upcoming';
  expiryDate: Date;
}

export interface SalaryStats {
  hourlyRate: NumericStats;
  billingRate: NumericStats;
  profitMargin: NumericStats;
}

export interface NumericStats {
  min: number;
  max: number;
  average: number;
  median: number;
  count: number;
}

export interface AgeGroup {
  label: string;
  min: number;
  max: number;
  count: number;
}

export interface DispatchCompanyCount {
  company: string;
  count: number;
}
