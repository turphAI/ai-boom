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
  thresholdValue: varchar('threshold_value', { length: 50 }).notNull(),
  comparisonPeriod: int('comparison_period').notNull(),
  enabled: boolean('enabled').default(true),
  notificationChannels: text('notification_channels'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const userPreferences = mysqlTable('user_preferences', {
  id: varchar('id', { length: 255 }).primaryKey(),
  userId: varchar('user_id', { length: 255 }).notNull(),
  preferences: text('preferences'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type AlertConfiguration = typeof alertConfigurations.$inferSelect;
export type NewAlertConfiguration = typeof alertConfigurations.$inferInsert;
export type UserPreferences = typeof userPreferences.$inferSelect;
export type NewUserPreferences = typeof userPreferences.$inferInsert;