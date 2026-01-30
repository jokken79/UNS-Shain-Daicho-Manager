import { Injectable } from '@nestjs/common';
import { ExcelService } from '../excel/excel.service';
import { Employee, EmployeeCategory, EmployeeStats } from '../common/interfaces/employee.interface';

@Injectable()
export class EmployeesService {
  constructor(private readonly excelService: ExcelService) {}

  /**
   * Get all employees
   */
  getAllEmployees(): Employee[] {
    return this.excelService.getAllEmployees();
  }

  /**
   * Get active employees
   */
  getActiveEmployees(category?: string): Employee[] {
    const cat = category as EmployeeCategory | undefined;
    return this.excelService.getActiveEmployees(cat);
  }

  /**
   * Search employees by name
   */
  searchEmployees(name: string, activeOnly: boolean = true): Employee[] {
    return this.excelService.searchEmployee(name, activeOnly);
  }

  /**
   * Get employee by ID
   */
  getEmployeeById(id: number): Employee | undefined {
    return this.excelService.getEmployeeById(id);
  }

  /**
   * Get summary statistics
   */
  async getSummaryStats(): Promise<EmployeeStats> {
    return this.excelService.getSummaryStats();
  }

  /**
   * Get nationality breakdown
   */
  getNationalityBreakdown() {
    return this.excelService.getNationalityBreakdown();
  }

  /**
   * Get age breakdown
   */
  getAgeBreakdown() {
    return this.excelService.getAgeBreakdown();
  }

  /**
   * Get dispatch company breakdown
   */
  getDispatchCompanyBreakdown(topN?: number) {
    return this.excelService.getDispatchCompanyBreakdown(topN);
  }
}
