import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';
import { APP_GUARD } from '@nestjs/core';

import { AppController } from './app.controller';
import { DatabaseModule } from './database/database.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { ExcelModule } from './excel/excel.module';
import { EmployeesModule } from './employees/employees.module';
import { VisasModule } from './visas/visas.module';
import { SalariesModule } from './salaries/salaries.module';
import { ReportsModule } from './reports/reports.module';
import { NotificationsModule } from './notifications/notifications.module';
import { JwtAuthGuard } from './auth/guards/jwt-auth.guard';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),

    // Scheduled tasks
    ScheduleModule.forRoot(),

    // Database
    DatabaseModule,

    // Authentication
    AuthModule,
    UsersModule,

    // Core modules
    ExcelModule,
    EmployeesModule,
    VisasModule,
    SalariesModule,
    ReportsModule,

    // Notifications
    NotificationsModule,
  ],
  controllers: [AppController],
  providers: [
    // Global JWT guard (routes are public by default with @Public() decorator)
    {
      provide: APP_GUARD,
      useClass: JwtAuthGuard,
    },
  ],
})
export class AppModule {}
