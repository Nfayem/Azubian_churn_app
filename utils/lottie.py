import requests
import streamlit as st
from streamlit_lottie import st_lottie

# Cache the Lottie animation data with persistence across sessions
@st.cache_data(show_spinner=False, persist=True)
def load_lottie_animation(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load Lottie animation: {e}")
        return None

# Example of how to use this in a page
def display_lottie_on_page(page_name):
    lottie_urls = {
        "Sign_Up": "https://lottie.host/0fd6e98b-0ace-4f1e-a801-d86331f4cc5d/f4yuXA2ioF.json",
        "Login": "https://lottie.host/eae02fe9-b668-45dd-a630-f37bf69aa5cb/SHJKStoKhR.json",
        "Home": "https://lottie.host/f3734960-8bd5-4e1e-94c7-57787a497ac7/dXSGaeZhUf.json",
        "Account": "https://lottie.host/7be714de-5b8b-499a-ac6b-80363094675a/JSmWux7ypN.json",
        "Data Overview": "https://assets5.lottiefiles.com/private_files/lf30_5ttqPi.json",
        "Analytics Dashboard": "https://assets1.lottiefiles.com/packages/lf20_o6spyjnc.json",
        "History Overview": "https://lottie.host/f2dd5f4d-a43e-4836-b6b3-a3aac326018d/C1DlvH4nQ4.json",
        "Future Projections": "https://lottie.host/f52a4606-dba8-41e5-8fdc-6cc6552034c4/N8AlKsvPww.json"        
    }

    if page_name in lottie_urls:
        animation_data = load_lottie_animation(lottie_urls[page_name])
        if animation_data:
            st_lottie(animation_data, height=300, key=page_name)
    else:
        st.error("No Lottie animation available for this page.")
