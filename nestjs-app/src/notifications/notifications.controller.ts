import {
  Controller,
  Post,
  Body,
  UseGuards,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
} from '@nestjs/swagger';
import { NotificationsService } from './notifications.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RolesGuard, Role } from '../auth/guards/roles.guard';
import { Roles } from '../auth/decorators/roles.decorator';

class SendTestEmailDto {
  email: string;
}

class TriggerAlertsDto {
  type: 'daily' | 'weekly';
}

@ApiTags('notifications')
@Controller('api/notifications')
@UseGuards(JwtAuthGuard, RolesGuard)
@ApiBearerAuth()
export class NotificationsController {
  constructor(private notificationsService: NotificationsService) {}

  @Post('test')
  @Roles(Role.ADMIN)
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Enviar email de prueba (solo admin)' })
  @ApiResponse({ status: 200, description: 'Email enviado' })
  @ApiResponse({ status: 401, description: 'No autorizado' })
  @ApiResponse({ status: 403, description: 'Acceso denegado' })
  async sendTestEmail(@Body() dto: SendTestEmailDto) {
    const success = await this.notificationsService.sendTestEmail(dto.email);
    return {
      success,
      message: success
        ? 'Email de prueba enviado correctamente'
        : 'Error al enviar email - verifica la configuración SMTP',
    };
  }

  @Post('trigger')
  @Roles(Role.ADMIN)
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Disparar alertas manualmente (solo admin)' })
  @ApiResponse({ status: 200, description: 'Alertas enviadas' })
  async triggerAlerts(@Body() dto: TriggerAlertsDto) {
    if (dto.type === 'daily') {
      await this.notificationsService.sendDailyVisaAlerts();
      return { message: 'Alertas diarias enviadas' };
    } else if (dto.type === 'weekly') {
      await this.notificationsService.sendWeeklyReport();
      return { message: 'Reporte semanal enviado' };
    }
    return { message: 'Tipo de alerta no válido' };
  }
}
