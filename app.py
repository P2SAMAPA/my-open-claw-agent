import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(page_title="OpenClaw Agent Chat", page_icon="🤖")
st.title("🤖 OpenClaw Agent Chat")

# Sidebar for settings
with st.sidebar:
    st.header("Configuration")
    # Model selection only - no API key input
    model = st.selectbox(
        "Model", 
        ["openrouter/free", "openai/gpt-4o-mini", "anthropic/claude-3-haiku", "nvidia/nemotron-3-ultra:free"], 
        index=0
    )
    
    # Show current model info
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This agent can search the web, execute commands, and more!")
    st.markdown("💡 Your API key is securely stored in the cloud.")
    
    # Optional: Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like the agent to do?"):
    # Get API key from secrets
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        st.error("❌ OpenRouter API key not found. Please add it to your Streamlit secrets.")
        st.stop()
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call OpenRouter API
    with st.chat_message("assistant"):
        with st.spinner("🧠 Agent is thinking..."):
            try:
                # Prepare the API request
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://your-app-url.streamlit.app",  # Replace with your actual Streamlit URL
                    "X-Title": "OpenClaw Agent"
                }
                
                # Convert messages to the format OpenRouter expects
                api_messages = []
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})
                
                # Add a system prompt to guide the agent
                system_prompt = """You are OpenClaw, a helpful AI agent that can perform tasks.
                You have access to tools like:
                - Web search: Search for current information
                - Shell commands: Execute terminal commands
                - Web fetch: Retrieve content from websites
                
                When you need to use a tool, respond with a JSON object containing the tool name and parameters.
                If you don't need a tool, just respond normally.
                """
                
                api_messages.insert(0, {"role": "system", "content": system_prompt})
                
                # Make the API call
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": api_messages,
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "tools": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "search_web",
                                    "description": "Search the web for current information",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string", 
                                                "description": "The search query to look up"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                }
                            },
                            {
                                "type": "function",
                                "function": {
                                    "name": "execute_command",
                                    "description": "Execute a shell command",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "command": {
                                                "type": "string", 
                                                "description": "The shell command to execute"
                                            }
                                        },
                                        "required": ["command"]
                                    }
                                }
                            }
                        ],
                        "tool_choice": "auto"
                    },
                    timeout=60
                )
                
                # Check if the request was successful
                response.raise_for_status()
                result = response.json()
                
                # Extract and display the assistant's response
                if "choices" in result and len(result["choices"]) > 0:
                    assistant_message = result["choices"][0]["message"]["content"]
                    
                    # Check if the response contains a tool call
                    if "tool_calls" in result["choices"][0]["message"]:
                        st.info("🔧 The agent is using a tool. Check the response for details.")
                    
                    st.markdown(assistant_message)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": assistant_message
                    })
                else:
                    st.error("No response received from the model.")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"🌐 Network error: {str(e)}")
                st.info("Please check your internet connection and try again.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("If this persists, try selecting a different model.")
