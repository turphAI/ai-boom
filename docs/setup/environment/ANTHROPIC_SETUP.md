# Setting Up Anthropic (Claude) API for LLM Agent

The LLM Agent supports Anthropic's Claude models. Here's how to set it up.

## Quick Setup

### 1. Install Anthropic Package

```bash
pip install anthropic
```

Or add to `requirements.txt`:
```
anthropic>=0.7.0
```

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or add to your `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
ENABLE_LLM_AGENT=true
```

### 3. That's It!

The agent will automatically detect your Anthropic key and use Claude models.

## Available Claude Models

The agent supports these Claude models:

- **`claude-3-opus-20240229`** - Most capable, best for complex analysis
- **`claude-3-sonnet-20240229`** - Balanced performance (default)
- **`claude-3-haiku-20240307`** - Fastest, most cost-effective

### Default Model

If you don't specify a model, it defaults to `claude-3-sonnet-20240229` (good balance of quality and cost).

### Specify a Different Model

```python
from agents.llm_agent import LLMAgent

# Use Claude Opus (most capable)
agent = LLMAgent(model="claude-3-opus-20240229")

# Use Claude Haiku (fastest/cheapest)
agent = LLMAgent(model="claude-3-haiku-20240307")
```

## Cost Comparison

### Anthropic Claude Pricing (as of 2024)

- **Claude Opus**: ~$0.015 per 1K input tokens, ~$0.075 per 1K output tokens
- **Claude Sonnet**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **Claude Haiku**: ~$0.00025 per 1K input tokens, ~$0.00125 per 1K output tokens

### Estimated Monthly Cost

For typical scraper error analysis (~500 tokens per analysis):

- **Claude Opus**: ~$0.05-0.10 per analysis → ~$5-15/month
- **Claude Sonnet**: ~$0.01-0.02 per analysis → ~$1-5/month (recommended)
- **Claude Haiku**: ~$0.001-0.002 per analysis → ~$0.10-0.50/month

**Recommendation**: Start with Claude Sonnet - good balance of quality and cost.

## Testing Your Setup

### Quick Test

```python
from agents.llm_agent import LLMAgent

agent = LLMAgent()

if agent.is_enabled():
    print(f"✅ LLM Agent enabled with {agent.model}")
    print(f"   Client type: {agent.client_type}")
else:
    print("❌ LLM Agent not enabled")
    print("   Check your ANTHROPIC_API_KEY environment variable")
```

### Run Demo

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export ENABLE_LLM_AGENT=true

# Run demo
python agents/demo.py
```

## Troubleshooting

### "anthropic package not installed"

```bash
pip install anthropic
```

### "LLM Agent enabled but no API key found"

Make sure you've set the environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or check your `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### "Failed to initialize LLM client"

Check:
1. API key is correct (starts with `sk-ant-`)
2. API key has credits/quota
3. Internet connection is working
4. Anthropic package is installed: `pip install anthropic`

### Using Both OpenAI and Anthropic

If you have both API keys set, the agent will:
- Prefer Anthropic by default
- Use OpenAI if you specify a GPT model explicitly
- Use Anthropic if you specify a Claude model explicitly

Example:
```python
# Uses Anthropic (default)
agent = LLMAgent()

# Uses OpenAI (explicit)
agent = LLMAgent(model="gpt-4")

# Uses Anthropic (explicit)
agent = LLMAgent(model="claude-3-opus-20240229")
```

## Getting Your API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)
6. Set it as environment variable

## Security Best Practices

1. **Never commit API keys to git**
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Use separate keys for dev/prod**
   - Different keys for different environments
   - Rotate keys regularly

3. **Monitor usage**
   - Check Anthropic dashboard for usage
   - Set up billing alerts

4. **Limit access**
   - Use least privilege principle
   - Don't share keys

## Example Usage

```python
import os
from agents.llm_agent import LLMAgent
from agents.pattern_analyzer import FailurePattern

# Set API key (or use environment variable)
os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-your-key-here'

# Create agent (auto-detects Anthropic)
agent = LLMAgent()

if agent.is_enabled():
    # Analyze a failure pattern
    analysis = agent.analyze_error(pattern)
    
    print(f"Root cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence:.2f}")
    print(f"Suggested fix: {analysis.suggested_fix}")
    print(f"Explanation: {analysis.explanation}")
```

## Next Steps

1. ✅ Install anthropic: `pip install anthropic`
2. ✅ Set API key: `export ANTHROPIC_API_KEY=sk-ant-...`
3. ✅ Test: `python agents/demo.py`
4. ✅ Integrate into your code

That's it! The agent will now use Claude for intelligent error analysis.

