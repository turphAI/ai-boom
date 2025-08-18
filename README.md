# Boom Bust Sentinel - Financial Market Monitoring System

> **Last Updated:** $(date) - Force Vercel deployment update

A comprehensive financial market monitoring system that tracks various market indicators and provides real-time alerts for potential market crashes or booms.

## Features

- **Authentication**: NextAuth.js with email/password authentication
- **Current Metrics API**: Real-time access to current market metrics
- **Historical Data API**: Time-series data with aggregation and trend analysis
- **Alert Configuration**: User-configurable alert thresholds and notification preferences
- **User Preferences**: Customizable dashboard settings and notification channels
- **Security**: CORS protection, rate limiting, and secure headers
- **Database**: PlanetScale MySQL with Drizzle ORM

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/signin` - User login (NextAuth)
- `POST /api/auth/signout` - User logout (NextAuth)

### Metrics
- `GET /api/metrics/current` - Get current metric values
- `GET /api/metrics/historical` - Get historical data with aggregation

### Alert Configuration
- `GET /api/alerts/config` - Get user alert configurations
- `POST /api/alerts/config` - Create new alert configuration
- `PUT /api/alerts/config?id={id}` - Update alert configuration
- `DELETE /api/alerts/config?id={id}` - Delete alert configuration

### User Preferences
- `GET /api/user/preferences` - Get user preferences
- `PUT /api/user/preferences` - Update user preferences

## Repository Structure

- `dashboard/`: Next.js application (canonical frontend)
- `serverless.yml` and `handlers/`, `scrapers/`, `services/`: Python backend for AWS Lambda
- `tests/`: Python tests for backend
- `scripts/`: Ops and verification scripts

Root-level Next.js files have been removed; only `dashboard/` is used for the app.

## Dashboard Setup (in `dashboard/`)

1. Install dependencies:
```bash
cd dashboard
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Set up PlanetScale database:
```bash
npx drizzle-kit generate:mysql
npx drizzle-kit push:mysql
```

4. Run development server:
```bash
npm run dev
```

## Testing

Run API integration tests:
```bash
npm test
```

## Environment Variables

See `.env.example` for required environment variables:

- `DATABASE_HOST` - PlanetScale database host
- `DATABASE_USERNAME` - Database username
- `DATABASE_PASSWORD` - Database password
- `NEXTAUTH_SECRET` - NextAuth.js secret key
- `NEXTAUTH_URL` - Application URL
- `ALLOWED_ORIGIN` - CORS allowed origin
- `STATE_STORE_TABLE` - DynamoDB/Firestore table name for metrics data

## Integration with Main System

The dashboard connects to the existing Boom-Bust Sentinel state store (DynamoDB/Firestore) to fetch real-time and historical metrics data. The `StateStoreClient` class provides an abstraction layer for this integration.

## Security Features

- JWT-based authentication with NextAuth.js
- CORS protection with configurable origins
- Rate limiting on API endpoints
- Security headers (CSP, XSS protection, etc.)
- Input validation with Zod schemas
- SQL injection protection with Drizzle ORM

## Database Schema

The dashboard uses three main tables:
- `users` - User authentication and profile data
- `alert_configurations` - User-defined alert thresholds and settings
- `user_preferences` - Dashboard customization and notification preferences