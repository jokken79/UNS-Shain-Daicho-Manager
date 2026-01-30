import { ApiProperty } from '@nestjs/swagger';
import { IsString, MinLength } from 'class-validator';

export class LoginDto {
  @ApiProperty({ description: 'Nombre de usuario', example: 'admin' })
  @IsString()
  @MinLength(3)
  username: string;

  @ApiProperty({ description: 'Contraseña', example: '********' })
  @IsString()
  @MinLength(6)
  password: string;
}

export class AuthResponseDto {
  @ApiProperty({ description: 'Token JWT' })
  access_token: string;

  @ApiProperty({ description: 'Tipo de token' })
  token_type: string;

  @ApiProperty({ description: 'Tiempo de expiración en segundos' })
  expires_in: number;

  @ApiProperty({ description: 'Información del usuario' })
  user: {
    id: number;
    username: string;
    role: string;
  };
}
