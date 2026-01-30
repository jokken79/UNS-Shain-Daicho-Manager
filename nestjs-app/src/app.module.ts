import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { EmployeesModule } from './employees/employees.module';
import { VisasModule } from './visas/visas.module';
import { SalariesModule } from './salaries/salaries.module';
import { ReportsModule } from './reports/reports.module';
import { ExcelModule } from './excel/excel.module';

@Module({
  imports: [
    ExcelModule,
    EmployeesModule,
    VisasModule,
    SalariesModule,
    ReportsModule,
  ],
  controllers: [AppController],
})
export class AppModule {}
