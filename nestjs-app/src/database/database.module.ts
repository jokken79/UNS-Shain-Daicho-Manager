import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { User } from './entities/user.entity';
import { Employee } from './entities/employee.entity';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        host: configService.get('DB_HOST', 'localhost'),
        port: configService.get('DB_PORT', 5432),
        username: configService.get('DB_USERNAME', 'uns_admin'),
        password: configService.get('DB_PASSWORD', 'uns_password'),
        database: configService.get('DB_DATABASE', 'uns_shain_daicho'),
        entities: [User, Employee],
        synchronize: configService.get('DB_SYNC', 'true') === 'true', // Only in development
        logging: configService.get('DB_LOGGING', 'false') === 'true',
        autoLoadEntities: true,
      }),
    }),
  ],
  exports: [TypeOrmModule],
})
export class DatabaseModule {}
