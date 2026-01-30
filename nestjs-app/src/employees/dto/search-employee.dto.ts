import { IsString, IsOptional, IsBoolean, MinLength } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class SearchEmployeeDto {
  @ApiProperty({ description: 'Nombre a buscar', minLength: 1 })
  @IsString()
  @MinLength(1)
  name: string;

  @ApiPropertyOptional({ description: 'Solo empleados activos', default: true })
  @IsOptional()
  @IsBoolean()
  activeOnly?: boolean = true;
}

export class FilterEmployeeDto {
  @ApiPropertyOptional({ description: 'Filtrar solo empleados activos' })
  @IsOptional()
  @IsBoolean()
  active?: boolean;

  @ApiPropertyOptional({ description: 'Filtrar por categoría (派遣社員, 請負社員, スタッフ)' })
  @IsOptional()
  @IsString()
  category?: string;
}
