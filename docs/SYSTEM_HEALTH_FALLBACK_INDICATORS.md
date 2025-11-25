# System Health Fallback Indicators

## Overview
Added visual indicators to the System Health UI to show when scrapers use fallback data sources or encounter partial data situations. This provides awareness without being overly detailed.

## Changes Made

### 1. API Endpoint (`dashboard/src/pages/api/system/health.ts`)
- Updated SQL query to fetch `raw_data` and `metadata` columns from metrics table
- Added logic to extract fallback information from scraper metadata:
  - **BDC Discount**: Detects when NAV data comes from fallback sources (Yahoo Finance, RSS, IR pages)
  - **Credit Fund**: Detects when using alternative sources or partial data (some funds missing)
  - **Bank Provision**: Detects when using transcript analysis fallback instead of XBRL parsing
- Returns `fallbackInfo` object with type, message, and optional sources/reason

### 2. Type Definitions (`dashboard/src/types/dashboard.ts`)
- Extended `SystemHealth` interface to include:
  - `fallbackInfo`: Object containing fallback type, message, sources, and reason
  - `metadata`: Object containing data quality and source information

### 3. System Health Component (`dashboard/src/components/dashboard/SystemHealth.tsx`)
- Added `Info` icon import from lucide-react
- Displays fallback indicators with appropriate styling:
  - **Fallback**: Amber/yellow color with warning icon (⚠️)
  - **Partial**: Blue color with info icon (ℹ️)
- Shows data quality indicator when quality is not "high"
- Displays source information when available

### 4. System Health Page (`dashboard/src/pages/system-health.tsx`)
- Updated data transformation to pass through `fallbackInfo` and `metadata` from API response

## Visual Indicators

### Fallback Indicators
- **Type: fallback** - Shows amber/yellow text with warning icon
  - Example: "⚠️ Using fallback data sources (yahoo_finance, rss_feed)"
  - Example: "⚠️ Using alternative data sources - Form PF filings not available"
  - Example: "⚠️ Using transcript analysis fallback - XBRL parsing unavailable"

### Partial Data Indicators
- **Type: partial** - Shows blue text with info icon
  - Example: "ℹ️ Partial data available - Some funds missing"

### Data Quality Indicators
- Shows when data quality is not "high"
  - Example: "Data quality: medium"
  - Example: "Data quality: low"

## Examples

### BDC Discount Scraper
When NAV data comes from Yahoo Finance instead of SEC EDGAR:
```
BDC Discount Scraper
Last update: 2025-11-25 18:00:36
⚠️ Using fallback data sources (yahoo_finance)
```

### Credit Fund Scraper
When Form PF filings aren't available and using alternative sources:
```
Credit Fund Scraper
Last update: 2025-11-25 18:00:39
⚠️ Using alternative data sources - Form PF filings not available
Data quality: low
```

### Credit Fund Scraper (Partial Data)
When some funds have data but not all:
```
Credit Fund Scraper
Last update: 2025-11-25 18:00:39
ℹ️ Partial data available - Some funds missing
Data quality: medium
```

### Bank Provision Scraper
When using transcript analysis instead of XBRL:
```
Bank Provision Scraper
Last update: 2025-11-25 18:00:55
⚠️ Using transcript analysis fallback - XBRL parsing unavailable
```

## Benefits
- ✅ Provides awareness of data source quality without overwhelming detail
- ✅ Helps identify when scrapers are using fallback mechanisms
- ✅ Shows data quality indicators for transparency
- ✅ Non-intrusive visual indicators that don't clutter the UI
- ✅ Helps users understand when data might be less reliable

## Technical Notes
- Fallback information is extracted from scraper metadata stored in the database
- Metadata is parsed from JSON stored in `raw_data` or `metadata` columns
- Indicators only show when fallback/partial situations occur
- All indicators are subtle and informational, not error messages

