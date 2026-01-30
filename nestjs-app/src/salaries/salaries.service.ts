import { Injectable } from '@nestjs/common';
import { ExcelService } from '../excel/excel.service';
import { SalaryStats, EmployeeCategory } from '../common/interfaces/employee.interface';
import { CONFIG } from '../common/constants';

export interface SalaryDistribution {
  range: string;
  count: number;
  percentage: number;
}

export interface ProfitAnalysis {
  totalProfit: number;
  averageProfit: number;
  profitByCategory: { category: string; totalProfit: number; avgProfit: number; count: number }[];
}

@Injectable()
export class SalariesService {
  constructor(private readonly excelService: ExcelService) {}

  /**
   * Get salary statistics
   */
  getSalaryStats(activeOnly: boolean = true): SalaryStats {
    return this.excelService.getSalaryStats(activeOnly);
  }

  /**
   * Get salary distribution (histogram data)
   */
  getSalaryDistribution(activeOnly: boolean = true): SalaryDistribution[] {
    const employees = activeOnly
      ? this.excelService.getActiveEmployees()
      : this.excelService.getAllEmployees();

    const hourlyRates = employees
      .filter((e) => e.hourlyRate !== null)
      .map((e) => e.hourlyRate as number);

    if (hourlyRates.length === 0) return [];

    // Create distribution buckets
    const min = Math.floor(Math.min(...hourlyRates) / 100) * 100;
    const max = Math.ceil(Math.max(...hourlyRates) / 100) * 100;
    const bucketSize = 100;

    const distribution: SalaryDistribution[] = [];
    for (let i = min; i < max; i += bucketSize) {
      const count = hourlyRates.filter((r) => r >= i && r < i + bucketSize).length;
      distribution.push({
        range: `¥${i.toLocaleString()}-${(i + bucketSize).toLocaleString()}`,
        count,
        percentage: Math.round((count / hourlyRates.length) * 100),
      });
    }

    return distribution;
  }

  /**
   * Get profit analysis
   */
  getProfitAnalysis(activeOnly: boolean = true): ProfitAnalysis {
    const employees = activeOnly
      ? this.excelService.getActiveEmployees()
      : this.excelService.getAllEmployees();

    const withProfit = employees.filter((e) => e.profitMargin !== null);
    const totalProfit = withProfit.reduce((sum, e) => sum + (e.profitMargin || 0), 0);

    const categories = [EmployeeCategory.DISPATCH, EmployeeCategory.CONTRACT, EmployeeCategory.STAFF];
    const profitByCategory = categories.map((category) => {
      const catEmployees = withProfit.filter((e) => e.category === category);
      const catTotal = catEmployees.reduce((sum, e) => sum + (e.profitMargin || 0), 0);
      return {
        category,
        totalProfit: catTotal,
        avgProfit: catEmployees.length > 0 ? Math.round(catTotal / catEmployees.length) : 0,
        count: catEmployees.length,
      };
    });

    return {
      totalProfit,
      averageProfit: withProfit.length > 0 ? Math.round(totalProfit / withProfit.length) : 0,
      profitByCategory,
    };
  }

  /**
   * Get top earners
   */
  getTopEarners(topN: number = 10, activeOnly: boolean = true) {
    const employees = activeOnly
      ? this.excelService.getActiveEmployees()
      : this.excelService.getAllEmployees();

    return employees
      .filter((e) => e.hourlyRate !== null)
      .sort((a, b) => (b.hourlyRate || 0) - (a.hourlyRate || 0))
      .slice(0, topN)
      .map((e) => ({
        employeeId: e.employeeId,
        name: e.name,
        hourlyRate: e.hourlyRate,
        billingRate: e.billingRate,
        profitMargin: e.profitMargin,
        category: e.category,
      }));
  }

  /**
   * Get salary comparison by category
   */
  getSalaryByCategory(activeOnly: boolean = true) {
    const categories = [EmployeeCategory.DISPATCH, EmployeeCategory.CONTRACT, EmployeeCategory.STAFF];
    const employees = activeOnly
      ? this.excelService.getActiveEmployees()
      : this.excelService.getAllEmployees();

    return categories.map((category) => {
      const catEmployees = employees.filter(
        (e) => e.category === category && e.hourlyRate !== null,
      );
      const hourlyRates = catEmployees.map((e) => e.hourlyRate as number);

      if (hourlyRates.length === 0) {
        return { category, min: 0, max: 0, average: 0, count: 0 };
      }

      return {
        category,
        min: Math.min(...hourlyRates),
        max: Math.max(...hourlyRates),
        average: Math.round(hourlyRates.reduce((a, b) => a + b, 0) / hourlyRates.length),
        count: hourlyRates.length,
      };
    });
  }
}
