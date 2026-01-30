import { Injectable } from '@nestjs/common';
import * as ExcelJS from 'exceljs';
import { ExcelService } from '../excel/excel.service';
import { EmployeeCategory } from '../common/interfaces/employee.interface';

@Injectable()
export class ReportsService {
  constructor(private readonly excelService: ExcelService) {}

  /**
   * Export to JSON
   */
  exportToJson(activeOnly: boolean = true): string {
    return this.excelService.exportToJson(activeOnly);
  }

  /**
   * Export to CSV
   */
  exportToCsv(activeOnly: boolean = true): string {
    return this.excelService.exportToCsv(activeOnly);
  }

  /**
   * Export to Excel
   */
  async exportToExcel(activeOnly: boolean = true): Promise<Buffer> {
    const employees = activeOnly
      ? this.excelService.getActiveEmployees()
      : this.excelService.getAllEmployees();

    const workbook = new ExcelJS.Workbook();
    workbook.creator = 'UNS Shain Daicho Manager';
    workbook.created = new Date();

    const worksheet = workbook.addWorksheet('Employees');

    // Define columns
    worksheet.columns = [
      { header: 'Employee ID', key: 'employeeId', width: 12 },
      { header: 'Name', key: 'name', width: 25 },
      { header: 'Name (Kana)', key: 'nameKana', width: 25 },
      { header: 'Status', key: 'currentStatus', width: 12 },
      { header: 'Nationality', key: 'nationality', width: 15 },
      { header: 'Hire Date', key: 'hireDate', width: 12 },
      { header: 'Visa Expiry', key: 'visaExpiry', width: 12 },
      { header: 'Hourly Rate', key: 'hourlyRate', width: 12 },
      { header: 'Billing Rate', key: 'billingRate', width: 12 },
      { header: 'Profit Margin', key: 'profitMargin', width: 12 },
      { header: 'Dispatch Company', key: 'dispatchCompany', width: 25 },
      { header: 'Age', key: 'age', width: 8 },
      { header: 'Category', key: 'category', width: 15 },
    ];

    // Style header row
    worksheet.getRow(1).font = { bold: true };
    worksheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF4472C4' },
    };
    worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };

    // Add data
    employees.forEach((emp) => {
      worksheet.addRow({
        employeeId: emp.employeeId,
        name: emp.name,
        nameKana: emp.nameKana,
        currentStatus: emp.currentStatus,
        nationality: emp.nationality,
        hireDate: emp.hireDate ? emp.hireDate.toISOString().split('T')[0] : '',
        visaExpiry: emp.visaExpiry ? emp.visaExpiry.toISOString().split('T')[0] : '',
        hourlyRate: emp.hourlyRate,
        billingRate: emp.billingRate,
        profitMargin: emp.profitMargin,
        dispatchCompany: emp.dispatchCompany,
        age: emp.age,
        category: emp.category,
      });
    });

    // Format currency columns
    ['hourlyRate', 'billingRate', 'profitMargin'].forEach((col) => {
      worksheet.getColumn(col).numFmt = '¥#,##0';
    });

    const buffer = await workbook.xlsx.writeBuffer();
    return buffer as Buffer;
  }

  /**
   * Generate summary report
   */
  async generateSummaryReport() {
    const stats = await this.excelService.getSummaryStats();
    const salaryStats = this.excelService.getSalaryStats(true);
    const visaAlerts = this.excelService.getVisaAlerts(90, true);
    const ageBreakdown = this.excelService.getAgeBreakdown();
    const dispatchCompanies = this.excelService.getDispatchCompanyBreakdown(10);

    return {
      generatedAt: new Date().toISOString(),
      employeeStats: stats,
      salaryStats,
      visaAlerts: {
        total: visaAlerts.length,
        critical: visaAlerts.filter((a) => a.urgencyLevel === 'critical').length,
        warning: visaAlerts.filter((a) => a.urgencyLevel === 'warning').length,
        upcoming: visaAlerts.filter((a) => a.urgencyLevel === 'upcoming').length,
      },
      ageBreakdown,
      topDispatchCompanies: dispatchCompanies,
    };
  }

  /**
   * Get tenure analysis
   */
  getTenureAnalysis() {
    const employees = this.excelService.getActiveEmployees();
    const now = new Date();

    const tenureRanges = [
      { min: 0, max: 1, label: 'Less than 1 year' },
      { min: 1, max: 2, label: '1-2 years' },
      { min: 2, max: 3, label: '2-3 years' },
      { min: 3, max: 5, label: '3-5 years' },
      { min: 5, max: 10, label: '5-10 years' },
      { min: 10, max: 999, label: '10+ years' },
    ];

    return tenureRanges.map((range) => {
      const count = employees.filter((e) => {
        if (!e.hireDate) return false;
        const years = (now.getTime() - new Date(e.hireDate).getTime()) / (1000 * 60 * 60 * 24 * 365);
        return years >= range.min && years < range.max;
      }).length;

      return {
        ...range,
        count,
        percentage: employees.length > 0 ? Math.round((count / employees.length) * 100) : 0,
      };
    });
  }
}
