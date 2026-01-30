import { Injectable } from '@nestjs/common';
import { ExcelService } from '../excel/excel.service';
import { VisaAlert } from '../common/interfaces/employee.interface';
import { CONFIG } from '../common/constants';

export interface VisaAlertSummary {
  total: number;
  critical: number;
  warning: number;
  upcoming: number;
  alerts: VisaAlert[];
}

@Injectable()
export class VisasService {
  constructor(private readonly excelService: ExcelService) {}

  /**
   * Get visa alerts
   */
  getVisaAlerts(days: number = 90, activeOnly: boolean = true): VisaAlert[] {
    return this.excelService.getVisaAlerts(days, activeOnly);
  }

  /**
   * Get visa alerts with summary
   */
  getVisaAlertSummary(days: number = 90, activeOnly: boolean = true): VisaAlertSummary {
    const alerts = this.getVisaAlerts(days, activeOnly);

    return {
      total: alerts.length,
      critical: alerts.filter((a) => a.urgencyLevel === 'critical').length,
      warning: alerts.filter((a) => a.urgencyLevel === 'warning').length,
      upcoming: alerts.filter((a) => a.urgencyLevel === 'upcoming').length,
      alerts,
    };
  }

  /**
   * Get alerts by urgency level
   */
  getAlertsByUrgency(
    urgencyLevel: 'critical' | 'warning' | 'upcoming',
    activeOnly: boolean = true,
  ): VisaAlert[] {
    const alerts = this.getVisaAlerts(CONFIG.VISA_THRESHOLDS.UPCOMING, activeOnly);
    return alerts.filter((a) => a.urgencyLevel === urgencyLevel);
  }

  /**
   * Get critical alerts (expiring in 30 days or less)
   */
  getCriticalAlerts(activeOnly: boolean = true): VisaAlert[] {
    return this.getAlertsByUrgency('critical', activeOnly);
  }

  /**
   * Get expired visas
   */
  getExpiredVisas(activeOnly: boolean = true): VisaAlert[] {
    const alerts = this.getVisaAlerts(0, activeOnly);
    return alerts.filter((a) => a.daysUntilExpiry < 0);
  }
}
