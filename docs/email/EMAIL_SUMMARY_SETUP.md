# Email Summary Setup Guide

## Overview

Email summaries are now integrated into the alert service! You'll receive daily email summaries of agent results automatically.

## Quick Setup

### Option 1: SendGrid (Recommended - Easiest)

1. **Get SendGrid API Key**:
   - Sign up at https://sendgrid.com (free tier: 100 emails/day)
   - Go to Settings → API Keys
   - Create API Key with "Mail Send" permissions

2. **Add to GitHub Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add `SENDGRID_API_KEY`: Your SendGrid API key
   - Add `EMAIL_RECIPIENT`: Your email address
   - Add `EMAIL_FROM`: (Optional) From address, defaults to `noreply@boom-bust-sentinel.com`

3. **Done!** Emails will be sent automatically after each scraper run.

### Option 2: SMTP (Gmail, Outlook, etc.)

1. **Get SMTP Credentials**:
   - **Gmail**: Create App Password (Settings → Security → App Passwords)
   - **Outlook**: Use your regular password or App Password

2. **Add to GitHub Secrets**:
   - `SMTP_HOST`: `smtp.gmail.com` (Gmail) or `smtp-mail.outlook.com` (Outlook)
   - `SMTP_PORT`: `587` (TLS)
   - `SMTP_USER`: Your email address
   - `SMTP_PASSWORD`: Your app password
   - `EMAIL_RECIPIENT`: Your email address
   - `EMAIL_FROM`: Your email address

3. **Done!** Emails will be sent automatically.

## Local Testing

### Test Email Configuration

```bash
source venv/bin/activate

# Set environment variables
export SENDGRID_API_KEY="your-api-key"
export EMAIL_RECIPIENT="your-email@example.com"

# Send test email
python scripts/send_agent_summary_email.py --test
```

### Send Latest Report

```bash
# Send latest agent report
python scripts/send_agent_summary_email.py

# Send to specific recipient
python scripts/send_agent_summary_email.py --recipient your-email@example.com
```

## Email Content

### Daily Summary Email Includes:

- ✅ **Scraper Execution Summary**
  - Success/failure counts
  - Success rate
  - Execution times

- 🔍 **Scraper Results**
  - Individual scraper status
  - Error messages (if any)

- 🔍 **Failure Patterns**
  - Detected patterns
  - Suggested fixes
  - Confidence scores

- 📊 **Visual Status**
  - Color-coded (green/yellow/red)
  - HTML formatted
  - Mobile-friendly

### Example Email Subject:

- ✅ `Boom-Bust Sentinel Summary (Nov 25, 2025) - All 4 Scrapers Successful`
- ⚠️ `Boom-Bust Sentinel Summary (Nov 25, 2025) - 3/4 Successful, 1 Failed`

## Configuration

### Environment Variables

**Required**:
- `EMAIL_RECIPIENT`: Email address to send summaries to

**Email Provider** (choose one):

**SendGrid**:
- `SENDGRID_API_KEY`: Your SendGrid API key

**SMTP**:
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP port (usually 587)
- `SMTP_USER`: SMTP username (your email)
- `SMTP_PASSWORD`: SMTP password or app password

**Optional**:
- `EMAIL_FROM`: From address (defaults to `noreply@boom-bust-sentinel.com`)

### GitHub Actions Secrets

Add these to your repository secrets:

```
SENDGRID_API_KEY=your-sendgrid-api-key
EMAIL_RECIPIENT=your-email@example.com
EMAIL_FROM=noreply@boom-bust-sentinel.com  # Optional
```

Or for SMTP:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_RECIPIENT=your-email@example.com
```

## When Emails Are Sent

### Automated (GitHub Actions)

- ✅ **After each scraper run** (daily at 2 AM UTC)
- ✅ **Always** (even if scrapers fail)
- ✅ **Includes latest report**

### Manual

```bash
# Send latest report
python scripts/send_agent_summary_email.py

# Send all reports
python scripts/send_agent_summary_email.py --all

# Send test email
python scripts/send_agent_summary_email.py --test
```

## Troubleshooting

### Email Not Sending

1. **Check Configuration**:
   ```bash
   python scripts/send_agent_summary_email.py --test
   ```

2. **Check Logs**:
   - Look for email-related errors in GitHub Actions logs
   - Check SendGrid dashboard for delivery status

3. **Verify Secrets**:
   - Ensure secrets are set in GitHub repository
   - Check secret names match exactly

### SendGrid Issues

- **API Key Invalid**: Regenerate API key in SendGrid dashboard
- **Rate Limit**: Free tier is 100 emails/day
- **Domain Verification**: May need to verify sender domain for production

### SMTP Issues

- **Authentication Failed**: Check username/password
- **Connection Timeout**: Check SMTP host/port
- **Gmail**: Must use App Password, not regular password

## Cost

### SendGrid
- **Free Tier**: 100 emails/day
- **Paid**: $15/month for 50,000 emails

### SMTP
- **Free**: Unlimited (Gmail, Outlook free tiers)
- **Limits**: May have daily sending limits

## Benefits

- ✅ **No manual checking**: Get results automatically
- ✅ **Faster response**: Know about issues immediately
- ✅ **Beautiful formatting**: HTML emails with color coding
- ✅ **Actionable**: Clear recommendations included
- ✅ **Mobile-friendly**: Works on all devices

## Next Steps

1. ✅ Set up email provider (SendGrid or SMTP)
2. ✅ Add secrets to GitHub
3. ✅ Test with `--test` flag
4. ✅ Wait for next scraper run
5. ✅ Receive your first email summary!

---

**Status**: Ready to use! Just configure your email provider and you're done! 🎉

