import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(page_title="OpenClaw Agent Chat", page_icon="🤖")
st.title("🤖 OpenClaw Agent Chat")

# Sidebar for settings
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenRouter API Key", type="password", 
                            help="Get your key from openrouter.ai/keys")
    model = st.selectbox("Model", ["openrouter/free", "openai/gpt-4o-mini", "anthropic/claude-3-haiku"], 
                         index=0)
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This agent can search the web, execute commands, and more!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like the agent to do?"):
    if not api_key:
        st.error("Please enter your OpenRouter API key in the sidebar.")
        st.stop()
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call OpenRouter API
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://your-app-url.streamlit.app",  # Replace with your actual URL
                        "X-Title": "OpenClaw Agent"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": m["role"], "content": m["content"]} 
                                     for m in st.session_state.messages],
                        "tools": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "search_web",
                                    "description": "Search the web for information",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string", "description": "Search query"}
                                        },
                                        "required": ["query"]
                                    }
                                }
                            }
                        ],
                        "tool_choice": "auto"
                    },
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                assistant_message = result["choices"][0]["message"]["content"]
                st.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            except Exception as e:
                st.error(f"Error: {str(e)}")
