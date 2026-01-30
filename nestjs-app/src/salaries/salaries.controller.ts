import { Controller, Get, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery } from '@nestjs/swagger';
import { SalariesService } from './salaries.service';

@ApiTags('salaries')
@Controller('api/salaries')
export class SalariesController {
  constructor(private readonly salariesService: SalariesService) {}

  @Get('stats')
  @ApiOperation({ summary: 'Obtener estadísticas de salarios' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getSalaryStats(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return this.salariesService.getSalaryStats(onlyActive);
  }

  @Get('distribution')
  @ApiOperation({ summary: 'Obtener distribución de salarios (para histograma)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getSalaryDistribution(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return this.salariesService.getSalaryDistribution(onlyActive);
  }

  @Get('profit')
  @ApiOperation({ summary: 'Obtener análisis de ganancias' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getProfitAnalysis(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return this.salariesService.getProfitAnalysis(onlyActive);
  }

  @Get('top-earners')
  @ApiOperation({ summary: 'Obtener empleados con mayor salario' })
  @ApiQuery({ name: 'top', required: false, type: Number, description: 'Número de empleados (default: 10)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getTopEarners(
    @Query('top') top?: string,
    @Query('activeOnly') activeOnly?: string,
  ) {
    const topN = top ? parseInt(top, 10) : 10;
    const onlyActive = activeOnly !== 'false';
    return this.salariesService.getTopEarners(topN, onlyActive);
  }

  @Get('by-category')
  @ApiOperation({ summary: 'Obtener comparación de salarios por categoría' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getSalaryByCategory(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return this.salariesService.getSalaryByCategory(onlyActive);
  }
}
