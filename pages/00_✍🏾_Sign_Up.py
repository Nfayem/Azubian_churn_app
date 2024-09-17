# Standard library imports
import yaml
import time
import base64

# Third-party imports
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import RegisterError

# Local application imports
from utils.lottie import display_lottie_on_page


# Set up the page configuration
st.set_page_config(
    page_title="Sign Up",
    page_icon="assets/app_icon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Loading config file
with open('./config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)


# Set up general page elements
st.logo("assets/team_logo.svg")
st.image("assets/team_logo.svg", width=200)
st.sidebar.text("Powered by Team Switzerland 💡🌍")


# Page introduction
st.write("---")
st.title("✍🏾 Create a New Account")
left_column, right_column = st.columns(2)
with left_column:
    st.write("""
    Welcome to the Churn Predictor App registration page! Please fill out the form below to create a new account. 
    Once registered, you will be able to log in and use the app.

    Ensure that you provide valid credentials for your account. After successful registration, you will be directed to the Welcome page where you can proceed to log in.
    """)
with right_column:
    display_lottie_on_page("Sign_Up")


# Creating a new user registration widget
try:
    email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(pre_authorization=False, fields={'Form name': 'Sign Up Here', 'Register': 'Sign Up'})
    if email_of_registered_user:
        # Create a placeholder for the success message
        success_placeholder = st.empty()
        success_placeholder.success('The new user has been successfully registered.')
        
        # Clear the success message after a delay
        time.sleep(3)  # Wait for 3 seconds
        success_placeholder.empty()
        
        st.write("""
        Your account has been created successfully. You can now proceed to login. 
        Click [here](http://localhost:8501) to go to the Gateway page.
        """)
except RegisterError as e:
    st.error(f"Registration Error: {e}")

# Save the updated configuration file
with open('./config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)


# Function to convert an image to base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Image paths
image_paths = ["./assets/favicon.png"]

# Convert images to base64
image_b64 = [image_to_base64(img) for img in image_paths]

# Need Help Section
st.markdown("Need help? Contact support at [sdi@azubiafrica.org](mailto:sdi@azubiafrica.org)")

st.write("---")

# Contact Information Section
st.markdown(
f"""
<div style="display: flex; justify-content: space-between; align-items: center;">
    <div style="flex: 1;">
        <h2>Contact Us</h2>
        <p>For inquiries, please reach out to us:</p>
        <p>📍 Address: Accra, Ghana</p>
        <p>📞 Phone: +233 123 456 789</p>
        <p>📧 Email: sdi@azubiafrica.org</p>
    </div>
    <div style="flex: 0 0 auto;">
        <img src="data:image/png;base64,{image_b64[0]}" style="width:100%";" />
    </div>
</div>
""",
unsafe_allow_html=True
)
