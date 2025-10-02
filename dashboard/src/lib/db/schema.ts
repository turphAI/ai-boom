import { mysqlTable, varchar, text, timestamp, decimal, boolean, json, int, datetime, mysqlEnum } from 'drizzle-orm/mysql-core';

export const users = mysqlTable('users', {
  id: int('id').primaryKey().autoincrement(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: varchar('password_hash', { length: 255 }).notNull(),
  name: varchar('name', { length: 50 }).notNull(),
  role: mysqlEnum('role', ['user', 'admin', 'editor', 'moderator']).default('user'),
  preferences: json('preferences'),
  notifications: json('notifications'),
  profile: json('profile'),
  resetPasswordToken: varchar('reset_password_token', { length: 255 }),
  resetPasswordExpire: datetime('reset_password_expire'),
  emailVerificationToken: varchar('email_verification_token', { length: 255 }),
  emailVerified: boolean('email_verified').default(false),
  lastLogin: datetime('last_login').default(new Date()),
  active: boolean('active').default(true),
  accountDeletionScheduled: datetime('account_deletion_scheduled'),
  accountDeleted: boolean('account_deleted').default(false),
  accountDeletedAt: datetime('account_deleted_at'),
  dataRetention: json('data_retention'),
  privacySettings: json('privacy_settings'),
  consents: json('consents'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const alertConfigurations = mysqlTable('alert_configurations', {
  id: varchar('id', { length: 255 }).primaryKey(),
  userId: varchar('user_id', { length: 255 }).notNull(),
  dataSource: varchar('data_source', { length: 255 }).notNull(),
  metricName: varchar('metric_name', { length: 255 }).notNull(),
  thresholdType: varchar('threshold_type', { length: 50 }).notNull(),
  thresholdValue: decimal('threshold_value', { precision: 20, scale: 8 }).notNull(),
  comparisonPeriod: int('comparison_period').notNull(),
  enabled: boolean('enabled').default(true),
  notificationChannels: text('notification_channels'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const userPreferences = mysqlTable('user_preferences', {
  id: varchar('id', { length: 255 }).primaryKey(),
  userId: varchar('user_id', { length: 255 }).notNull(),
  preferences: json('preferences'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const metrics = mysqlTable('metrics', {
  id: varchar('id', { length: 255 }).primaryKey(),
  dataSource: varchar('data_source', { length: 255 }).notNull(),
  metricName: varchar('metric_name', { length: 255 }).notNull(),
  value: decimal('value', { precision: 20, scale: 8 }).notNull(),
  unit: varchar('unit', { length: 50 }),
  status: mysqlEnum('status', ['healthy', 'warning', 'critical', 'stale']).default('healthy'),
  confidence: decimal('confidence', { precision: 3, scale: 2 }).default('1.00'),
  metadata: json('metadata'),
  rawData: json('raw_data'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const metricHistory = mysqlTable('metric_history', {
  id: varchar('id', { length: 255 }).primaryKey(),
  metricId: varchar('metric_id', { length: 255 }).notNull(),
  value: decimal('value', { precision: 20, scale: 8 }).notNull(),
  status: mysqlEnum('status', ['healthy', 'warning', 'critical', 'stale']).default('healthy'),
  confidence: decimal('confidence', { precision: 3, scale: 2 }).default('1.00'),
  metadata: json('metadata'),
  rawData: json('raw_data'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const scraperHealth = mysqlTable('scraper_health', {
  id: varchar('id', { length: 255 }).primaryKey(),
  scraperName: varchar('scraper_name', { length: 255 }).notNull(),
  status: mysqlEnum('status', ['healthy', 'degraded', 'failed']).notNull(),
  lastRun: timestamp('last_run').defaultNow(),
  nextRun: timestamp('next_run'),
  errorMessage: text('error_message'),
  executionTime: int('execution_time'), // in milliseconds
  dataQuality: mysqlEnum('data_quality', ['high', 'medium', 'low']).default('medium'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type AlertConfiguration = typeof alertConfigurations.$inferSelect;
export type NewAlertConfiguration = typeof alertConfigurations.$inferInsert;
export type UserPreferences = typeof userPreferences.$inferSelect;
export type NewUserPreferences = typeof userPreferences.$inferInsert;
export type Metric = typeof metrics.$inferSelect;
export type NewMetric = typeof metrics.$inferInsert;
export type MetricHistory = typeof metricHistory.$inferSelect;
export type NewMetricHistory = typeof metricHistory.$inferInsert;
export type ScraperHealth = typeof scraperHealth.$inferSelect;
export type NewScraperHealth = typeof scraperHealth.$inferInsert;
