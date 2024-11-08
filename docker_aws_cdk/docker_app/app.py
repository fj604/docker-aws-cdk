import jwt
import os
import boto3
import streamlit as st
from langchain_aws.chat_models import ChatBedrockConverse
from langchain.schema import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import json

def get_jwt_token():
    headers = getattr(st.context, 'headers', {})
    auth_header = headers.get("X-Amzn-Oidc-Data", "")
    if auth_header:
        try:
            return jwt.decode(auth_header, options={"verify_signature": False})
        except Exception as e:
            print(f"Error decoding JWT: {e}")
    else:
        print("No Authorization header found")
    return None

def send_sns_message(message, subject):
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if not sns_topic_arn:
        raise ValueError("SNS_TOPIC_ARN environment variable not set.")
    sns = boto3.client("sns")
    try:
        response = sns.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)
        return response['MessageId']
    except Exception as e:
        raise ValueError(f"Error sending message: {e}")

def send_message_history(token):
    if "messages" in st.session_state:
        message_history = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
        message_id = send_sns_message(json.dumps(message_history), subject=token.get("email"))
        st.info(f"Message sent with ID: {message_id}")

st.set_page_config(page_title="🦜🔗 Chatbot App", page_icon="🤖")

model_options = {
    "Anthropic: Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "Anthropic: Claude 3 Haiku": "anthropic.claude-3-haiku-20240307-v1:0"
}

token = get_jwt_token()
st.sidebar.header(token.get("email", "Not authenticated") if token else "Not authenticated")
selected_model = st.sidebar.selectbox("Select Model", options=list(model_options.keys()), index=0)
model_id = model_options[selected_model]

if "messages" not in st.session_state:
    st.session_state.messages = []

memory = ConversationBufferMemory()

if token and os.environ.get("SNS_TOPIC_ARN") and st.sidebar.button("Send Message History"):
    send_message_history(token)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def generate_response(prompt):
    model = ChatBedrockConverse(model_id=model_id)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            memory.add_message(HumanMessage(content=msg["content"]))
        else:
            memory.add_message(AIMessage(content=msg["content"]))
    
    chain = ConversationChain(llm=model, memory=memory, output_parser=StrOutputParser())
    assistant_message_placeholder = st.chat_message("assistant")
    response_placeholder = assistant_message_placeholder.markdown("...")
    response = ""

    for chunk in chain.stream(prompt):
        if isinstance(chunk, str):
            response += chunk
            response_placeholder.markdown(response + "▌")
        else:
            st.warning("Received unexpected chunk format. Please check model output.")

    response_placeholder.markdown(response)
    return response

if prompt := st.chat_input("Enter your message here..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})