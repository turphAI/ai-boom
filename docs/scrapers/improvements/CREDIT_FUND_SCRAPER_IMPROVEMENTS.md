# Credit Fund Scraper Improvements

## Problem
The credit fund scraper was failing when no recent Form PF filings were found, causing the entire scraper run to fail with:
```
ValueError: No private credit fund data could be retrieved from SEC Form PF filings
```

## Root Cause
Form PF filings are filed quarterly/annually and may not always be available:
- Filings may not be publicly available immediately after submission
- Filings may be filed under different CIKs (subsidiaries)
- Filings may not be processed by SEC EDGAR yet
- Some funds may not be required to file Form PF

## Solution
Updated the credit fund scraper to be more resilient:

### 1. Extended Date Range
- **Before**: Only looked for recent filings (implicit date restriction)
- **After**: Looks back up to 365 days (1 year) for Form PF filings
- **Benefit**: Finds older filings if recent ones aren't available

### 2. Increased Search Scope
- **Before**: Searched for 10 filings
- **After**: Searches for 20 filings
- **Benefit**: More likely to find available filings

### 3. Better Error Handling
- **Before**: Failed immediately if no filings found
- **After**: 
  - Tries alternative sources (10-K filings) as fallback
  - Provides detailed error messages explaining why data might not be available
  - Logs helpful debugging information

### 4. Partial Data Support
- **Before**: Required data from all funds
- **After**: Works with partial data if at least some funds have data
- **Benefit**: Scraper can succeed even if some funds don't have filings

### 5. Improved Logging
- Added debug logging for date range checks
- Better error messages explaining potential reasons for missing data
- Logs which funds were attempted

## Changes Made

### Updated `scrapers/credit_fund_scraper.py`:
- Modified `_get_latest_form_pf()` to accept `max_age_days` parameter (default: 365)
- Added date range validation to accept filings up to 1 year old
- Increased filing count from 10 to 20
- Added `_try_alternative_sources()` method for fallback data sources
- Updated `fetch_data()` to handle partial data and try alternatives
- Improved error messages with helpful explanations
- Updated `_download_form_pf_xml()` to only use mock data when explicitly enabled

## Expected Behavior

### Success Cases:
1. **Recent filings available**: Uses most recent Form PF filings (within 365 days)
2. **Older filings available**: Uses older filings if recent ones aren't available
3. **Partial data**: Succeeds if at least some funds have data

### Failure Cases:
- Only fails if NO data can be found from ANY source
- Provides detailed error message explaining why
- Logs all attempted funds for debugging

## Testing
The scraper should now:
- ✅ Find older Form PF filings if recent ones aren't available
- ✅ Work with partial data (some funds missing)
- ✅ Provide helpful error messages when data truly isn't available
- ✅ Log detailed debugging information

## Notes
- Form PF filings are filed quarterly/annually, so gaps in data are expected
- The scraper now looks back up to 1 year for filings
- Alternative sources (10-K parsing) are a placeholder for future enhancement
- Mock data is only used when `USE_MOCK_DATA=true` environment variable is set

