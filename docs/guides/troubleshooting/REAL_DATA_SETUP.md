# Real Data Setup Guide

This guide explains how to switch from mock data to real data in the Boom-Bust Sentinel dashboard.

## 🎯 **Overview**

The dashboard currently uses mock data for demonstration purposes. To use real data, you need to:

1. **Run the scrapers** to collect real financial data
2. **Configure the APIs** to read from real data files
3. **Set up automated data collection** for continuous updates

## 🚀 **Quick Start**

### **1. Generate Real Data**

Run the scrapers to collect real financial data:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all scrapers once
python scripts/run_scrapers.py

# Or start continuous data pipeline (runs every 30 minutes)
./scripts/start_data_pipeline.sh
```

### **2. Start the Dashboard**

```bash
# Start the Next.js dashboard
npm run dev

# Visit http://localhost:3000
```

## 📊 **Data Sources**

The system collects data from these sources:

| Data Source | File | Description |
|-------------|------|-------------|
| **Bond Issuance** | `data/bond_issuance_weekly.json` | SEC EDGAR bond filings |
| **BDC Discount** | `data/bdc_discount_discount_to_nav.json` | BDC NAV discounts |
| **Credit Fund** | `data/comprehensive_test_test_metric.json` | Form PF filings |
| **Bank Provision** | `data/health_check_database_test.json` | 10-Q filings |

## 🔧 **API Configuration**

### **System Health API** (`src/pages/api/system/health.ts`)

- ✅ **Real Data**: Checks file timestamps to determine scraper health
- ✅ **Database**: Tests actual database connectivity
- ✅ **Fallback**: Uses mock data if real data fails

### **Metrics API** (`src/pages/api/metrics/current.ts`)

- ✅ **Real Data**: Reads from actual data files
- ✅ **Calculations**: Computes real change percentages
- ✅ **Fallback**: Uses mock data if files missing

### **Alert Config API** (`src/pages/api/alerts/config.ts`)

- ✅ **Real Data**: Reads/writes to actual database
- ✅ **Validation**: Validates real alert configurations

## 📁 **Data File Structure**

Real data files follow this structure:

```json
[
  {
    "data_source": "bond_issuance",
    "metric_name": "weekly",
    "timestamp": "2025-08-15 22:16:12.033574+00:00",
    "data": {
      "value": 3500000000,
      "timestamp": "2025-08-15 22:16:12.033574+00:00",
      "confidence": 0.75,
      "metadata": {
        "companies": ["MSFT", "META"],
        "avg_coupon": 4.35,
        "bond_count": 2,
        "source": "sec_edgar"
      }
    }
  }
]
```

## 🔄 **Automated Data Collection**

### **Option 1: Manual Updates**

Run scrapers manually when needed:

```bash
python scripts/run_scrapers.py
```

### **Option 2: Continuous Pipeline**

Start the data pipeline for automatic updates:

```bash
./scripts/start_data_pipeline.sh
```

This runs scrapers every 30 minutes.

### **Option 3: Cron Job (Production)**

Add to crontab for production:

```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/kiro_aiCrash && source venv/bin/activate && python scripts/run_scrapers.py
```

## 🚨 **Troubleshooting**

### **No Data Showing**

1. **Check if scrapers ran successfully:**
   ```bash
   python scripts/run_scrapers.py
   ```

2. **Verify data files exist:**
   ```bash
   ls -la data/
   ```

3. **Check file permissions:**
   ```bash
   chmod 644 data/*.json
   ```

### **API Errors**

1. **Check API logs** in the browser console
2. **Verify authentication** is working
3. **Check database connectivity**

### **Scraper Failures**

Common issues and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | Rate limiting | Wait and retry |
| `404 Not Found` | API endpoint changed | Update scraper URLs |
| `No data retrieved` | External API down | Use fallback data |

## 📈 **Monitoring Real Data**

### **Dashboard Indicators**

- **System Health**: Shows real scraper status
- **Metrics**: Displays actual financial values
- **Alerts**: Based on real thresholds

### **Data Quality**

The system includes data validation:

- **Confidence scores** (0.0-1.0)
- **Anomaly detection**
- **Data checksums**
- **Source verification**

## 🔐 **Security Considerations**

### **API Keys**

Some scrapers require API keys:

```bash
# Set environment variables
export SEC_EDGAR_EMAIL="your-email@domain.com"
export YAHOO_FINANCE_API_KEY="your-api-key"
```

### **Rate Limiting**

Respect API rate limits:

- **SEC EDGAR**: 10 requests/second
- **Yahoo Finance**: 100 requests/hour
- **Form PF**: 100 requests/day

## 🎯 **Next Steps**

1. **Run scrapers** to generate initial data
2. **Start dashboard** to view real data
3. **Configure alerts** based on real thresholds
4. **Set up monitoring** for data quality
5. **Deploy to production** with automated pipelines

## 📞 **Support**

If you encounter issues:

1. Check the logs in the terminal
2. Verify data files exist and are readable
3. Test individual scrapers
4. Review API responses in browser dev tools

---

**🎉 You're now using real financial data!**
