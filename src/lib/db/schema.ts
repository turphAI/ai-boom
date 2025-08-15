import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  name: text('name'),
  createdAt: text('created_at').default('CURRENT_TIMESTAMP'),
  updatedAt: text('updated_at').default('CURRENT_TIMESTAMP'),
});

export const alertConfigurations = sqliteTable('alert_configurations', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull(),
  dataSource: text('data_source').notNull(),
  metricName: text('metric_name').notNull(),
  thresholdType: text('threshold_type').notNull(),
  thresholdValue: real('threshold_value').notNull(),
  comparisonPeriod: integer('comparison_period').notNull(),
  enabled: integer('enabled').default(1),
  notificationChannels: text('notification_channels'),
  createdAt: text('created_at').default('CURRENT_TIMESTAMP'),
  updatedAt: text('updated_at').default('CURRENT_TIMESTAMP'),
});

export const userPreferences = sqliteTable('user_preferences', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull(),
  preferences: text('preferences'),
  createdAt: text('created_at').default('CURRENT_TIMESTAMP'),
  updatedAt: text('updated_at').default('CURRENT_TIMESTAMP'),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type AlertConfiguration = typeof alertConfigurations.$inferSelect;
export type NewAlertConfiguration = typeof alertConfigurations.$inferInsert;
export type UserPreferences = typeof userPreferences.$inferSelect;
export type NewUserPreferences = typeof userPreferences.$inferInsert;