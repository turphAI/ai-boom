# Boom-Bust Sentinel - Complete Setup Guide

This guide will help you set up the Boom-Bust Sentinel application to work end-to-end with proper authentication, database connectivity, and real data scraping.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the complete setup script
./scripts/startup_complete_system.sh
```

### Option 2: Manual Setup
Follow the detailed steps below.

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **MySQL** (local or PlanetScale account)
- **Git** (to clone the repository)

## 🔧 Step-by-Step Setup

### 1. Environment Setup

#### Python Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Node.js Environment
```bash
cd dashboard
npm install
```

### 2. Database Configuration

#### Option A: Local MySQL Database
```bash
# Install MySQL (macOS)
brew install mysql

# Install MySQL (Ubuntu)
sudo apt-get install mysql-server

# Start MySQL service
brew services start mysql  # macOS
sudo systemctl start mysql  # Ubuntu

# Setup local database
cd dashboard
./scripts/setup-local-database.sh
```

#### Option B: PlanetScale Database
1. Create a PlanetScale account at [planetscale.com](https://planetscale.com)
2. Create a new database
3. Get your connection string
4. Update `.env.local`:
```bash
DATABASE_URL=mysql://username:password@host/database?sslaccept=strict
```

### 3. Environment Variables

Create `dashboard/.env.local`:
```bash
# Database Configuration
DATABASE_URL=mysql://username:password@host/database?sslaccept=strict

# NextAuth Configuration
NEXTAUTH_SECRET=your-super-secret-key-change-this-in-production
NEXTAUTH_URL=http://localhost:3000

# CORS Configuration
ALLOWED_ORIGIN=http://localhost:3000

# State Store Configuration
STATE_STORE_TABLE=boom-bust-metrics

# Development Settings
NODE_ENV=development
```

### 4. Database Schema Setup

```bash
cd dashboard
npm run db:generate  # Generate schema migrations
npm run db:push      # Push schema to database
```

### 5. Initial Data Generation

```bash
# Run scrapers to generate initial data
cd ..
source venv/bin/activate
python scripts/run_all_scrapers_safe.py
```

### 6. Start the Application

#### Start Dashboard Only
```bash
cd dashboard
npm run dev
```

#### Start Complete System
```bash
# From project root
./start_full_system.sh
```

## 🎯 Access the Application

- **Dashboard**: http://localhost:3000
- **API Health**: http://localhost:3000/api/system/health
- **Metrics API**: http://localhost:3000/api/metrics/current

### Default Login Credentials (Local Setup)
- **Email**: test@example.com
- **Password**: testpassword123

## 📊 Data Sources

The system scrapes data from these sources:

| Data Source | Description | Update Frequency |
|-------------|-------------|------------------|
| **Bond Issuance** | SEC EDGAR bond filings | Daily/Weekly |
| **BDC Discount** | BDC NAV discounts | Daily |
| **Credit Fund** | Form PF filings | Quarterly |
| **Bank Provision** | 10-Q filings | Quarterly |

## 🔄 Data Scraping Schedule

### Manual Scraping
```bash
# Run all scrapers once
./start_scrapers.sh

# Run individual scrapers
python scripts/run_credit_fund_scraper.py
python scripts/run_bank_provision_scraper.py
python scripts/run_bond_issuance_scraper.py
python scripts/run_bdc_discount_scraper.py
```

### Automated Scraping
```bash
# Set up cron job for daily scraping (weekdays only)
crontab -e

# Add this line:
0 9 * * 1-5 cd /path/to/boom-bust-sentinel && ./start_scrapers.sh
```

## 🛠️ Troubleshooting

### Authentication Issues
1. **Check environment variables**: Ensure `NEXTAUTH_SECRET` is set
2. **Database connectivity**: Verify `DATABASE_URL` is correct
3. **User creation**: Run database setup script to create test user

### Database Issues
1. **Connection errors**: Check database credentials in `.env.local`
2. **Schema issues**: Run `npm run db:push` in dashboard directory
3. **Missing tables**: Ensure database setup script completed successfully

### Data Scraping Issues
1. **No data files**: Check if scrapers are running successfully
2. **Outdated data**: Run scrapers manually to refresh data
3. **File permissions**: Ensure write access to `data/` directory

### Dashboard Issues
1. **Build errors**: Run `npm install` in dashboard directory
2. **API errors**: Check browser console for detailed error messages
3. **Port conflicts**: Ensure port 3000 is available

## 📁 Project Structure

```
boom-bust-sentinel/
├── dashboard/                 # Next.js dashboard
│   ├── src/
│   │   ├── lib/db/           # Database schema and connection
│   │   ├── pages/api/        # API endpoints
│   │   └── components/       # React components
│   ├── scripts/              # Database setup scripts
│   └── .env.local           # Environment variables
├── scrapers/                 # Python data scrapers
├── services/                 # Backend services
├── data/                     # Scraped data files
├── logs/                     # Application logs
└── scripts/                  # Utility scripts
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env.local` to version control
2. **Database Credentials**: Use strong passwords and secure connections
3. **API Keys**: Rotate API keys regularly
4. **HTTPS**: Use HTTPS in production environments

## 🚀 Production Deployment

### Environment Setup
1. Set `NODE_ENV=production`
2. Use production database (PlanetScale recommended)
3. Set secure `NEXTAUTH_SECRET`
4. Configure proper CORS origins

### Database
- Use PlanetScale or AWS RDS for production
- Enable SSL connections
- Set up automated backups

### Monitoring
- Set up application monitoring (e.g., Vercel Analytics)
- Monitor scraper execution logs
- Set up alerts for data quality issues

## 📞 Support

If you encounter issues:

1. **Check logs**: Look in `logs/scraper_safe_run.log`
2. **Verify setup**: Run the startup script again
3. **Database issues**: Check database connectivity and credentials
4. **Environment issues**: Verify all environment variables are set

## 🎉 Success Indicators

Your setup is successful when:

- ✅ Dashboard loads at http://localhost:3000
- ✅ You can login with test credentials
- ✅ System health shows green status
- ✅ Metrics display real data (not mock data)
- ✅ Scrapers run without errors
- ✅ Data files are created in `data/` directory

---

**Note**: This system is designed to work with real financial data. Ensure you comply with all relevant data usage policies and rate limits when scraping external sources.
