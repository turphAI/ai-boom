# Scraper Automation & Data Storage Fix Plan

## Problem Summary

### Issue 1: Scrapers Not Running Automatically
- **Current State**: GitHub Actions workflow exists (`run-scrapers.yml`) but scrapers are failing
- **Root Causes**:
  1. GitHub Actions may not be enabled or secrets not configured
  2. Workflow uses two-step process (local files → sync) which is fragile
  3. No verification that workflow is actually running
  4. Lambda functions exist but may not be deployed to AWS

### Issue 2: Data Not Being Stored Correctly
- **Current State**: Database health shows healthy, but dashboards show no periodic data
- **Root Causes**:
  1. Scrapers write to local JSON files first, then sync separately
  2. Sync step can fail silently
  3. No direct write to PlanetScale from scrapers in GitHub Actions
  4. State store may not be configured correctly for production environment

## Solution Strategy

### Phase 1: Fix GitHub Actions Workflow (Primary Solution)
**Goal**: Make GitHub Actions the reliable, primary automation mechanism

1. **Ensure Direct PlanetScale Storage**
   - Modify scrapers to write directly to PlanetScale when `ENVIRONMENT=production`
   - Remove dependency on local file storage → sync step
   - Use `PlanetScaleStateStore` directly in production

2. **Fix Workflow Configuration**
   - Verify GitHub Actions is enabled
   - Ensure `DATABASE_URL` secret is configured
   - Add better error handling and logging
   - Add verification step to confirm data was stored

3. **Add Monitoring & Alerts**
   - Add workflow status checks
   - Create health check endpoint that verifies data freshness
   - Add notifications on failure

### Phase 2: Backup Automation (AWS Lambda)
**Goal**: Deploy Lambda functions as backup/alternative automation

1. **Deploy Serverless Functions**
   - Deploy `serverless.yml` to AWS
   - Configure CloudWatch Events schedules
   - Ensure Lambda functions have DATABASE_URL in environment

2. **Verify Lambda Execution**
   - Test each handler manually
   - Verify CloudWatch logs show successful execution
   - Confirm data is stored in PlanetScale

### Phase 3: Data Storage Verification
**Goal**: Ensure data is actually being stored and accessible

1. **Fix State Store Configuration**
   - Ensure `ENVIRONMENT=production` uses PlanetScaleStateStore
   - Remove file-based fallbacks in production
   - Add connection retry logic

2. **Add Data Verification**
   - Create script to verify recent data exists in PlanetScale
   - Add to workflow as verification step
   - Update health check to verify data freshness

## Implementation Steps

### Step 1: Diagnose Current State ✅ COMPLETED
- [x] Created diagnostic script (`scripts/diagnose_scraper_status.py`)
- [ ] Check if GitHub Actions workflow is enabled (user needs to verify)
- [ ] Verify DATABASE_URL secret exists (user needs to verify)
- [ ] Check recent workflow runs and their status (user needs to check)
- [ ] Verify PlanetScale database has recent data (run diagnostic script)
- [ ] Check if Lambda functions are deployed (optional backup)

### Step 2: Fix GitHub Actions Workflow ✅ COMPLETED
- [x] Updated `run-scrapers.yml` to use production environment
- [x] Modified `run_all_scrapers_safe.py` to write directly to PlanetScale in production
- [x] Added verification step (`scripts/verify_planetscale_data.py`) after scrapers run
- [x] Fixed PlanetScale storage method call signature
- [x] Added better error handling and logging
- [ ] Test workflow manually (user needs to trigger)

### Step 3: Fix Data Storage
- [ ] Ensure `StateStore()` initializes PlanetScaleStateStore in production
- [ ] Remove file-based storage from production path
- [ ] Add retry logic for database connections
- [ ] Test scraper execution locally with production environment

### Step 4: Add Monitoring
- [ ] Create diagnostic script to check system health
- [ ] Add data freshness check to health endpoint
- [ ] Update dashboard to show last successful scraper run
- [ ] Add alerts for stale data

### Step 5: Deploy & Verify
- [ ] Deploy updated workflow
- [ ] Run workflow manually to test
- [ ] Verify data appears in PlanetScale
- [ ] Verify dashboard shows fresh data
- [ ] Monitor for 3-5 days to ensure stability

## Files to Modify

1. **`.github/workflows/run-scrapers.yml`**
   - Ensure ENVIRONMENT=production
   - Remove sync step (scrapers write directly)
   - Add verification step

2. **`services/state_store.py`**
   - Ensure production uses PlanetScaleStateStore
   - Add better error handling

3. **`scrapers/base.py`**
   - Ensure state_store is initialized correctly
   - Add logging for storage operations

4. **`scripts/run_all_scrapers_safe.py`**
   - Update to use PlanetScale directly in production
   - Remove local file storage dependency

5. **`dashboard/src/pages/api/system/health.ts`**
   - Add data freshness check
   - Verify recent data exists in PlanetScale

## Testing Checklist

- [ ] Run scrapers locally with `ENVIRONMENT=production`
- [ ] Verify data appears in PlanetScale
- [ ] Test GitHub Actions workflow manually
- [ ] Verify workflow completes successfully
- [ ] Check PlanetScale for new data after workflow run
- [ ] Verify dashboard shows fresh data
- [ ] Test error scenarios (missing secrets, DB connection failure)

## Success Criteria

1. ✅ GitHub Actions workflow runs daily without errors
2. ✅ Data is stored directly in PlanetScale (no intermediate files)
3. ✅ Dashboard shows fresh data within 24 hours
4. ✅ System health shows scrapers as "healthy"
5. ✅ Data freshness is verified automatically

## Rollback Plan

If issues occur:
1. Revert workflow changes
2. Re-enable two-step process temporarily
3. Investigate specific failure point
4. Fix and re-deploy

## Timeline

- **Day 1**: Diagnose current state, fix GitHub Actions workflow
- **Day 2**: Fix data storage, test locally
- **Day 3**: Deploy and verify, monitor for issues
- **Days 4-7**: Monitor daily runs, fix any issues

