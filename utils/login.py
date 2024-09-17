import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import LoginError

def load_config(config_path: str):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except FileNotFoundError:
        st.error("Configuration file not found.")
        st.stop()
    except yaml.YAMLError as e:
        st.error(f"Error loading YAML file: {e}")
        st.stop()

def initialize_authenticator(config):
    if 'authenticator' not in st.session_state:
        st.session_state['authenticator'] = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['pre-authorized'],
            False
        )
    return st.session_state['authenticator']

def invoke_login_widget(page_title):
    # Load the configuration and initialize the authenticator
    config = load_config('./config.yaml')
    authenticator = initialize_authenticator(config)

    # Display the login form if the user is not authenticated
    if not st.session_state.get("authentication_status"):
        st.title("🔐 Login")
        try:
            authenticator.login('sidebar', 'Login')
        except LoginError as e:
            st.error(e)
    
    # Handle authentication status with custom messages based on the page title
    if st.session_state.get("authentication_status"):
        if page_title == "Home":
            st.sidebar.success("How can we assist you?👋🏾🙂")
        elif page_title == "Account":
            st.sidebar.success("Manage your account settings.🔧🔒")
        elif page_title == "Data Overview":
            st.sidebar.success("Data ready for naviagation 🧑🏾‍💻👍🏾")
        elif page_title == "Analytics Dashboard":
            st.sidebar.success("Explore the latest insights.🔎📶")
        elif page_title == "History Overview":
            st.sidebar.success("Delve into past prediction trends.⏳☎️")
        elif page_title == "Future Projections":
            st.sidebar.success("Let's predict the future together!🔭🤞🏾")
        else:
            st.sidebar.success("You're successfully logged in!")
    elif st.session_state.get("authentication_status") is False:
        st.error('Username/password is incorrect.')
    elif st.session_state.get("authentication_status") is None:
        st.warning('Please enter your username and password.')


