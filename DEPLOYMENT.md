# Dashboard Deployment Guide

## Vercel Deployment

### Prerequisites
1. Vercel account
2. PlanetScale database (or compatible MySQL database)
3. Environment variables configured

### Environment Variables
Set these in your Vercel project settings:

```bash
NEXTAUTH_URL=https://your-domain.vercel.app
NEXTAUTH_SECRET=your-secret-key-here
DATABASE_URL=mysql://username:password@host/database
```

### Deployment Steps

1. **Connect to Vercel**
   ```bash
   npm install -g vercel
   vercel login
   vercel --prod
   ```

2. **Configure Environment Variables**
   - Go to Vercel dashboard
   - Select your project
   - Go to Settings > Environment Variables
   - Add the required variables

3. **Deploy**
   ```bash
   vercel --prod
   ```

### Automatic Deployments
- Connect your GitHub repository to Vercel
- Enable automatic deployments from main branch
- Set up preview deployments for pull requests

### Database Setup
1. Create PlanetScale database
2. Run database migrations:
   ```bash
   npm run db:push
   ```
3. Seed initial data if needed

### Monitoring
- Enable Vercel Analytics
- Set up error tracking with Sentry (optional)
- Configure uptime monitoring

## Local Development

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Set up Environment Variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your values
   ```

3. **Run Development Server**
   ```bash
   npm run dev
   ```

4. **Run Tests**
   ```bash
   npm test
   ```

## Features Implemented

- ✅ Next.js with TypeScript and Tailwind CSS
- ✅ shadcn/ui component library
- ✅ Real-time metric display with cards and badges
- ✅ Interactive charts using Recharts
- ✅ Alert configuration interface with forms and dialogs
- ✅ System health status indicators
- ✅ Visual indicators for stale data
- ✅ Responsive design for mobile and desktop
- ✅ Authentication with NextAuth.js
- ✅ Auto-refresh functionality
- ✅ Vercel deployment configuration

## API Endpoints

- `GET /api/metrics/current` - Current metric values
- `GET /api/metrics/historical` - Historical data for charts
- `GET /api/alerts/config` - Alert configurations
- `POST /api/alerts/config` - Create alert configuration
- `PUT /api/alerts/config/[id]` - Update alert configuration
- `DELETE /api/alerts/config/[id]` - Delete alert configuration
- `GET /api/system/health` - System health status