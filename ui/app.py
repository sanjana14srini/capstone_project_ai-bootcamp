import streamlit as st
import json
import requests



st.set_page_config(page_title="Chat Frontend", layout="wide")

st.title("🔧 arXiv Reserach Agent")


# ---- Replace this with your own backend call ---- #
def send_to_backend(messages):
    resp = requests.post(
        "http://localhost:8001/chat",
        json={"messages": messages},
        stream=True,
    )


    for line in resp.iter_lines(chunk_size=1, decode_unicode=True):
        if not line or line.strip() == "":
            continue  # skip empty lines

        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            # optionally log the invalid line
            print("Skipping invalid line:", line)
            continue


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display existing conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "tool_call" in msg:
            st.code(json.dumps(msg["tool_call"], indent=2))


# User input box
user_input = st.chat_input("Say something...")

if user_input:
    # Add user message
    
    st.session_state.messages.append({"role": "user", "content": user_input, "latest_query": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Stream assistant reply
    with st.chat_message("assistant"):
        text_box = st.empty()
        tool_box = st.empty()
        
        streamed_text = ""
        streamed_tool_calls = []
        
        
        # Call your backend agent
        for event in send_to_backend(st.session_state.messages):

            # Stream tokens or final_result
            if event["type"] == "token" or event["type"] == "final_result":
                streamed_text += event["content"]
                text_box.markdown(streamed_text)

            # Stream tool calls
            elif event["type"] == "tool_call":
                streamed_tool_calls.append(event)
                tool_box.code(json.dumps(streamed_tool_calls, indent=2))


        # store the assistant msg (saving final state)
        msg_record = {
            "role": "assistant",
            "content": streamed_text,
            "latest_query": user_input
        }
        if streamed_tool_calls:
            msg_record["tool_call"] = streamed_tool_calls

        st.session_state.messages.append(msg_record)
