// agent.js - OpenRouter Agent with Tool Support
import fetch from 'fetch';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Configuration
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const MODEL = process.env.OPENROUTER_MODEL || 'openrouter/free';
const MAX_STEPS = 10;

// Tool Definitions
const tools = {
  // 1. Execute shell commands
  execute_shell: {
    description: 'Execute a shell command and return the output',
    parameters: {
      command: {
        type: 'string',
        description: 'The shell command to execute'
      }
    },
    execute: async ({ command }) => {
      try {
        const { stdout, stderr } = await execAsync(command);
        return stdout || stderr || 'Command executed with no output';
      } catch (error) {
        return `Error: ${error.message}`;
      }
    }
  },

  // 2. Web search (using a free API)
  search_web: {
    description: 'Search the web using DuckDuckGo (free, no API key needed)',
    parameters: {
      query: {
        type: 'string',
        description: 'The search query'
      }
    },
    execute: async ({ query }) => {
      try {
        const response = await fetch(`https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`);
        const data = await response.json();
        if (data.AbstractText) {
          return data.AbstractText;
        } else if (data.RelatedTopics && data.RelatedTopics.length > 0) {
          return data.RelatedTopics.slice(0, 3).map(t => t.Text).join('\n');
        } else {
          return 'No results found for your query.';
        }
      } catch (error) {
        return `Search error: ${error.message}`;
      }
    }
  },

  // 3. Fetch web content
  fetch_webpage: {
    description: 'Fetch the content of a webpage',
    parameters: {
      url: {
        type: 'string',
        description: 'The URL to fetch'
      }
    },
    execute: async ({ url }) => {
      try {
        const response = await fetch(url);
        const html = await response.text();
        // Return first 1000 characters as a preview
        return html.substring(0, 1000) + '... (truncated)';
      } catch (error) {
        return `Error fetching URL: ${error.message}`;
      }
    }
  }
};

// The main agent function
async function runAgent(goal) {
  console.log(`🎯 Starting agent with goal: ${goal}`);
  console.log(`🧠 Using model: ${MODEL}`);
  
  let messages = [
    {
      role: 'system',
      content: `You are an AI agent that can perform tasks by using tools.
Available tools:
${Object.entries(tools).map(([name, tool]) => 
  `- ${name}: ${tool.description}`
).join('\n')}

To use a tool, respond with:
{
  "tool": "tool_name",
  "params": { "param1": "value1", "param2": "value2" }
}

If you have finished the task, respond with:
{
  "final_answer": "your final answer here"
}

Always check the output of a tool before proceeding. You have ${MAX_STEPS} steps maximum.`
    },
    {
      role: 'user',
      content: goal
    }
  ];

  let steps = 0;
  let finalAnswer = null;

  while (steps < MAX_STEPS && !finalAnswer) {
    steps++;
    console.log(`\n📝 Step ${steps}/${MAX_STEPS}`);

    try {
      // Call OpenRouter API
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
          'HTTP-Referer': process.env.GITHUB_REPOSITORY || 'https://github.com',
          'X-Title': 'GitHub Agent'
        },
        body: JSON.stringify({
          model: MODEL,
          messages: messages,
          max_tokens: 1000,
          temperature: 0.7
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        throw new Error(`API call failed: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage = data.choices[0].message.content;
      console.log('🤖 Agent thinking:', assistantMessage.substring(0, 200) + '...');

      // Parse the response
      try {
        const parsed = JSON.parse(assistantMessage);
        
        // Check if it's a tool call
        if (parsed.tool && tools[parsed.tool]) {
          console.log(`🔧 Using tool: ${parsed.tool}`);
          const tool = tools[parsed.tool];
          const result = await tool.execute(parsed.params);
          console.log(`✅ Tool result: ${result.substring(0, 200)}...`);
          
          // Add assistant's message and tool result to the conversation
          messages.push({
            role: 'assistant',
            content: assistantMessage
          });
          messages.push({
            role: 'user',
            content: `Tool result: ${result}`
          });
        } else if (parsed.final_answer) {
          finalAnswer = parsed.final_answer;
          console.log(`✅ Final answer: ${finalAnswer}`);
        } else {
          // If the response is not a tool call, treat it as a response
          messages.push({
            role: 'assistant',
            content: assistantMessage
          });
        }
      } catch (parseError) {
        // If it's not JSON, treat it as a normal response
        messages.push({
          role: 'assistant',
          content: assistantMessage
        });
      }

    } catch (error) {
      console.error('Error in agent loop:', error);
      break;
    }
  }

  if (!finalAnswer) {
    finalAnswer = 'Agent reached maximum steps without completing the task.';
  }

  return finalAnswer;
}

// Main execution
async function main() {
  if (!OPENROUTER_API_KEY) {
    console.error('Error: OPENROUTER_API_KEY environment variable is required');
    process.exit(1);
  }

  // Get the goal from environment or use a default
  const goal = process.env.AGENT_GOAL || 'Research the latest developments in AI and provide a 3-point summary.';
  
  console.log('🚀 Starting OpenRouter Agent');
  console.log('📋 Goal:', goal);
  console.log('🌐 Model:', MODEL);
  
  try {
    const result = await runAgent(goal);
    console.log('\n📊 FINAL RESULT:');
    console.log('========================================');
    console.log(result);
    console.log('========================================');
  } catch (error) {
    console.error('Agent execution failed:', error);
    process.exit(1);
  }
}

main();
