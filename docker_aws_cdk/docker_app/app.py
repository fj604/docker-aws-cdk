import streamlit as st
from langchain_aws.chat_models import ChatBedrockConverse
from langchain.schema import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# Set the page title and icon
st.set_page_config(page_title="🦜🔗 Chatbot App", page_icon="🤖")

# Sidebar for model selection
model_options = {
    "Anthropic: Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "Anthropic: Claude 3 Haiku": "anthropic.claude-3-haiku-20240307-v1:0"
}
selected_model = st.sidebar.selectbox("Select Model", options=list(model_options.keys()), index=0)
model_id = model_options[selected_model]

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to generate and display AI response
def generate_response(prompt):
    model = ChatBedrockConverse(model_id=model_id)

    # Prepare the input history to maintain context
    conversation_history = [
        HumanMessage(content=msg["content"]) if msg["role"] == "user" else
        AIMessage(content=msg["content"])
        for msg in st.session_state.messages
    ]

    # Add the current prompt to the conversation history
    conversation_history.append(HumanMessage(content=prompt))

    # Create the chain with StrOutputParser for streaming
    chain = model | StrOutputParser()

    # Create a placeholder for the assistant's response
    assistant_message_placeholder = st.chat_message("assistant")
    response_placeholder = assistant_message_placeholder.markdown("...")

    # Loop through chunks and update the placeholder
    response = ""
    for chunk in chain.stream(conversation_history):
        if isinstance(chunk, str):
            response += chunk
            response_placeholder.markdown(response + "▌")
        else:
            st.warning("Received unexpected chunk format. Please check model output.")

    # Finalize the message
    response_placeholder.markdown(response)
    return response

# Input field for user message
if prompt := st.chat_input("Enter your message here..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    # Append user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Generate AI response
    response = generate_response(prompt)
    # Append AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})