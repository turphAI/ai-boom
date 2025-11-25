# Setting Up DATABASE_URL

## Problem
The `DATABASE_URL` environment variable is blank, which prevents scrapers from storing data in PlanetScale.

## Solution: Get Your PlanetScale Connection String

### Step 1: Access PlanetScale Dashboard

1. Go to [PlanetScale Dashboard](https://app.planetscale.com/)
2. Log in to your account
3. Select your database (likely named `ai-awareness` based on your code)

### Step 2: Get Connection String

1. Click on your database
2. Click the **"Connect"** button (usually in the top right)
3. Select **"Node.js"** or **"General"** connection type
4. Copy the connection string - it will look like:
   ```
   mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict
   ```

### Step 3: Set Up GitHub Secret

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `DATABASE_URL`
5. Value: Paste your PlanetScale connection string
6. Click **"Add secret"**

### Step 4: Test Locally (Optional)

To test the connection locally before running GitHub Actions:

```bash
# Set the environment variable
export DATABASE_URL="mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict"
export ENVIRONMENT="production"

# Test the connection
python scripts/diagnose_scraper_status.py

# Or test connection directly
python scripts/test_planetscale_connection.py
```

## Format Requirements

Your DATABASE_URL should be in this format:
```
mysql://username:password@host.connect.psdb.cloud/database_name?sslaccept=strict
```

**Important Notes:**
- Must start with `mysql://`
- Username and password are separated by `:`
- Host should be something like `xxxxx.connect.psdb.cloud`
- Database name comes after the `/`
- SSL parameter `?sslaccept=strict` is required

## Example (DO NOT USE THIS - GET YOUR OWN)

```
mysql://abc123:pscale_pw_xyz789@aws.connect.psdb.cloud/ai-awareness?sslaccept=strict
```

## Troubleshooting

### "DATABASE_URL not set" error
- Verify the secret is named exactly `DATABASE_URL` (case-sensitive)
- Check that you added it to **Actions secrets**, not environment secrets

### Connection fails
- Verify the connection string is correct
- Check that your PlanetScale database is active (not sleeping)
- Ensure SSL parameter is included (`?sslaccept=strict`)

### Password contains special characters
- If your password has special characters, they may need to be URL-encoded
- PlanetScale usually generates passwords that are URL-safe, but if you have issues, check the connection string format

## Security Notes

⚠️ **Never commit DATABASE_URL to git!**
- Always use GitHub Secrets for production
- Use environment variables locally
- Add `.env` to `.gitignore` if you create one

## Next Steps

After setting up DATABASE_URL:
1. Test the connection: `python scripts/diagnose_scraper_status.py`
2. Manually trigger GitHub Actions workflow to test
3. Verify data appears in PlanetScale after workflow runs

