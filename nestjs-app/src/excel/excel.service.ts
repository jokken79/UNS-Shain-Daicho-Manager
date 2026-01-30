import { Injectable, Logger } from '@nestjs/common';
import * as ExcelJS from 'exceljs';
import * as path from 'path';
import * as fs from 'fs';
import {
  Employee,
  EmployeeCategory,
  EmployeeStats,
  CategoryCount,
  NationalityCount,
  SalaryStats,
  NumericStats,
  VisaAlert,
  AgeGroup,
  DispatchCompanyCount,
} from '../common/interfaces/employee.interface';
import { COLUMN_MAPPINGS, SHEET_NAMES, STATUS, CONFIG } from '../common/constants';

@Injectable()
export class ExcelService {
  private readonly logger = new Logger(ExcelService.name);
  private employees: Employee[] = [];
  private isLoaded = false;
  private loadedFilePath: string | null = null;

  /**
   * Load employees from an Excel file
   */
  async loadFromFile(filePath: string): Promise<boolean> {
    try {
      this.logger.log(`Loading Excel file: ${filePath}`);

      if (!fs.existsSync(filePath)) {
        this.logger.error(`File not found: ${filePath}`);
        return false;
      }

      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.readFile(filePath);

      this.employees = [];

      // Load each sheet
      await this.loadSheet(workbook, SHEET_NAMES.DISPATCH, EmployeeCategory.DISPATCH);
      await this.loadSheet(workbook, SHEET_NAMES.CONTRACT, EmployeeCategory.CONTRACT);
      await this.loadSheet(workbook, SHEET_NAMES.STAFF, EmployeeCategory.STAFF);

      this.isLoaded = true;
      this.loadedFilePath = filePath;
      this.logger.log(`Loaded ${this.employees.length} employees successfully`);

      return true;
    } catch (error) {
      this.logger.error(`Error loading Excel file: ${error}`);
      return false;
    }
  }

  /**
   * Load employees from uploaded buffer
   */
  async loadFromBuffer(buffer: Buffer): Promise<boolean> {
    try {
      this.logger.log('Loading Excel from buffer');

      const workbook = new ExcelJS.Workbook();
      await workbook.xlsx.load(buffer as unknown as ExcelJS.Buffer);

      this.employees = [];

      await this.loadSheet(workbook, SHEET_NAMES.DISPATCH, EmployeeCategory.DISPATCH);
      await this.loadSheet(workbook, SHEET_NAMES.CONTRACT, EmployeeCategory.CONTRACT);
      await this.loadSheet(workbook, SHEET_NAMES.STAFF, EmployeeCategory.STAFF);

      this.isLoaded = true;
      this.loadedFilePath = 'uploaded';
      this.logger.log(`Loaded ${this.employees.length} employees from buffer`);

      return true;
    } catch (error) {
      this.logger.error(`Error loading Excel from buffer: ${error}`);
      return false;
    }
  }

  private async loadSheet(
    workbook: ExcelJS.Workbook,
    sheetName: string,
    category: EmployeeCategory,
  ): Promise<void> {
    const worksheet = workbook.getWorksheet(sheetName);
    if (!worksheet) {
      this.logger.warn(`Sheet not found: ${sheetName}`);
      return;
    }

    const headers: Map<string, number> = new Map();
    const headerRow = worksheet.getRow(1);

    // Map column headers
    headerRow.eachCell((cell, colNumber) => {
      const value = cell.value?.toString() || '';
      if (COLUMN_MAPPINGS[value as keyof typeof COLUMN_MAPPINGS]) {
        headers.set(COLUMN_MAPPINGS[value as keyof typeof COLUMN_MAPPINGS], colNumber);
      }
    });

    // Process data rows
    worksheet.eachRow((row, rowNumber) => {
      if (rowNumber === 1) return; // Skip header

      const employee = this.parseRow(row, headers, category);
      if (employee && employee.employeeId) {
        this.employees.push(employee);
      }
    });

    this.logger.log(`Loaded ${worksheet.rowCount - 1} rows from ${sheetName}`);
  }

  private parseRow(
    row: ExcelJS.Row,
    headers: Map<string, number>,
    category: EmployeeCategory,
  ): Employee | null {
    try {
      const getValue = (field: string): any => {
        const colNum = headers.get(field);
        if (!colNum) return null;
        const cell = row.getCell(colNum);
        return cell.value;
      };

      const parseDate = (value: any): Date | null => {
        if (!value) return null;
        if (value instanceof Date) return value;
        const date = new Date(value);
        return isNaN(date.getTime()) ? null : date;
      };

      const parseNumber = (value: any): number | null => {
        if (value === null || value === undefined || value === '') return null;
        const num = Number(value);
        return isNaN(num) ? null : num;
      };

      return {
        employeeId: parseNumber(getValue('employeeId')) || 0,
        name: getValue('name')?.toString() || '',
        nameKana: getValue('nameKana')?.toString() || '',
        currentStatus: getValue('currentStatus')?.toString() || '',
        nationality: getValue('nationality')?.toString() || '',
        hireDate: parseDate(getValue('hireDate')),
        resignationDate: parseDate(getValue('resignationDate')),
        visaExpiry: parseDate(getValue('visaExpiry')),
        visaType: getValue('visaType')?.toString() || '',
        hourlyRate: parseNumber(getValue('hourlyRate')),
        billingRate: parseNumber(getValue('billingRate')),
        profitMargin: parseNumber(getValue('profitMargin')),
        dispatchCompany: getValue('dispatchCompany')?.toString() || '',
        age: parseNumber(getValue('age')),
        category,
      };
    } catch (error) {
      this.logger.error(`Error parsing row: ${error}`);
      return null;
    }
  }

  /**
   * Check if data is loaded
   */
  isDataLoaded(): boolean {
    return this.isLoaded;
  }

  /**
   * Get all employees
   */
  getAllEmployees(): Employee[] {
    return this.employees;
  }

  /**
   * Get active employees
   */
  getActiveEmployees(category?: EmployeeCategory): Employee[] {
    let filtered = this.employees.filter((e) => e.currentStatus === STATUS.ACTIVE);
    if (category) {
      filtered = filtered.filter((e) => e.category === category);
    }
    return filtered;
  }

  /**
   * Search employees by name
   */
  searchEmployee(name: string, activeOnly: boolean = true): Employee[] {
    const searchTerm = name.toLowerCase();
    let results = this.employees.filter(
      (e) =>
        e.name.toLowerCase().includes(searchTerm) ||
        e.nameKana.toLowerCase().includes(searchTerm),
    );

    if (activeOnly) {
      results = results.filter((e) => e.currentStatus === STATUS.ACTIVE);
    }

    return results;
  }

  /**
   * Get employee by ID
   */
  getEmployeeById(employeeId: number): Employee | undefined {
    return this.employees.find((e) => e.employeeId === employeeId);
  }

  /**
   * Get summary statistics
   */
  async getSummaryStats(): Promise<EmployeeStats> {
    const total = this.employees.length;
    const active = this.employees.filter((e) => e.currentStatus === STATUS.ACTIVE).length;

    const byCategory: CategoryCount[] = [
      EmployeeCategory.DISPATCH,
      EmployeeCategory.CONTRACT,
      EmployeeCategory.STAFF,
    ].map((cat) => {
      const catEmployees = this.employees.filter((e) => e.category === cat);
      return {
        category: cat,
        total: catEmployees.length,
        active: catEmployees.filter((e) => e.currentStatus === STATUS.ACTIVE).length,
      };
    });

    const nationalityCounts = new Map<string, number>();
    this.employees.forEach((e) => {
      if (e.nationality) {
        nationalityCounts.set(
          e.nationality,
          (nationalityCounts.get(e.nationality) || 0) + 1,
        );
      }
    });

    const byNationality: NationalityCount[] = Array.from(nationalityCounts.entries())
      .map(([nationality, count]) => ({
        nationality,
        count,
        percentage: total > 0 ? Math.round((count / total) * 100) : 0,
      }))
      .sort((a, b) => b.count - a.count);

    return {
      total,
      active,
      inactive: total - active,
      byCategory,
      byNationality,
    };
  }

  /**
   * Get salary statistics
   */
  getSalaryStats(activeOnly: boolean = true): SalaryStats {
    let employees = activeOnly ? this.getActiveEmployees() : this.employees;

    const calculateStats = (values: number[]): NumericStats => {
      if (values.length === 0) {
        return { min: 0, max: 0, average: 0, median: 0, count: 0 };
      }

      const sorted = [...values].sort((a, b) => a - b);
      const sum = values.reduce((a, b) => a + b, 0);

      return {
        min: sorted[0],
        max: sorted[sorted.length - 1],
        average: Math.round(sum / values.length),
        median: sorted[Math.floor(sorted.length / 2)],
        count: values.length,
      };
    };

    const hourlyRates = employees
      .filter((e) => e.hourlyRate !== null)
      .map((e) => e.hourlyRate as number);

    const billingRates = employees
      .filter((e) => e.billingRate !== null)
      .map((e) => e.billingRate as number);

    const profitMargins = employees
      .filter((e) => e.profitMargin !== null)
      .map((e) => e.profitMargin as number);

    return {
      hourlyRate: calculateStats(hourlyRates),
      billingRate: calculateStats(billingRates),
      profitMargin: calculateStats(profitMargins),
    };
  }

  /**
   * Get visa alerts
   */
  getVisaAlerts(days: number = 90, activeOnly: boolean = true): VisaAlert[] {
    const now = new Date();
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + days);

    let employees = activeOnly ? this.getActiveEmployees() : this.employees;

    const alerts: VisaAlert[] = [];

    for (const employee of employees) {
      if (!employee.visaExpiry) continue;

      const expiry = new Date(employee.visaExpiry);
      if (expiry <= futureDate) {
        const daysUntil = Math.ceil(
          (expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
        );

        let urgencyLevel: 'critical' | 'warning' | 'upcoming';
        if (daysUntil <= CONFIG.VISA_THRESHOLDS.CRITICAL) {
          urgencyLevel = 'critical';
        } else if (daysUntil <= CONFIG.VISA_THRESHOLDS.WARNING) {
          urgencyLevel = 'warning';
        } else {
          urgencyLevel = 'upcoming';
        }

        alerts.push({
          employee,
          daysUntilExpiry: daysUntil,
          urgencyLevel,
          expiryDate: expiry,
        });
      }
    }

    return alerts.sort((a, b) => a.daysUntilExpiry - b.daysUntilExpiry);
  }

  /**
   * Get nationality breakdown
   */
  getNationalityBreakdown(): NationalityCount[] {
    const counts = new Map<string, number>();
    const total = this.employees.length;

    this.employees.forEach((e) => {
      if (e.nationality) {
        counts.set(e.nationality, (counts.get(e.nationality) || 0) + 1);
      }
    });

    return Array.from(counts.entries())
      .map(([nationality, count]) => ({
        nationality,
        count,
        percentage: total > 0 ? Math.round((count / total) * 100) : 0,
      }))
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Get age breakdown
   */
  getAgeBreakdown(): AgeGroup[] {
    const activeEmployees = this.getActiveEmployees();

    return CONFIG.AGE_GROUPS.map((group) => ({
      ...group,
      count: activeEmployees.filter(
        (e) => e.age !== null && e.age >= group.min && e.age <= group.max,
      ).length,
    }));
  }

  /**
   * Get dispatch company breakdown
   */
  getDispatchCompanyBreakdown(topN: number = CONFIG.DEFAULT_TOP_N): DispatchCompanyCount[] {
    const counts = new Map<string, number>();

    this.getActiveEmployees(EmployeeCategory.DISPATCH).forEach((e) => {
      if (e.dispatchCompany) {
        counts.set(e.dispatchCompany, (counts.get(e.dispatchCompany) || 0) + 1);
      }
    });

    return Array.from(counts.entries())
      .map(([company, count]) => ({ company, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, topN);
  }

  /**
   * Export employees to JSON
   */
  exportToJson(activeOnly: boolean = true): string {
    const employees = activeOnly ? this.getActiveEmployees() : this.employees;
    return JSON.stringify(employees, null, 2);
  }

  /**
   * Export employees to CSV
   */
  exportToCsv(activeOnly: boolean = true): string {
    const employees = activeOnly ? this.getActiveEmployees() : this.employees;

    const headers = [
      'Employee ID',
      'Name',
      'Name (Kana)',
      'Status',
      'Nationality',
      'Hire Date',
      'Visa Expiry',
      'Hourly Rate',
      'Billing Rate',
      'Profit Margin',
      'Dispatch Company',
      'Age',
      'Category',
    ];

    const rows = employees.map((e) => [
      e.employeeId,
      e.name,
      e.nameKana,
      e.currentStatus,
      e.nationality,
      e.hireDate?.toISOString().split('T')[0] || '',
      e.visaExpiry?.toISOString().split('T')[0] || '',
      e.hourlyRate || '',
      e.billingRate || '',
      e.profitMargin || '',
      e.dispatchCompany,
      e.age || '',
      e.category,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) =>
        row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','),
      ),
    ].join('\n');

    return '\uFEFF' + csvContent; // BOM for UTF-8
  }
}
