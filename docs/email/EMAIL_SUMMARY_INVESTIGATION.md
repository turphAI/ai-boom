# Email Summary Investigation - Agent Results

## Goal

Investigate sending agent results as email summaries so you don't have to manually check results.

## Use Cases

### Daily Summary Email
- **When**: After each GitHub Actions run (daily at 2 AM UTC)
- **What**: Summary of scraper executions, patterns detected, structure changes
- **Recipients**: You (and optionally team members)

### Weekly Digest
- **When**: Weekly summary of all activity
- **What**: Trends, patterns, recommendations
- **Recipients**: You

### Alert-Only Emails
- **When**: Only when critical issues detected
- **What**: Urgent failures, broken selectors, critical patterns
- **Recipients**: You (immediate notification)

## What to Include in Email

### Daily Summary Email Content

```
Subject: Boom-Bust Sentinel - Daily Agent Summary (Nov 25, 2025)

📊 Scraper Execution Summary
✅ Successful: 3/4
❌ Failed: 1/4
⏱️  Total Time: 45.23s

🔍 Failure Patterns Detected: 2
   - bdc_discount: RECURRING_ERROR (3 occurrences)
   - credit_fund: WEBSITE_STRUCTURE_CHANGE (2 occurrences)

🌐 Website Structure Monitoring
   - Monitored: 36 URLs
   - Changes Detected: 1
   - Selectors Adapted: 1

💡 Recommendations
   - Review bdc_discount scraper (RSS feed 404)
   - Check credit_fund selector adaptation

View Full Report: [Link to GitHub Actions]
```

### Alert Email Content (Critical Issues Only)

```
Subject: 🚨 CRITICAL: Scraper Failures Detected

❌ Critical Issues Found:

1. credit_fund: Multiple selector failures
   - Broken: .nav-value
   - Suggested: .net-asset-value-per-share
   - Action Required: Update scraper code

2. bdc_discount: Recurring 404 errors
   - Frequency: 5 occurrences
   - Suggested Fix: Switch to SEC EDGAR source

View Details: [Link]
```

## Existing Infrastructure

**Good News!** You already have an alert service (`services/alert_service.py`) with:
- ✅ Notification channel abstraction
- ✅ SNS channel (AWS)
- ✅ Telegram channel
- ✅ Dashboard channel

**We can leverage this** by adding an Email channel to the existing system!

## Email Service Options

### Option 1: SendGrid (Recommended)
- **Pros**: Easy API, free tier (100 emails/day), reliable
- **Cons**: Requires API key
- **Cost**: Free for < 100 emails/day
- **Setup**: Add SENDGRID_API_KEY to GitHub Secrets

### Option 2: AWS SES
- **Pros**: Already using AWS, very cheap ($0.10 per 1000 emails)
- **Cons**: Requires AWS setup, domain verification
- **Cost**: ~$0.10/month for daily emails
- **Setup**: Configure SES, verify domain

### Option 3: SMTP (Gmail/Outlook)
- **Pros**: Free, no API key needed
- **Cons**: Less reliable, rate limits, requires app password
- **Cost**: Free
- **Setup**: Configure SMTP credentials

### Option 4: GitHub Actions Email Action
- **Pros**: Built-in, simple
- **Cons**: Limited customization
- **Cost**: Free
- **Setup**: Use existing GitHub Actions email action

## Implementation Approach

### Option A: Add to Existing Alert Service (Recommended)
- Add `EmailNotificationChannel` to `services/alert_service.py`
- Leverage existing channel infrastructure
- Consistent with current architecture

### Option B: Standalone Email Service
- Create `agents/email_summary.py`
- Separate from alert service
- More focused on summaries vs alerts

### Phase 1: Email Generator
- Generate HTML/text email from agent results
- Format: Clean, readable, actionable
- Include links to GitHub Actions

### Phase 2: Email Sender
- Add EmailNotificationChannel to alert service (Option A)
- OR create standalone email sender (Option B)
- Integrate email service (SendGrid recommended)
- Handle errors gracefully

### Phase 3: Configuration
- Add email settings to `.env`
- Add email secrets to GitHub Secrets
- Configure recipients

### Phase 4: Testing
- Test email delivery
- Test formatting
- Test error handling

## Email Template Design

### HTML Email Template
- Clean, professional design
- Color-coded status (green/yellow/red)
- Clickable links to GitHub Actions
- Mobile-friendly

### Text Email Template
- Plain text fallback
- Same information, simpler format
- Works in all email clients

## Integration Points

### GitHub Actions Integration

```yaml
- name: Send email summary
  if: always()
  env:
    SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
    EMAIL_RECIPIENT: ${{ secrets.EMAIL_RECIPIENT }}
  run: |
    python scripts/send_agent_summary_email.py
```

### Conditional Sending

- **Always**: Send daily summary
- **On Failure**: Send alert email
- **Weekly**: Send digest (optional)

## Questions to Investigate

1. **Which email service?**
   - SendGrid (easiest)
   - AWS SES (if using AWS)
   - SMTP (simplest, but less reliable)

2. **Email frequency?**
   - Daily (after each run)
   - Weekly digest
   - Alert-only (only on failures)

3. **Email content?**
   - Summary only
   - Full details
   - Actionable recommendations

4. **Recipients?**
   - Single recipient (you)
   - Multiple recipients (team)
   - Configurable list

5. **Format?**
   - HTML (pretty)
   - Text (universal)
   - Both (HTML with text fallback)

## Next Steps

1. ✅ Research email service options
2. ✅ Design email template
3. ✅ Build email generator
4. ✅ Integrate into workflow
5. ✅ Test and deploy

## Estimated Effort

- **Research**: 1 hour
- **Implementation**: 2-3 hours
- **Testing**: 1 hour
- **Total**: ~4-5 hours

## Benefits

- ✅ **No manual checking**: Get results automatically
- ✅ **Faster response**: Know about issues immediately
- ✅ **Better visibility**: Team can see status
- ✅ **Actionable**: Clear recommendations in email

---

**Status**: TODO created - Ready to investigate!

