# Fix: DATABASE_URL Secret Format Issue

## Problem
The GitHub secret `DATABASE_URL` contains the variable name and quotes:
```
DATABASE_URL='mysql://...'
```

But it should only contain the connection string itself:
```
mysql://...
```

## Two Solutions

### Solution 1: Fix GitHub Secret (RECOMMENDED)

1. Go to GitHub → Settings → Secrets and variables → Actions
2. Find `DATABASE_URL` secret
3. Click "Update" or delete and recreate it
4. **Value should be ONLY the connection string:**
   ```
   mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict
   (Replace with your actual PlanetScale connection string from the dashboard)
   ```
5. **DO NOT include:**
   - `DATABASE_URL=`
   - Quotes (`'` or `"`)
   - Variable name

### Solution 2: Code Fix (Applied)

I've also updated the code to automatically strip any `DATABASE_URL=` prefix or quotes, so it will work even if the secret has them. But it's still better to fix the secret itself.

## Correct Format

The secret value should be:
```
mysql://username:password@host.connect.psdb.cloud/database?ssl={"rejectUnauthorized":true}
```

**NOT:**
```
DATABASE_URL='mysql://...'
```

## Next Steps

1. **Fix the GitHub secret** (remove `DATABASE_URL=` and quotes)
2. **Commit and push the code fix** (already done - handles edge cases)
3. **Re-run the workflow**

## Testing

After fixing the secret, the workflow should:
- ✅ Parse the URL correctly
- ✅ Connect to PlanetScale
- ✅ Run scrapers successfully
- ✅ Store data in PlanetScale

