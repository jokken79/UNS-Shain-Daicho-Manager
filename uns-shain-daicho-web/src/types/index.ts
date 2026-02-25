export interface Employee {
  id: string;
  no: number;
  name: string;
  kana: string;
  category: '派遣' | '請負' | 'Staff' | '退社';
  status: '在職中' | '退社' | string;
  
  // Company/assignment
  companyId?: number;
  company?: string;
  assignment?: string;
  assignmentLine?: string;
  workDescription?: string;
  office?: string;
  
  // Personal info
  gender?: string;
  nationality?: string;
  birthDate?: string;
  age?: number;
  
  // Salary
  hourlyWage?: number;
  hourlyWageRevision?: string;
  billingRate?: number;
  billingRevision?: string;
  profit?: number;
  standardReward?: number;
  
  // Social insurance
  healthInsurance?: string;
  careInsurance?: string;
  welfarePension?: string;
  socialInsurance?: string;
  employmentInsurance?: string;
  
  // Visa
  visaExpiry?: string;
  visaAlert?: string;
  visaType?: string;
  
  // Contact
  postalCode?: string;
  address?: string;
  building?: string;
  phone?: string;
  phoneAlt?: string;
  
  // Bank
  bankAccountName?: string;
  bankName?: string;
  bankBranchNumber?: string;
  bankBranchName?: string;
  bankAccountNumber?: string;
  
  // Dates
  hireDate?: string;
  retireDate?: string;
  moveOutDate?: string;
  moveInDate?: string;
  
  // Other
  commuteMethod?: string;
  commuteDistance?: number;
  commuteAllowance?: number;
  licenseType?: string;
  licenseExpiry?: string;
  insuranceExpiry?: string;
  japaneseLevel?: string;
  carrier5Years?: string;
  notes?: string;
  hireRequest?: string;
}

export interface EmployeeStats {
  total: number;
  active: number;
  retired: number;
  byCategory: Record<string, number>;
  byNationality: Record<string, number>;
  ageGroups: Record<string, number>;
  byCompany: Record<string, number>;
}

export interface VisaAlert {
  employee: Employee;
  daysUntilExpiry: number;
  alertLevel: 'expired' | 'urgent' | 'warning' | 'upcoming';
}

export interface SalaryStats {
  hourlyWage: { min: number; max: number; avg: number; median: number; count: number };
  billingRate: { min: number; max: number; avg: number; median: number; count: number };
  profit: { min: number; max: number; avg: number; median: number; count: number };
}
