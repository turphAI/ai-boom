# Setting Up .env File for Agent System

Yes! You can absolutely place your Anthropic API key in a `.env` file. This is actually the **recommended approach** for local development.

## Quick Setup

### Step 1: Create .env File

In your project root (`/Users/turphai/Projects/kiro_aiCrash/`), create a `.env` file:

```bash
touch .env
```

### Step 2: Add Your API Key

Open `.env` and add:

```bash
# LLM Agent Configuration
ENABLE_LLM_AGENT=true
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 3: Make Sure .env is in .gitignore

**IMPORTANT**: Never commit your `.env` file to git! Make sure it's in `.gitignore`:

```bash
# Check if .env is ignored
cat .gitignore | grep "\.env"

# If not, add it:
echo ".env" >> .gitignore
```

### Step 4: That's It!

The agent will automatically load your `.env` file. No need to export environment variables manually!

## Example .env File

Here's a complete example `.env` file:

```bash
# Database Configuration
DATABASE_URL=mysql://username:password@host/database?sslaccept=strict

# LLM Agent Configuration
ENABLE_LLM_AGENT=true
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Specify model (default: claude-3-sonnet-20240229)
# ANTHROPIC_MODEL=claude-3-opus-20240229

# Optional: Log directory
# AGENT_LOG_DIR=logs/agent
```

## How It Works

The agent code automatically loads `.env` files using `python-dotenv`:

```python
# This is already in agents/llm_agent.py
from dotenv import load_dotenv
load_dotenv()  # Loads .env automatically
```

So when you do:
```python
from agents.llm_agent import LLMAgent
agent = LLMAgent()
```

It will automatically read `ANTHROPIC_API_KEY` from your `.env` file!

## Testing

After creating your `.env` file:

```bash
# Test that it works
python agents/demo.py
```

You should see:
```
✅ LLM Agent initialized with Anthropic (claude-3-sonnet-20240229)
```

## Security Best Practices

1. **Never commit .env to git**
   ```bash
   # Check .gitignore
   cat .gitignore | grep "\.env"
   
   # Should show: .env
   ```

2. **Use .env.example for templates**
   - Create `.env.example` with placeholder values
   - Commit `.env.example` to git
   - Never commit actual `.env` file

3. **Different keys for different environments**
   - `.env.local` for local development
   - `.env.production` for production (use secrets manager instead)
   - `.env.staging` for staging

## Troubleshooting

### "LLM Agent enabled but no API key found"

1. Check `.env` file exists:
   ```bash
   ls -la .env
   ```

2. Check key is set correctly:
   ```bash
   cat .env | grep ANTHROPIC_API_KEY
   ```

3. Make sure key starts with `sk-ant-`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...  ✅ Correct
   ANTHROPIC_API_KEY=sk-ant...   ❌ Missing dash
   ```

4. Check python-dotenv is installed:
   ```bash
   pip install python-dotenv
   ```

### Environment Variable Not Loading

If `.env` isn't loading, you can manually load it:

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file

from agents.llm_agent import LLMAgent
agent = LLMAgent()
```

## Alternative: Environment Variables

If you prefer not to use `.env` files, you can still use environment variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export ENABLE_LLM_AGENT=true
```

But `.env` files are more convenient for local development!

## Summary

✅ **Yes, you can use .env file!**

1. Create `.env` in project root
2. Add `ANTHROPIC_API_KEY=sk-ant-...`
3. Add `.env` to `.gitignore` (if not already)
4. Done! Agent loads it automatically

No need to export environment variables manually! 🎉

