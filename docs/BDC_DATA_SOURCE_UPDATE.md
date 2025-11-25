# BDC Data Source Update

## Problem
The BDC scraper was failing because RSS feeds were returning 404 errors. RSS feeds are not a reliable source for BDC NAV (Net Asset Value) data.

## Solution
Updated the BDC scraper to use multiple data sources with fallback mechanisms:

### Primary Source: SEC EDGAR Filings
- **Method**: Fetch 10-Q (quarterly) and 10-K (annual) filings from SEC EDGAR
- **Why**: BDCs are required by law to report NAV in their quarterly and annual SEC filings
- **Implementation**: 
  - Uses SEC EDGAR API to search for recent filings
  - Parses XBRL instance documents for structured NAV data
  - Falls back to HTML/text parsing if XBRL is not available
  - Respects SEC rate limits (10 requests/second)

### Fallback Sources (in order):
1. **Investor Relations Pages** - Scrapes company investor relations websites for NAV announcements
2. **RSS Feeds** - Legacy support (kept for backward compatibility, but expected to fail)
3. **Yahoo Finance** - Checks if NAV data is available in Yahoo Finance extended fields

## Changes Made

### Updated `scrapers/bdc_discount_scraper.py`:
- Added CIK codes for all BDCs (required for SEC EDGAR access)
- Implemented `_fetch_nav_from_sec_edgar()` - Primary NAV fetching method
- Implemented `_get_latest_bdc_filing()` - Gets most recent 10-Q/10-K filing
- Implemented `_parse_nav_from_filing()` - Parses NAV from SEC filings
- Implemented `_parse_nav_from_xbrl()` - Extracts NAV from XBRL documents
- Implemented `_parse_nav_from_html()` - Extracts NAV from HTML/text filings
- Implemented `_fetch_nav_from_ir_page()` - Fallback to investor relations pages
- Updated `_fetch_nav_from_rss()` - Now returns tuple with source info
- Implemented `_fetch_nav_from_yahoo()` - Fallback to Yahoo Finance
- Updated `fetch_data()` - Now tries all sources in order with proper fallback logic

### BDC Configuration:
Each BDC now has:
- `cik`: SEC CIK code (required for EDGAR access)
- `ir_url`: Investor relations page URL (fallback)
- `rss_url`: RSS feed URL (legacy fallback)
- `nav_pattern`: Regex pattern for NAV extraction

## BDC CIK Codes Used:
- **ARCC** (Ares Capital Corporation): `0001288879`
- **OCSL** (Oaktree Specialty Lending Corporation): `0001414932`
- **MAIN** (Main Street Capital Corporation): `0001396440`
- **PSEC** (Prospect Capital Corporation): `0001176438`

## Data Source Priority:
1. **SEC EDGAR** (10-Q/10-K filings) - Most reliable, official source
2. **Investor Relations Pages** - Company websites, may have recent NAV updates
3. **RSS Feeds** - Legacy support (may return 404)
4. **Yahoo Finance** - May have NAV in extended data fields

## Benefits:
- ✅ No longer dependent on RSS feeds
- ✅ Uses official SEC filings (most reliable source)
- ✅ Multiple fallback mechanisms ensure data availability
- ✅ Respects SEC rate limits
- ✅ Tracks data source for each NAV value (for transparency)

## Testing:
The scraper should now successfully fetch NAV data even when RSS feeds return 404 errors. Test with:
```python
from scrapers.bdc_discount_scraper import BDCDiscountScraper

scraper = BDCDiscountScraper()
result = scraper.execute()
print(result.data)
```

## Notes:
- SEC EDGAR requires a User-Agent header with contact information (configured via `SEC_EDGAR_EMAIL` env var)
- Rate limiting is implemented (100ms delay between requests = 10 req/sec max)
- NAV values are validated to be reasonable (between $1 and $1000 per share)
- Each NAV value includes its source in the metadata for transparency

