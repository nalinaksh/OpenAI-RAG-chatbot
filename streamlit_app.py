import streamlit as st
import openai
from openai import OpenAI
import time

# Set OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key = openai.api_key)

@st.cache_data
def init():
    assistant = client.beta.assistants.create(
        instructions="You are a helpful assistant. Answer the queries based upon knowledge retrieve from the attached files only. Keep the answers as concise as possible",
        name="Helpful Assistant",
        #model="gpt-3.5-turbo",
        model="gpt-3.5-turbo-1106",
        tools=[{"type": "retrieval"}]
    )
    
    #file to be attached to the assistant
    file = client.files.create(
        file=open("memgpt.pdf", "rb"),
        purpose='assistants'
    )
    #attaching the file to assistant
    assistant_file = client.beta.assistants.files.create(
    assistant_id=assistant.id, 
    file_id=file.id
    )
    #create a persistent thread
    thread = client.beta.threads.create()
    return (assistant.id, thread.id)
    
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Clear chat messages
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

assistant_id, thread_id = init()

# React to user input
if prompt := st.chat_input("How are you?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    assistant_response=""
    placeholder = st.empty()

    #Post user message to the thread
    thread_message = client.beta.threads.messages.create(
      thread_id,
      role="user",
      content=prompt,
    )
    
    #ask assistant to process the thread messages to generate and append the new response back to the thread 
    run = client.beta.threads.runs.create(
      thread_id=thread_id,
      assistant_id=assistant_id
    )
    
    #poll run status every 1 sec to find out if the request has been completed or not
    status = "in_progress"
    while status == "in_progress":
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        status = run.status
        
    #retrieve all thread messages and fetch the newly generate response by the assistant
    thread_messages = client.beta.threads.messages.list(thread_id)
    message = thread_messages.data[0]
    assistant_response += message.content[0].text.value
    placeholder.chat_message("assistant").markdown(assistant_response, unsafe_allow_html=True)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
