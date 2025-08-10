# 🧪 Test Accounts for Boom-Bust Sentinel Dashboard

## Quick Login Credentials

### Demo User
- **Email**: `demo@example.com`
- **Password**: `demo123`
- **Role**: Standard user with sample alert configurations

### Admin User  
- **Email**: `admin@example.com`
- **Password**: `admin123`
- **Role**: Admin user with full access

## Sample Data Included

### Alert Configurations
- **Bond Issuance Alert**: Triggers when weekly issuance > $5B
- **BDC Discount Alert**: Triggers on 5% average discount change
- **Credit Fund Alert**: Triggers on 10% asset mark change (disabled)

### User Preferences
- Light theme
- Eastern timezone
- 30-day default chart period
- Email notifications enabled

## How to Reset Test Data

Run the setup script again to recreate all test data:

```bash
cd dashboard
node scripts/setup-test-data.js
```

## Database Location

Local SQLite database: `dashboard/local.db`

## Quick Start

1. Start the dashboard: `npm run dev`
2. Go to: http://localhost:3000
3. Sign in with any test account above
4. Explore the interface!

---

*Note: These are development-only accounts. Never use these credentials in production.*