# Streamlit Chat App Examples and Resources

[Created by Claude: 0406893a-d1f8-4f12-99dc-11ede8c39975]

## Official Streamlit Resources

### Official Tutorial
- **Build a basic LLM chat app**: https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps
- **Chat elements API reference**: https://docs.streamlit.io/develop/api-reference/chat

### Official Example Repository
- **Streamlit LLM Examples**: https://github.com/streamlit/llm-examples/blob/main/Chatbot.py

## Key Chat Components

### 1. `st.chat_message()`
- Inserts a chat message container into the app
- Displays messages from the user or assistant
- Can contain other Streamlit elements (charts, tables, text, etc.)
- Provides preset styling and avatars for "user" and "assistant" roles

### 2. `st.chat_input()`
- Displays a chat input widget
- Positioned at the bottom of the interface
- Allows users to type and submit messages

### 3. `st.session_state`
- Persists chat history across app reruns
- Stores messages as a list of dictionaries with `role` and `content` keys

## Basic Echo Bot Example

```python
import streamlit as st

st.title("Echo Bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display assistant response
    response = f"Echo: {prompt}"
    with st.chat_message("assistant"):
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
```

## OpenAI-Powered Chatbot (Official Example)

```python
from openai import OpenAI
import streamlit as st

# Sidebar for API key
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

# Initialize chat history with welcome message
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Handle user input
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Get and display assistant response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
```

## Streaming Response Example

For a typewriter effect with animated responses:

```python
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ... (initialize session state and display previous messages)

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
```

## GitHub Repositories & Examples

### Official
1. **streamlit/llm-examples** - https://github.com/streamlit/llm-examples/blob/main/Chatbot.py
   - Official examples from Streamlit team
   - OpenAI chatbot implementation
   - Clean, well-documented code

### Community Projects

2. **AI-Yash/st-chat** - https://github.com/AI-Yash/st-chat
   - Streamlit Component for a Chatbot UI
   - Custom chat interface component

3. **fshnkarimi/Chat-Bot-using-Streamlit-and-OpenAI** - https://github.com/fshnkarimi/Chat-Bot-using-Streamlit-and-OpenAI
   - User-friendly chatbot with GPT-3.5
   - Good for beginners

4. **nishijima13/StreamlitChatAppDemo** - https://github.com/nishijima13/StreamlitChatAppDemo
   - Chat between users
   - ChatGPT character personalities
   - Advanced features

5. **ilhansevval/Gemini-Chatbot-Interface-with-Streamlit** - https://github.com/ilhansevval/Gemini-Chatbot-Interface-with-Streamlit
   - Gemini AI integration
   - Chat history persistence
   - Continue previous conversations

6. **billyotieno/streamlit-chat** - https://github.com/billyotieno/streamlit-chat
   - ChatGPT-powered
   - User-friendly interface

7. **whitphx/streamlit-video-chat-example** - https://github.com/whitphx/streamlit-video-chat-example
   - Video chat with computer vision filters
   - Advanced real-time features

### GitHub Topic Pages
- **streamlit-chat**: https://github.com/topics/streamlit-chat
- **streamlit-chatbot**: https://github.com/topics/streamlit-chatbot
- **streamlit-application**: https://github.com/topics/streamlit-application

## Key Patterns & Best Practices

### Session State Management
```python
# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []

# Append messages
st.session_state.messages.append({
    "role": "user",  # or "assistant"
    "content": "message text"
})
```

### Message Structure
```python
{
    "role": "user",      # "user" or "assistant"
    "content": "text"    # message content
}
```

### Display Pattern
```python
# Display all messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
```

### Input Handling Pattern
```python
if prompt := st.chat_input("Your placeholder"):
    # 1. Add to session state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Generate response
    response = generate_response(prompt)

    # 4. Display assistant message
    with st.chat_message("assistant"):
        st.markdown(response)

    # 5. Add response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
```

## Additional Tutorials

1. **TypeThePipe** - "New Streamlit Chat. Conversational app with st.chat_message and st.chat_input"
   - https://typethepipe.com/post/streamlit-chat-conversational-app-st-chat_message/

2. **DEV Community** - "Streamlit Part 7: Build a Chat Interface"
   - https://dev.to/jamesbmour/streamlit-part-7-build-a-chat-interface-51mo

3. **PythonAndVBA** - "Create a ChatGPT Clone with Streamlit in Under 50 Lines"
   - https://pythonandvba.com/blog/streamlit-chat-feature/

4. **Medium** - "Chat Application using Streamlit and Text Bison"
   - https://bijukunjummen.medium.com/chat-application-using-streamlit-and-text-bison-05024f939827

## Advanced Features

### Chat History Persistence
- Store conversations in databases
- Save/load chat sessions
- Export conversations

### Multi-model Support
- OpenAI GPT models
- Google Gemini
- Anthropic Claude
- Local LLMs (LLaMA, etc.)
- HuggingFace models

### Enhanced UI
- Custom avatars
- Message timestamps
- Typing indicators
- Message editing
- File uploads in chat
- Code syntax highlighting

### Integration Options
- LangChain for complex workflows
- Vector databases for RAG
- PDF/document chat
- Web search integration
- Custom function calling

---

[Created by Claude: 0406893a-d1f8-4f12-99dc-11ede8c39975]
