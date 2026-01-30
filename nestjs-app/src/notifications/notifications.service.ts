import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import * as nodemailer from 'nodemailer';
import { ConfigService } from '@nestjs/config';
import { VisasService } from '../visas/visas.service';
import { VisaAlert } from '../common/interfaces/employee.interface';

@Injectable()
export class NotificationsService {
  private readonly logger = new Logger(NotificationsService.name);
  private transporter: nodemailer.Transporter | null = null;

  constructor(
    private configService: ConfigService,
    private visasService: VisasService,
  ) {
    this.initializeTransporter();
  }

  private initializeTransporter() {
    const host = this.configService.get('SMTP_HOST');
    const port = this.configService.get('SMTP_PORT');
    const user = this.configService.get('SMTP_USER');
    const pass = this.configService.get('SMTP_PASS');

    if (host && user && pass) {
      this.transporter = nodemailer.createTransport({
        host,
        port: port || 587,
        secure: port === 465,
        auth: { user, pass },
      });
      this.logger.log('📧 Email transporter initialized');
    } else {
      this.logger.warn('📧 Email not configured - notifications disabled');
    }
  }

  async sendEmail(
    to: string,
    subject: string,
    html: string,
  ): Promise<boolean> {
    if (!this.transporter) {
      this.logger.warn('Email not sent - transporter not configured');
      return false;
    }

    try {
      const info = await this.transporter.sendMail({
        from: this.configService.get('SMTP_FROM', 'UNS System <noreply@uns.co.jp>'),
        to,
        subject,
        html,
      });
      this.logger.log(`📧 Email sent: ${info.messageId}`);
      return true;
    } catch (error) {
      this.logger.error(`📧 Email failed: ${error.message}`);
      return false;
    }
  }

  // Run every day at 9:00 AM
  @Cron(CronExpression.EVERY_DAY_AT_9AM)
  async sendDailyVisaAlerts() {
    this.logger.log('🔔 Running daily visa alert check...');

    const alerts = this.visasService.getCriticalAlerts(true);
    if (alerts.length === 0) {
      this.logger.log('✅ No critical visa alerts');
      return;
    }

    const adminEmail = this.configService.get('ADMIN_EMAIL');
    if (!adminEmail) {
      this.logger.warn('ADMIN_EMAIL not configured');
      return;
    }

    const html = this.generateVisaAlertEmail(alerts);
    await this.sendEmail(
      adminEmail,
      `⚠️ ALERTA: ${alerts.length} visa(s) próximas a expirar`,
      html,
    );
  }

  // Run every Monday at 8:00 AM
  @Cron('0 8 * * 1')
  async sendWeeklyReport() {
    this.logger.log('📊 Generating weekly visa report...');

    const summary = this.visasService.getVisaAlertSummary(90, true);
    const adminEmail = this.configService.get('ADMIN_EMAIL');

    if (!adminEmail) {
      this.logger.warn('ADMIN_EMAIL not configured');
      return;
    }

    const html = this.generateWeeklyReportEmail(summary);
    await this.sendEmail(
      adminEmail,
      `📊 Reporte Semanal de Visas - ${new Date().toLocaleDateString('es-ES')}`,
      html,
    );
  }

  private generateVisaAlertEmail(alerts: VisaAlert[]): string {
    const rows = alerts
      .map(
        (a) => `
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 10px;">${a.employee.name}</td>
        <td style="padding: 10px;">${a.employee.employeeId}</td>
        <td style="padding: 10px;">${a.employee.nationality || '-'}</td>
        <td style="padding: 10px; color: ${a.daysUntilExpiry <= 7 ? 'red' : 'orange'}; font-weight: bold;">
          ${a.daysUntilExpiry} días
        </td>
        <td style="padding: 10px;">${new Date(a.expiryDate).toLocaleDateString('es-ES')}</td>
      </tr>
    `,
      )
      .join('');

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; }
          .header { background: #d9534f; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th { background: #f5f5f5; padding: 12px; text-align: left; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>⚠️ Alerta de Visas - UNS</h1>
          <p>${alerts.length} empleado(s) con visa próxima a expirar</p>
        </div>
        <div class="content">
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>ID</th>
                <th>Nacionalidad</th>
                <th>Días Restantes</th>
                <th>Fecha Expiración</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
          <p style="margin-top: 20px; color: #666;">
            Este es un mensaje automático del sistema UNS Shain Daicho Manager.
          </p>
        </div>
      </body>
      </html>
    `;
  }

  private generateWeeklyReportEmail(summary: any): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; }
          .header { background: #4472C4; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; }
          .stat-box { display: inline-block; padding: 15px; margin: 10px; border-radius: 8px; text-align: center; min-width: 120px; }
          .critical { background: #ffebee; color: #c62828; }
          .warning { background: #fff3e0; color: #ef6c00; }
          .upcoming { background: #fffde7; color: #f9a825; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>📊 Reporte Semanal de Visas</h1>
          <p>UNS Shain Daicho Manager</p>
        </div>
        <div class="content">
          <h2>Resumen de Alertas (próximos 90 días)</h2>

          <div style="text-align: center; margin: 20px 0;">
            <div class="stat-box critical">
              <h3>🔴 Crítico</h3>
              <p style="font-size: 24px; font-weight: bold;">${summary.critical || 0}</p>
              <small>≤30 días</small>
            </div>
            <div class="stat-box warning">
              <h3>🟠 Advertencia</h3>
              <p style="font-size: 24px; font-weight: bold;">${summary.warning || 0}</p>
              <small>31-60 días</small>
            </div>
            <div class="stat-box upcoming">
              <h3>🟡 Próximo</h3>
              <p style="font-size: 24px; font-weight: bold;">${summary.upcoming || 0}</p>
              <small>61-90 días</small>
            </div>
          </div>

          <p><strong>Total de alertas:</strong> ${summary.total || 0}</p>
          <p><strong>Fecha del reporte:</strong> ${new Date().toLocaleString('es-ES')}</p>

          <p style="margin-top: 20px; color: #666;">
            Este es un mensaje automático del sistema UNS Shain Daicho Manager.
          </p>
        </div>
      </body>
      </html>
    `;
  }

  // Manual trigger for testing
  async sendTestEmail(to: string): Promise<boolean> {
    return this.sendEmail(
      to,
      '🧪 Test - UNS Shain Daicho Manager',
      '<h1>Test Email</h1><p>El sistema de notificaciones está funcionando correctamente.</p>',
    );
  }
}
