# 🤖 OpenRouter AI Agent

An autonomous AI agent that runs for free on GitHub Actions using OpenRouter API.

## Features

- 🔄 Runs automatically every 6 hours
- 🔧 Supports shell commands and web search
- 📝 Saves results as artifacts
- 📅 Creates issues with results
- 💰 Uses free OpenRouter models

## Setup

1. **Fork this repository**

2. **Add your OpenRouter API key:**
   - Go to Settings → Secrets and variables → Actions
   - Add `OPENROUTER_API_KEY` with your key from [openrouter.ai/keys](https://openrouter.ai/keys)

3. **Optional: Change the model**
   - Add `OPENROUTER_MODEL` with any model (e.g., `openrouter/free`)

4. **Customize the agent's goal**
   - Edit the `AGENT_GOAL` in the workflow file or use manual trigger

## Usage

- **Automatic:** Runs every 6 hours
- **Manual:** Go to Actions → "Run AI Agent" → "Run workflow"
- **Results:** Check "Artifacts" or "Issues" tab

## Extending

Add new tools in `agent.js`:
```javascript
// Add a new tool
your_new_tool: {
  description: 'What it does',
  parameters: { param: { type: 'string', description: '...' } },
  execute: async ({ param }) => {
    // Implement tool logic
    return result;
  }
}
