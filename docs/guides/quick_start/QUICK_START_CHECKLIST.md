# Quick Start Checklist - Scraper Agents

## ✅ What's Done

- [x] Agent system built and ready
- [x] Anthropic API key configured in `.env`
- [x] GitHub Actions workflow updated
- [x] Integrated scraper runner created
- [x] Report viewer created

## 🎯 Next Steps (In Order)

### Step 1: Add API Key to GitHub Secrets ⏳

**Required for automated runs**

1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: `your-anthropic-api-key-here` (get from https://console.anthropic.com/)
5. Click "Add secret"

**Time**: 2 minutes

---

### Step 2: Test Locally First ✅

**Verify everything works before pushing**

```bash
# Activate venv
source venv/bin/activate

# Run scrapers with agents
python scripts/run_scrapers_with_agents.py
```

**What to expect**:
- All scrapers run
- Agent monitoring happens automatically
- Report generated in `logs/agent_reports/`

**Time**: 5-10 minutes

---

### Step 3: View the Report 📊

**See what agents detected**

```bash
# View latest report
python scripts/view_agent_report.py

# Or view health summary
python scripts/view_agent_report.py --health
```

**Time**: 1 minute

---

### Step 4: Commit and Push 🚀

**Deploy the updated workflow**

```bash
git add .github/workflows/run-scrapers.yml
git add agents/
git add scripts/run_scrapers_with_agents.py
git add scripts/view_agent_report.py
git commit -m "Add agent monitoring to scraper workflow"
git push
```

**Time**: 2 minutes

---

### Step 5: Wait for Next GitHub Actions Run ⏰

**Agents will run automatically**

- GitHub Actions runs daily at 2 AM UTC
- Or trigger manually: Actions → Run Data Scrapers → Run workflow

**After it runs**:
- Check Actions tab for results
- Download agent reports from artifacts
- Review any detected patterns

**Time**: Wait for next scheduled run (or trigger manually)

---

## 🎉 That's It!

Once Step 1-4 are done, agents will:
- ✅ Run automatically with every scraper execution
- ✅ Monitor all executions
- ✅ Detect failure patterns
- ✅ Analyze errors with Claude
- ✅ Generate reports automatically

**You don't need to do anything else** - it's all automated!

---

## 📋 Optional: Regular Review

**Weekly** (optional):
- Review agent reports: `python scripts/view_agent_report.py --all`
- Check for recurring patterns
- Review suggested fixes

**Monthly** (optional):
- Review LLM costs (should be ~$1-5/month)
- Export execution history for analysis
- Update fix proposals based on patterns

---

## 🆘 Troubleshooting

### Agents not running in GitHub Actions?
- Check API key is in Secrets
- Check workflow file was pushed
- Check Actions logs for errors

### Want to disable LLM (free monitoring only)?
- Set `ENABLE_LLM_AGENT=false` in GitHub Secrets
- Or remove `ANTHROPIC_API_KEY` secret
- Agents will still monitor and detect patterns (just no AI analysis)

### Reports not generating?
- Check `logs/agent_reports/` directory exists
- Check scrapers are actually running
- Check file permissions

---

## 📚 Documentation

- **Setup**: `docs/ANTHROPIC_SETUP.md`
- **Integration**: `docs/AGENT_AUTOMATION_INTEGRATION.md`
- **Next Steps**: `docs/AGENT_NEXT_STEPS.md`
- **Explanation**: `docs/SCRAPER_AGENT_EXPLANATION.md`

---

## Summary

**Right Now**: 
1. Add API key to GitHub Secrets (2 min)
2. Test locally (5-10 min)
3. Commit and push (2 min)

**Then**: 
- Agents run automatically forever! 🎉

**Total Setup Time**: ~15 minutes

