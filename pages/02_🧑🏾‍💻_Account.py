# Standard library imports
import yaml
import time
import base64

# Third-party imports
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import (
    ForgotError,
    RegisterError,
    ResetError,
    UpdateError
)

# Local application imports
from utils.login import invoke_login_widget
from utils.lottie import display_lottie_on_page


# Invoke the login form
invoke_login_widget('Account')

# Fetch the authenticator from session state
authenticator = st.session_state.get('authenticator')

# Ensure the authenticator is available
if not authenticator:
    st.error("Authenticator not found. Please check the configuration.")
    st.stop()

# Check authentication status
if st.session_state.get("authentication_status"):

    # Page introduction
    st.title("User Account Management")
    st.write("---")
    left_column, right_column = st.columns(2)
    with left_column:
        st.write("""Welcome to the User Account Management page. 
                 Here you can manage your personal account settings and sign up a new user as well.
                 """)
    with right_column:
        display_lottie_on_page("Account")  
    
    # Load configuration from YAML file
    try:
        with open('./config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("Configuration file not found.")
        st.stop()
    except yaml.YAMLError as e:
        st.error(f"Error loading YAML file: {e}")
        st.stop()

    # Create authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )

    # Handle password reset
    if st.session_state.get("authentication_status"):
        st.subheader("Reset Password")
        st.write("To reset your password, enter your current password and your new password below. Ensure that your new password is strong and secure.")
        try:
            if authenticator.reset_password(st.session_state["username"]):
                # Create a placeholder for the success message
                success_placeholder = st.empty()
                success_placeholder.success('Your password has been successfully updated.')
                # Clear the success message after a delay
                time.sleep(3)
                success_placeholder.empty()
        except ResetError as e:
            st.error(f"Error resetting password: {e}")
            time.sleep(3)
            st.empty()

    # Handle forgot password
    st.subheader("Forgot Password")
    st.write("If you've forgotten your password, enter your username here to request a new password. Instructions will be sent to your email address.")
    try:
        (username_of_forgotten_password, email_of_forgotten_password, new_random_password) = authenticator.forgot_password()
        if username_of_forgotten_password:
            # Create a placeholder for the success message
            success_placeholder = st.empty()
            success_placeholder.success('A new password has been sent to your email address.')
            # Clear the success message after a delay
            time.sleep(3)
            success_placeholder.empty()
        elif username_of_forgotten_password is None:
            st.warning('Please enter your username.')
        else:
            st.error('The provided username was not found.')
            time.sleep(3)
            st.empty()
    except ForgotError as e:
        st.error(f"Error with forgot password: {e}")
        time.sleep(3)
        st.empty()

    # Handle forgot username
    st.subheader("Forgot Username")
    st.write("If you’ve forgotten your username, enter your email address here. You will receive instructions to retrieve your username via email.")
    try:
        (username_of_forgotten_username, email_of_forgotten_username) = authenticator.forgot_username()
        if username_of_forgotten_username:
            # Create a placeholder for the success message
            success_placeholder = st.empty()
            success_placeholder.success('Your username has been sent to your email address.')
            # Clear the success message after a delay
            time.sleep(3)
            success_placeholder.empty()
        elif username_of_forgotten_username is None:
            st.warning('Please enter your email address to retrieve your username.')
        else:
            st.error('The provided email address was not found.')
            time.sleep(3)
            st.empty()
    except ForgotError as e:
        st.error(f"Error with forgot username: {e}")
        time.sleep(3)
        st.empty()

    # Handle update user details
    if st.session_state.get("authentication_status"):
        st.subheader("Update User Details")
        st.write("Use this section to update your personal details like name and email. Make sure to save your changes after updating.")
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                # Create a placeholder for the success message
                success_placeholder = st.empty()
                success_placeholder.success('Your details have been successfully updated.')
                # Clear the success message after a delay
                time.sleep(3)
                success_placeholder.empty()
        except UpdateError as e:
            st.error(f"Error updating details: {e}")
            time.sleep(3)
            st.empty()

    # Handle user registration
    st.subheader("Sign Up Here")
    st.write("To create a new user account, provide the email, username, and name for the new user.")
    try:
        (email_of_registered_user, username_of_registered_user, name_of_registered_user) = authenticator.register_user(
            key='Sign Up',
            pre_authorization=False,
            fields={'Form name': 'Sign Up Here', 'Register': 'Sign Up'}
        )
        if email_of_registered_user:
            # Create a placeholder for the success message
            success_placeholder = st.empty()
            success_placeholder.success('The new user has been successfully registered.')
            # Clear the success message after a delay
            time.sleep(3)
            success_placeholder.empty()
    except RegisterError as e:
        st.error(f"Error registering user: {e}")
        time.sleep(3)
        st.empty()

    # Save the updated configuration file
    with open('./config.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(config, file, default_flow_style=False)

else:
    st.warning("Please log in to manage your account.")


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
            <img src="data:image/png;base64,{image_b64[0]}" style="width:100%;" />
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
