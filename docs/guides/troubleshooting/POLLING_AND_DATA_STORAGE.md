# Polling Frequency and Data Storage Improvements

## Polling Frequency Changes

### Before
- **Auto-refresh**: Every 30 seconds
- **Issue**: Excessive for financial data that updates infrequently

### After
- **Auto-refresh**: Every 24 hours (86,400,000ms)
- **Manual refresh**: Available via "Refresh" button in header
- **Rationale**: Financial data typically updates:
  - Bond Issuance: Daily/weekly
  - BDC Discount: Daily
  - Credit Fund Assets: Quarterly (Form PF filings)
  - Bank Provisions: Quarterly (10-Q filings)

## Data Storage Architecture

### Database Schema
Added `metrics_data` table to store historical metrics:

```sql
CREATE TABLE metrics_data (
  id TEXT PRIMARY KEY,
  data_source TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  confidence REAL DEFAULT 1.0,
  metadata TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
- `idx_metrics_data_source_name`: For filtering by data source and metric
- `idx_metrics_data_timestamp`: For date range queries

### Data Retention
- **Local Development**: SQLite with 90 days of historical data
- **Production**: DynamoDB with 730-day TTL (2 years)
- **Fallback**: Mock data generation if database unavailable

## Implementation Details

### Historical API Changes
- **Before**: Generated mock data on each request, limited to 30 days
- **After**: Queries database with fallback to mock data, requests 4+ years of data
- **Benefits**: 
  - Consistent data across requests
  - Real historical trends
  - Better performance (no regeneration)
  - Appropriate data frequencies (quarterly for Credit Funds/Bank Provisions, daily for others)
  - Smart chart type selection (bar charts for quarterly, area charts for daily)
  - Full historical view with 17 quarters of data

### Data Population
- **Script**: `npm run db:populate`
- **Coverage**: 
  - Daily metrics: 365 days of data
  - Quarterly metrics: 17 quarters (4+ years) of data
- **Features**:
  - Realistic volatility patterns
  - Gradual trends over time
  - Confidence scores
  - Metadata for debugging
  - Appropriate data frequencies (daily vs quarterly)

### Dashboard Updates
- **Header**: Shows auto-refresh frequency
- **Manual Refresh**: Available for immediate updates
- **Loading States**: Proper feedback during data fetching
- **Smart Chart Types**: 
  - Bar charts for quarterly data (Credit Funds, Bank Provisions)
  - Area charts for daily data (Bond Issuance, BDC Discount)
- **Quarterly Labels**: X-axis shows "Q1 2025", "Q2 2025", etc. for quarterly data
- **Danger Thresholds**: Red dashed lines visible above bars for quarterly charts

## Usage

### Development Setup
```bash
# Populate database with historical data
npm run db:populate

# Start development server
npm run dev
```

### Production Considerations
- **Database**: Use DynamoDB/Firestore for scalability
- **Data Pipeline**: Connect to backend scrapers for real data
- **Monitoring**: Track API response times and data freshness
- **Caching**: Consider Redis for frequently accessed data

## Benefits

1. **Reduced Server Load**: Less frequent API calls
2. **Better User Experience**: Manual refresh control
3. **Data Consistency**: Persistent historical data
4. **Scalability**: Database-backed storage
5. **Reliability**: Fallback mechanisms for data availability

## Future Enhancements

1. **Configurable Polling**: User-selectable refresh intervals
2. **Real-time Updates**: WebSocket connections for live data
3. **Data Export**: CSV/JSON download of historical data
4. **Advanced Analytics**: Trend analysis and forecasting
5. **Multi-tenant**: User-specific data views and preferences
