import { Controller, Get, Query, Render } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery } from '@nestjs/swagger';
import { VisasService } from './visas.service';

@ApiTags('visas')
@Controller('api/visas')
export class VisasController {
  constructor(private readonly visasService: VisasService) {}

  @Get('alerts')
  @ApiOperation({ summary: 'Obtener alertas de visa' })
  @ApiQuery({ name: 'days', required: false, type: Number, description: 'Días hasta expiración (default: 90)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getVisaAlerts(
    @Query('days') days?: string,
    @Query('activeOnly') activeOnly?: string,
  ) {
    const daysNum = days ? parseInt(days, 10) : 90;
    const onlyActive = activeOnly !== 'false';
    return this.visasService.getVisaAlertSummary(daysNum, onlyActive);
  }

  @Get('alerts/critical')
  @ApiOperation({ summary: 'Obtener alertas críticas (≤30 días)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getCriticalAlerts(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return {
      urgencyLevel: 'critical',
      thresholdDays: 30,
      alerts: this.visasService.getCriticalAlerts(onlyActive),
    };
  }

  @Get('alerts/warning')
  @ApiOperation({ summary: 'Obtener alertas de advertencia (31-60 días)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getWarningAlerts(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return {
      urgencyLevel: 'warning',
      thresholdDays: 60,
      alerts: this.visasService.getAlertsByUrgency('warning', onlyActive),
    };
  }

  @Get('alerts/upcoming')
  @ApiOperation({ summary: 'Obtener alertas próximas (61-90 días)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getUpcomingAlerts(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return {
      urgencyLevel: 'upcoming',
      thresholdDays: 90,
      alerts: this.visasService.getAlertsByUrgency('upcoming', onlyActive),
    };
  }

  @Get('expired')
  @ApiOperation({ summary: 'Obtener visas expiradas' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  getExpiredVisas(@Query('activeOnly') activeOnly?: string) {
    const onlyActive = activeOnly !== 'false';
    return {
      status: 'expired',
      alerts: this.visasService.getExpiredVisas(onlyActive),
    };
  }
}
