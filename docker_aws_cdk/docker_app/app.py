import streamlit as st
import jwt  # For decoding JWT
import boto3  # For SNS
import dotenv  # For environment variables
import os  # For environment variables

dotenv.load_dotenv()

# Get the headers
headers = st.context.headers

auth_header = headers.get("X-Amzn-Oidc-Data", "")
if not auth_header:
    st.error("JWT not found")
token = None

if auth_header:
    token = auth_header
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        email = decoded_token.get("email", "")
        st.write(f"## User email: {email}")
    except Exception as e:
        st.error(f"Error decoding JWT: {e}")
else:
    st.error("No Authorization header found")


# Prompt for subject and message
st.write("## Send a Message")

# Show topic ARN
sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")

if sns_topic_arn:
    print(f"SNS_TOPIC_ARN: {sns_topic_arn}")
else:
    st.error("SNS_TOPIC_ARN environment variable not set.")

subject = st.text_input("Subject", value="Hello from Streamlit!")
message = st.text_area("Message", value="Hello, world!")

if st.button("Submit"):
    # Send the message with the subject to the SNS topic
    if not sns_topic_arn:
        st.error("SNS_TOPIC_ARN environment variable not set.")
    else:
        # Initialize SNS client
        sns = boto3.client("sns")
        try:
            response = sns.publish(
                TopicArn=sns_topic_arn, Message=message, Subject=subject
            )
            st.success(f"Message sent! Message ID: {response['MessageId']}")
        except Exception as e:
            st.error(f"Error sending message: {e}")

# Logout link
st.markdown('<a href="/logout" target="_self">Sign Out</a>', unsafe_allow_html=True)
