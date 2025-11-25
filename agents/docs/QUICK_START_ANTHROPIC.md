# Quick Start with Anthropic (Claude)

## 3-Step Setup

### Step 1: Install Package

```bash
pip install anthropic
```

### Step 2: Set API Key

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or add to `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
ENABLE_LLM_AGENT=true
```

### Step 3: Test It

```bash
python agents/demo.py
```

You should see:
```
✅ LLM Agent initialized with Anthropic (claude-3-sonnet-20240229)
```

## That's It!

The agent will automatically:
- ✅ Detect your Anthropic key
- ✅ Use Claude Sonnet (good balance of quality/cost)
- ✅ Provide intelligent error analysis

## Cost Estimate

- **Claude Sonnet**: ~$1-5/month for typical usage
- **Claude Haiku**: ~$0.10-0.50/month (cheapest)
- **Claude Opus**: ~$5-15/month (most capable)

**Recommendation**: Start with Sonnet (default) - great quality at reasonable cost.

## Need Help?

See `docs/ANTHROPIC_SETUP.md` for detailed setup instructions.

