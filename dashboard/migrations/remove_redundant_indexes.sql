-- Migration: Remove redundant indexes as recommended by PlanetScale Insights
-- These indexes are redundant because they duplicate primary keys or unique constraints
-- Created: 2025-01-XX

-- #19: Remove redundant index idx_year_month on table dividend_monthly_summaries
ALTER TABLE dividend_monthly_summaries DROP INDEX idx_year_month;

-- #18: Remove redundant index idx_symbol on table dividend_entries
ALTER TABLE dividend_entries DROP INDEX idx_symbol;

-- #17: Remove redundant index idx_email on table users
-- Note: email column already has UNIQUE constraint, making this index redundant
ALTER TABLE users DROP INDEX idx_email;

-- #16: Remove redundant index idx_user_id on table topic_preferences
ALTER TABLE topic_preferences DROP INDEX idx_user_id;

-- #15: Remove redundant index idx_user_id on table summary_preferences
ALTER TABLE summary_preferences DROP INDEX idx_user_id;

-- #14: Remove redundant index idx_user_id on table notification_settings
ALTER TABLE notification_settings DROP INDEX idx_user_id;

-- #13: Remove redundant index idx_user_id on table interest_profiles
ALTER TABLE interest_profiles DROP INDEX idx_user_id;

-- #12: Remove redundant index idx_content_id on table interactions
ALTER TABLE interactions DROP INDEX idx_content_id;

-- #11: Remove redundant index idx_user_id on table interactions
ALTER TABLE interactions DROP INDEX idx_user_id;

-- #10: Remove redundant index idx_user_id on table discovery_settings
ALTER TABLE discovery_settings DROP INDEX idx_user_id;

-- #9: Remove redundant index idx_user_id on table digest_scheduling
ALTER TABLE digest_scheduling DROP INDEX idx_user_id;

-- #8: Remove redundant index idx_user_id on table credentials
ALTER TABLE credentials DROP INDEX idx_user_id;

-- #7: Remove redundant index idx_user_id on table content_volume_settings
ALTER TABLE content_volume_settings DROP INDEX idx_user_id;

-- #6: Remove redundant index idx_source_content on table content_references
ALTER TABLE content_references DROP INDEX idx_source_content;

-- #5: Remove redundant index idx_source_id on table content
ALTER TABLE content DROP INDEX idx_source_id;

-- #4: Remove redundant index idx_user_id on table collections
ALTER TABLE collections DROP INDEX idx_user_id;

-- #3: Remove redundant index idx_collection_id on table collection_content
ALTER TABLE collection_content DROP INDEX idx_collection_id;

-- #2: Remove redundant index idx_collection_id on table collection_collaborators
ALTER TABLE collection_collaborators DROP INDEX idx_collection_id;

-- #1: Remove redundant index idx_name on table categories
ALTER TABLE categories DROP INDEX idx_name;

