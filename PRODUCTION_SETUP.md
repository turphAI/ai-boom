# Production Setup Guide

This guide covers all required environment variables and configurations for deploying the Boom-Bust Sentinel to production.

## 🚀 Vercel Environment Variables

Configure these in your Vercel project settings:

### Database Configuration (Required)

Choose ONE of these options:

**Option A: Single DATABASE_URL**
```
DATABASE_URL=mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict
```

**Option B: Separate credentials**
```
DATABASE_HOST=host.connect.psdb.cloud
DATABASE_USERNAME=your-username
DATABASE_PASSWORD=your-password
```

### Authentication (Required)

```
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=https://ai-boom-iota.vercel.app
```

**Generate NEXTAUTH_SECRET:**
```bash
openssl rand -base64 32
```

### Optional: Debug Token (for seeding/testing)

```
AUTH_DEBUG_TOKEN=your-debug-token
```

## 🔧 GitHub Repository Secrets

Configure these in GitHub Settings > Secrets and variables > Actions:

### Required for Automated Scrapers

1. **DATABASE_URL**
   - Same as Vercel DATABASE_URL
   - Allows GitHub Actions to sync data to PlanetScale

2. **FRED_API_KEY** (Optional but recommended)
   - Get from: https://fred.stlouisfed.org/docs/api/api_key.html
   - Free API key for economic data
   - Used by credit_fund and bank_provision scrapers

## 📊 PlanetScale Database Setup

### 1. Create Database Tables

The schema is defined in `dashboard/src/lib/db/schema.ts`. Tables needed:

- `users` - User accounts
- `alert_configurations` - User alert settings
- `user_preferences` - User preferences
- `metrics` - Current metric values
- `metric_history` - Historical metric data
- `scraper_health` - Scraper health status

### 2. Seed Initial Data

After deployment, seed the database with initial metrics:

```bash
# Using the protected API endpoint
curl -X POST \
  -H "Authorization: Bearer YOUR_AUTH_DEBUG_TOKEN" \
  https://ai-boom-iota.vercel.app/api/metrics/seed
```

This will populate the database with sample metrics so the dashboard displays data.

### 3. Verify Data

Check that metrics are available:

```bash
curl https://ai-boom-iota.vercel.app/api/metrics/current
curl "https://ai-boom-iota.vercel.app/api/metrics/historical?days=30"
```

## 🤖 GitHub Actions Setup

### 1. Enable Actions

- Go to repository Settings > Actions > General
- Ensure "Allow all actions and reusable workflows" is selected

### 2. Add Required Secrets

See "GitHub Repository Secrets" section above.

### 3. Manual Trigger (First Run)

1. Go to Actions tab
2. Select "Run Data Scrapers" workflow
3. Click "Run workflow" > "Run workflow" button
4. Monitor the execution in the Actions tab
5. Verify data appears in production dashboard

### 4. Automated Schedule

After the first successful run, the workflow will automatically run:
- **Daily at 2 AM UTC** (9 PM EST / 6 PM PST)

## 🔐 Authentication Setup

### Current Configuration

- Strategy: JWT (JSON Web Tokens)
- Session storage: In-memory (JWT tokens)
- User storage: PlanetScale database

### Create First User

Use the registration API or create directly in database:

```bash
curl -X POST https://ai-boom-iota.vercel.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-secure-password",
    "name": "Admin User"
  }'
```

### Known Issues & Improvements

1. **Session Persistence**
   - Current: JWT strategy (sessions in browser only)
   - Consider: Database sessions for better control
   - To switch: Change `session.strategy` to `"database"` in `dashboard/src/lib/auth/config.ts`

2. **Email Verification**
   - Currently disabled
   - Enable by setting up email provider (SendGrid, etc.)

## 📈 Monitoring & Health Checks

### System Health Endpoint

```bash
curl https://ai-boom-iota.vercel.app/api/system/health
```

Returns:
- Database connectivity
- Scraper health status
- Overall system health percentage

### Metrics Endpoints

```bash
# Current metrics (5 metrics including correlation)
GET /api/metrics/current

# Historical data (30 days by default)
GET /api/metrics/historical?days=30

# System health
GET /api/system/health
```

## 🐛 Troubleshooting

### Dashboard Shows "No Data"

1. Check API endpoints return data:
   ```bash
   curl https://ai-boom-iota.vercel.app/api/metrics/current
   ```

2. If empty, seed the database:
   ```bash
   curl -X POST \
     -H "Authorization: Bearer YOUR_AUTH_DEBUG_TOKEN" \
     https://ai-boom-iota.vercel.app/api/metrics/seed
   ```

3. Run the scraper workflow manually (GitHub Actions)

### Build Failures

- Check Vercel deployment logs
- Verify all environment variables are set
- Ensure DATABASE_URL is valid and database is accessible

### Authentication Issues

1. **Can't login:**
   - Verify NEXTAUTH_SECRET is set
   - Check database connectivity
   - Ensure user exists in database

2. **Session expires immediately:**
   - Check NEXTAUTH_URL matches deployment URL
   - Verify JWT secret is consistent across deployments

### Scraper Workflow Failures

1. Check GitHub Actions logs
2. Verify DATABASE_URL secret is set
3. Ensure PlanetScale database is accessible from GitHub Actions
4. Check FRED_API_KEY if using FRED-based scrapers

## ✅ Deployment Checklist

- [ ] PlanetScale database created
- [ ] Database tables created (via Drizzle schema)
- [ ] Vercel environment variables configured
- [ ] GitHub repository secrets configured
- [ ] Initial database seed completed
- [ ] First user account created
- [ ] Scraper workflow tested manually
- [ ] Dashboard displays metrics correctly
- [ ] Authentication working (login/logout)
- [ ] System health endpoint returns healthy status

## 📚 Additional Resources

- [PlanetScale Docs](https://planetscale.com/docs)
- [NextAuth.js Docs](https://next-auth.js.org)
- [Vercel Deployment Docs](https://vercel.com/docs)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [FRED API Docs](https://fred.stlouisfed.org/docs/api/)






