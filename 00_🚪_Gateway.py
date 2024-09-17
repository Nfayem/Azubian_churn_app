# Standard library imports
import yaml
import base64

# Third-party imports
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
from PIL import Image
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import LoginError

# Local application imports
from utils.lottie import display_lottie_on_page


# Set up the page configuration
st.set_page_config(
    page_title="Churn Predictor",
    page_icon="assets/app_icon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up general page elements
st.logo("assets/team_logo.svg")
st.image("assets/team_logo.svg", width=200)

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

# Creating the authenticator object and storing it in session state
if 'authenticator' not in st.session_state:
    st.session_state['authenticator'] = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized']
    )

authenticator = st.session_state['authenticator']

# Login page content
if not st.session_state.get("authentication_status"):
    st.write("---")
    st.title("🔐 Welcome to the Login Page")
    left_column, right_column = st.columns(2)
    with left_column:
        st.header("Secure Login")
        st.write(
            """
            Please enter your credentials to access your account.
            Your information is safe with us, and we ensure top-notch security.
            """
        )
        st.subheader("About the Churn Predictor App")
        st.write(
            """
            The Churn Predictor app is designed to analyze customer data and predict churn risk. 
            It helps businesses identify customers who are likely to leave and take proactive measures to retain them.
            """
        )
    with right_column:
        display_lottie_on_page("Login")

try:
    authenticator.login()
except LoginError as e:
    st.error(e)

# Check authentication status
if st.session_state.get("authentication_status"):
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f'Welcome *{st.session_state["name"]}*')

    home_page = st.Page(
        page="pages/01_🏡_Home.py",
        title="Home",
        icon="🏡",
        default=True
    )

    account_page = st.Page(
        page="pages/02_🧑🏾‍💻_Account.py",
        title="Account",
        icon="🧑🏾‍💻"
    )

    data_page = st.Page(
        page="pages/03_📊_Data.py",
        title="Data Overview",
        icon="📊"
    )

    dashboard_page = st.Page(
        page="pages/04_📈_Dashboard.py",
        title="Analytics Dashboard",
        icon="📈"
    )

    history_page = st.Page(
        page="pages/05_🕰️_History.py",
        title="Historical Insights",
        icon="🕰️"
    )

    prediction_page = st.Page(
        page="pages/06_🔮_Prediction.py",
        title="Future Projections",
        icon="🔮"
    )

    # Run authenticated pages
    pg = st.navigation(
        {
            "User Interaction": [home_page, account_page],
            "Data Management": [data_page, dashboard_page],
            "Insights and Forecasting": [history_page, prediction_page],
        }
    )

    pg.run()

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect.')

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

elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password.')

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

# Set up general page elements
st.sidebar.text("Powered by Team Switzerland 💡🌍")