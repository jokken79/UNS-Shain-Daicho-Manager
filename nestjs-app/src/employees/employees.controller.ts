import {
  Controller,
  Get,
  Param,
  Query,
  ParseIntPipe,
  NotFoundException,
  Render,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiParam } from '@nestjs/swagger';
import { EmployeesService } from './employees.service';

@ApiTags('employees')
@Controller('api/employees')
export class EmployeesController {
  constructor(private readonly employeesService: EmployeesService) {}

  @Get()
  @ApiOperation({ summary: 'Obtener todos los empleados' })
  @ApiQuery({ name: 'active', required: false, type: Boolean, description: 'Filtrar solo activos' })
  @ApiQuery({ name: 'category', required: false, description: 'Filtrar por categoría (派遣社員, 請負社員, スタッフ)' })
  getAllEmployees(
    @Query('active') active?: string,
    @Query('category') category?: string,
  ) {
    if (active === 'true') {
      return this.employeesService.getActiveEmployees(category);
    }
    return this.employeesService.getAllEmployees();
  }

  @Get('search')
  @ApiOperation({ summary: 'Buscar empleados por nombre' })
  @ApiQuery({ name: 'name', required: true, description: 'Nombre a buscar (parcial)' })
  @ApiQuery({ name: 'activeOnly', required: false, type: Boolean, description: 'Solo empleados activos' })
  searchEmployees(
    @Query('name') name: string,
    @Query('activeOnly') activeOnly?: string,
  ) {
    const onlyActive = activeOnly !== 'false';
    return this.employeesService.searchEmployees(name, onlyActive);
  }

  @Get('stats')
  @ApiOperation({ summary: 'Obtener estadísticas generales' })
  async getStats() {
    return this.employeesService.getSummaryStats();
  }

  @Get('stats/nationality')
  @ApiOperation({ summary: 'Obtener distribución por nacionalidad' })
  getNationalityBreakdown() {
    return this.employeesService.getNationalityBreakdown();
  }

  @Get('stats/age')
  @ApiOperation({ summary: 'Obtener distribución por edad' })
  getAgeBreakdown() {
    return this.employeesService.getAgeBreakdown();
  }

  @Get('stats/dispatch-companies')
  @ApiOperation({ summary: 'Obtener top empresas de despacho' })
  @ApiQuery({ name: 'top', required: false, type: Number, description: 'Número de empresas a mostrar' })
  getDispatchCompanyBreakdown(@Query('top') top?: string) {
    const topN = top ? parseInt(top, 10) : undefined;
    return this.employeesService.getDispatchCompanyBreakdown(topN);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Obtener empleado por ID' })
  @ApiParam({ name: 'id', type: Number, description: 'ID del empleado (社員№)' })
  getEmployeeById(@Param('id', ParseIntPipe) id: number) {
    const employee = this.employeesService.getEmployeeById(id);
    if (!employee) {
      throw new NotFoundException(`Empleado con ID ${id} no encontrado`);
    }
    return employee;
  }
}
