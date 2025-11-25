# Database Migrations

This directory contains SQL migration files for the PlanetScale database.

## Removing Redundant Indexes

PlanetScale Insights has identified several redundant indexes that can be safely removed. These indexes are redundant because they duplicate primary keys, unique constraints, or other indexes.

### Running the Migration

#### Option 1: Using the Node.js Script (Recommended)

```bash
cd dashboard
npm run db:remove-redundant-indexes
```

Or directly:

```bash
node scripts/remove-redundant-indexes.js
```

#### Option 2: Using PlanetScale CLI

```bash
pscale connect <database-name> <branch-name> --port 3309
mysql -h 127.0.0.1 -P 3309 -u <username> -p < migrations/remove_redundant_indexes.sql
```

#### Option 3: Using PlanetScale Dashboard

1. Go to your PlanetScale database dashboard
2. Navigate to the "Branches" section
3. Create a new branch or use an existing one
4. Open the SQL editor
5. Copy and paste the contents of `remove_redundant_indexes.sql`
6. Execute the migration
7. Create a deploy request to merge to main

### What This Migration Does

This migration removes 19 redundant indexes:

1. `idx_name` on `categories`
2. `idx_collection_id` on `collection_collaborators`
3. `idx_collection_id` on `collection_content`
4. `idx_user_id` on `collections`
5. `idx_source_id` on `content`
6. `idx_source_content` on `content_references`
7. `idx_user_id` on `content_volume_settings`
8. `idx_user_id` on `credentials`
9. `idx_user_id` on `digest_scheduling`
10. `idx_user_id` on `discovery_settings`
11. `idx_user_id` on `interactions`
12. `idx_content_id` on `interactions`
13. `idx_user_id` on `interest_profiles`
14. `idx_user_id` on `notification_settings`
15. `idx_user_id` on `summary_preferences`
16. `idx_user_id` on `topic_preferences`
17. `idx_email` on `users` (email already has UNIQUE constraint)
18. `idx_symbol` on `dividend_entries`
19. `idx_year_month` on `dividend_monthly_summaries`

### Safety Notes

- All DROP INDEX statements use `IF EXISTS`, so the migration is safe to run even if some indexes have already been removed
- The migration is idempotent - you can run it multiple times safely
- These indexes are redundant and removing them will:
  - Reduce storage overhead
  - Improve write performance
  - Simplify index maintenance
  - Not affect query performance (since they duplicate existing constraints/indexes)

### Verification

After running the migration, you can verify the indexes have been removed by checking PlanetScale Insights. The recommendations should disappear once the indexes are dropped.

