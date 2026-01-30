import { Controller, Get, Query, Res, Header } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiProduces } from '@nestjs/swagger';
import { Response } from 'express';
import { ReportsService } from './reports.service';

@ApiTags('reports')
@Controller('api/reports')
export class ReportsController {
  constructor(private readonly reportsService: ReportsService) {}

  @Get('summary')
  @ApiOperation({ summary: 'Generar reporte resumen completo' })
  async getSummaryReport() {
    return this.reportsService.generateSummaryReport();
  }

  @Get('tenure')
  @ApiOperation({ summary: 'Obtener análisis de antigüedad' })
  getTenureAnalysis() {
    return this.reportsService.getTenureAnalysis();
  }

  @Get('export/json')
  @ApiOperation({ summary: 'Exportar empleados a JSON' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  @Header('Content-Type', 'application/json')
  exportToJson(@Query('activeOnly') activeOnly?: string, @Res() res?: Response) {
    const onlyActive = activeOnly !== 'false';
    const json = this.reportsService.exportToJson(onlyActive);

    if (res) {
      res.setHeader('Content-Disposition', 'attachment; filename=employees.json');
      res.send(json);
    }
    return json;
  }

  @Get('export/csv')
  @ApiOperation({ summary: 'Exportar empleados a CSV' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  @ApiProduces('text/csv')
  exportToCsv(@Query('activeOnly') activeOnly?: string, @Res() res?: Response) {
    const onlyActive = activeOnly !== 'false';
    const csv = this.reportsService.exportToCsv(onlyActive);

    if (res) {
      res.setHeader('Content-Type', 'text/csv; charset=utf-8');
      res.setHeader('Content-Disposition', 'attachment; filename=employees.csv');
      res.send(csv);
    }
    return csv;
  }

  @Get('export/excel')
  @ApiOperation({ summary: 'Exportar empleados a Excel' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  @ApiProduces('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
  async exportToExcel(@Query('activeOnly') activeOnly?: string, @Res() res?: Response) {
    const onlyActive = activeOnly !== 'false';
    const buffer = await this.reportsService.exportToExcel(onlyActive);

    if (res) {
      res.setHeader(
        'Content-Type',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      );
      res.setHeader('Content-Disposition', 'attachment; filename=employees.xlsx');
      res.send(buffer);
    }
  }
}
