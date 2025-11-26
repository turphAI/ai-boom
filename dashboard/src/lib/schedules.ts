/**
 * Scraper schedule configuration
 * 
 * This file defines the schedules for all scrapers.
 * Update this file when changing schedules in serverless.yml to keep them in sync.
 * 
 * Cron format: minute hour day-of-month month day-of-week year
 * AWS uses 6-field cron: (minute hour day-of-month month day-of-week year)
 */

export interface ScraperSchedule {
  name: string;
  displayName: string;
  cronExpression: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  description: string;
  timezone: string;
  nextRunDescription: string;
}

/**
 * Parse a cron expression and return a human-readable description
 */
function describeCron(cron: string): string {
  // AWS cron format: minute hour day-of-month month day-of-week year
  const parts = cron.replace('cron(', '').replace(')', '').split(' ');
  if (parts.length < 5) return 'Unknown schedule';

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
  
  const hourInt = parseInt(hour);
  const hour12 = hourInt > 12 ? hourInt - 12 : hourInt === 0 ? 12 : hourInt;
  const ampm = hourInt >= 12 ? 'PM' : 'AM';
  const timeStr = `${hour12}:${minute.padStart(2, '0')} ${ampm} UTC`;

  // Weekly (Monday)
  if (dayOfWeek === 'MON' && dayOfMonth === '?') {
    return `Every Monday at ${timeStr}`;
  }

  // Daily
  if (dayOfMonth === '*' && dayOfWeek === '?') {
    return `Daily at ${timeStr}`;
  }

  // Monthly (first day)
  if (dayOfMonth === '1' && month === '*' && dayOfWeek === '?') {
    return `1st of each month at ${timeStr}`;
  }

  // Quarterly
  if (dayOfMonth === '1' && (month === '1,4,7,10' || month.includes(','))) {
    const months = month.split(',').map(m => {
      const monthNames = ['Jan', 'Apr', 'Jul', 'Oct'];
      const idx = ['1', '4', '7', '10'].indexOf(m);
      return idx >= 0 ? monthNames[idx] : m;
    });
    return `1st of ${months.join(', ')} at ${timeStr}`;
  }

  return `${cron} (UTC)`;
}

/**
 * Calculate the next run time based on cron expression
 */
function getNextRunDescription(cron: string, frequency: string): string {
  const now = new Date();
  const utcHour = now.getUTCHours();
  const utcDay = now.getUTCDay(); // 0 = Sunday
  const utcDate = now.getUTCDate();
  const utcMonth = now.getUTCMonth() + 1; // 1-indexed

  const parts = cron.replace('cron(', '').replace(')', '').split(' ');
  const [, scheduleHour] = parts;
  const hourInt = parseInt(scheduleHour);

  switch (frequency) {
    case 'daily': {
      if (utcHour < hourInt) {
        return 'Today';
      }
      return 'Tomorrow';
    }
    case 'weekly': {
      // Monday = 1, current day = utcDay (0 = Sunday)
      const daysUntilMonday = utcDay === 0 ? 1 : utcDay === 1 ? (utcHour < hourInt ? 0 : 7) : 8 - utcDay;
      if (daysUntilMonday === 0) return 'Today';
      if (daysUntilMonday === 1) return 'Tomorrow';
      return `In ${daysUntilMonday} days`;
    }
    case 'monthly': {
      if (utcDate === 1 && utcHour < hourInt) {
        return 'Today';
      }
      const nextMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1));
      const daysUntil = Math.ceil((nextMonth.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return `In ${daysUntil} days`;
    }
    case 'quarterly': {
      const quarterMonths = [1, 4, 7, 10];
      const nextQuarterMonth = quarterMonths.find(m => m > utcMonth) || quarterMonths[0];
      const nextYear = nextQuarterMonth <= utcMonth ? now.getUTCFullYear() + 1 : now.getUTCFullYear();
      const nextRun = new Date(Date.UTC(nextYear, nextQuarterMonth - 1, 1));
      const daysUntil = Math.ceil((nextRun.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      if (daysUntil <= 0) return 'Today';
      if (daysUntil === 1) return 'Tomorrow';
      return `In ${daysUntil} days`;
    }
    default:
      return 'Unknown';
  }
}

/**
 * Scraper schedules - these should match serverless.yml
 * 
 * To update: modify both this file AND serverless.yml
 */
export const SCRAPER_SCHEDULES: ScraperSchedule[] = [
  {
    name: 'bond-issuance',
    displayName: 'Bond Issuance',
    cronExpression: 'cron(0 8 ? * MON *)',
    frequency: 'weekly',
    description: 'Monitors weekly investment-grade tech bond issuance from SEC EDGAR',
    timezone: 'UTC',
    get nextRunDescription() {
      return getNextRunDescription(this.cronExpression, this.frequency);
    }
  },
  {
    name: 'bdc-discount',
    displayName: 'BDC Discount',
    cronExpression: 'cron(0 6 * * ? *)',
    frequency: 'daily',
    description: 'Monitors BDC discount-to-NAV ratios from Yahoo Finance and SEC filings',
    timezone: 'UTC',
    get nextRunDescription() {
      return getNextRunDescription(this.cronExpression, this.frequency);
    }
  },
  {
    name: 'credit-fund',
    displayName: 'Credit Fund',
    cronExpression: 'cron(0 7 1 * ? *)',
    frequency: 'monthly',
    description: 'Monitors private credit fund asset marks from Form PF filings',
    timezone: 'UTC',
    get nextRunDescription() {
      return getNextRunDescription(this.cronExpression, this.frequency);
    }
  },
  {
    name: 'bank-provision',
    displayName: 'Bank Provision',
    cronExpression: 'cron(0 9 1 1,4,7,10 ? *)',
    frequency: 'quarterly',
    description: 'Monitors bank provisioning for non-bank financial exposures from XBRL filings',
    timezone: 'UTC',
    get nextRunDescription() {
      return getNextRunDescription(this.cronExpression, this.frequency);
    }
  }
];

/**
 * Get all schedules with computed next run times
 */
export function getSchedules(): Omit<ScraperSchedule, 'nextRunDescription'>[] & { nextRunDescription: string }[] {
  return SCRAPER_SCHEDULES.map(schedule => ({
    name: schedule.name,
    displayName: schedule.displayName,
    cronExpression: schedule.cronExpression,
    frequency: schedule.frequency,
    description: schedule.description,
    timezone: schedule.timezone,
    nextRunDescription: getNextRunDescription(schedule.cronExpression, schedule.frequency),
    humanReadableSchedule: describeCron(schedule.cronExpression)
  }));
}

/**
 * Get a specific schedule by name
 */
export function getScheduleByName(name: string): ScraperSchedule | undefined {
  return SCRAPER_SCHEDULES.find(s => s.name === name);
}

