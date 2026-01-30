import { Controller, Get, Render } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiExcludeEndpoint } from '@nestjs/swagger';
import { ExcelService } from './excel/excel.service';
import { Public } from './auth/decorators/public.decorator';

@Controller()
export class AppController {
  constructor(private readonly excelService: ExcelService) {}

  @Get()
  @Public()
  @Render('index')
  @ApiExcludeEndpoint()
  async getIndex() {
    const stats = await this.excelService.getSummaryStats();
    return {
      title: 'UNS Shain Daicho Manager',
      stats,
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('login')
  @Public()
  @Render('login')
  @ApiExcludeEndpoint()
  getLogin() {
    return {
      title: 'Iniciar Sesión',
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('search')
  @Public()
  @Render('search')
  @ApiExcludeEndpoint()
  getSearch() {
    return {
      title: 'Búsqueda de Empleados',
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('visas')
  @Public()
  @Render('visas')
  @ApiExcludeEndpoint()
  getVisas() {
    return {
      title: 'Alertas de Visa',
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('salaries')
  @Public()
  @Render('salaries')
  @ApiExcludeEndpoint()
  getSalaries() {
    return {
      title: 'Análisis de Salarios',
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('reports')
  @Public()
  @Render('reports')
  @ApiExcludeEndpoint()
  getReports() {
    return {
      title: 'Reportes y Exportación',
      currentYear: new Date().getFullYear(),
    };
  }

  @Get('api/health')
  @Public()
  @ApiTags('system')
  @ApiOperation({ summary: 'Health check' })
  getHealth() {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '2.0.0',
      service: 'UNS Shain Daicho Manager API',
    };
  }
}
