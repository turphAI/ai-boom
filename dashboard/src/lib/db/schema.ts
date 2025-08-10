import { mysqlTable, varchar, text, timestamp, decimal, boolean, json, int } from 'drizzle-orm/mysql-core';

export const users = mysqlTable('users', {
  id: varchar('id', { length: 255 }).primaryKey(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: varchar('password_hash', { length: 255 }).notNull(),
  name: varchar('name', { length: 255 }),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const alertConfigurations = mysqlTable('alert_configurations', {
  id: varchar('id', { length: 255 }).primaryKey(),
  userId: varchar('user_id', { length: 255 }).notNull(),
  dataSource: varchar('data_source', { length: 100 }).notNull(),
  metricName: varchar('metric_name', { length: 100 }).notNull(),
  thresholdType: varchar('threshold_type', { length: 50 }).notNull(),
  thresholdValue: decimal('threshold_value', { precision: 15, scale: 2 }).notNull(),
  comparisonPeriod: int('comparison_period').notNull(),
  enabled: boolean('enabled').default(true),
  notificationChannels: json('notification_channels').$type<string[]>(),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export const userPreferences = mysqlTable('user_preferences', {
  id: varchar('id', { length: 255 }).primaryKey(),
  userId: varchar('user_id', { length: 255 }).notNull(),
  preferences: json('preferences').$type<{
    theme?: 'light' | 'dark';
    timezone?: string;
    defaultChartPeriod?: number;
    emailNotifications?: boolean;
    slackWebhook?: string;
    telegramBotToken?: string;
    telegramChatId?: string;
  }>(),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow().onUpdateNow(),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type AlertConfiguration = typeof alertConfigurations.$inferSelect;
export type NewAlertConfiguration = typeof alertConfigurations.$inferInsert;
export type UserPreferences = typeof userPreferences.$inferSelect;
export type NewUserPreferences = typeof userPreferences.$inferInsert;