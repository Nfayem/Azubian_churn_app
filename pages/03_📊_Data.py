# Standard library imports
import base64
import os
import sqlite3
import time
from io import BytesIO

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
from sklearn.impute import SimpleImputer

# Local application imports
from utils.login import invoke_login_widget
from utils.lottie import display_lottie_on_page


# Invoke the login form
invoke_login_widget('Data Overview')

# Fetch the authenticator from session state
authenticator = st.session_state.get('authenticator')

# Ensure the authenticator is available
if not authenticator:
    st.error("Authenticator not found. Please check the configuration.")
    st.stop()

# Check authentication status
if st.session_state.get("authentication_status"):
    username = st.session_state['username']
    st.title("Data Navigator")
    st.write("---")

    # Page Introdution
    with st.container():        
        left_column, right_column = st.columns(2)
        with left_column:
            st.write(
                """
                The Data Navigator page allows you to upload, view, and analyze datasets. 
                Start by exploring a template dataset or uploading yours. Detailed column descriptions 
                are provided to help you understand the structure and content required for your dataset. 
                Additionally, you can interactively filter the data and review a summary of the displayed dataset.
                Download options are provided in Excel, Stata, HTML, and JSON formats for professional data handling and analysis.
                """
            )
        with right_column:
            display_lottie_on_page("Data Overview")

    # Load the initial data from a local file
    @st.cache_data(persist=True, show_spinner=False)
    def load_initial_data():
        df = pd.read_csv('./data/CAP_template.csv')
        return df
    
    initial_df = load_initial_data()
    
    # Sidebar for file upload (CSV or Excel)
    st.sidebar.header("Data Upload")
    uploaded_file = st.sidebar.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])

    # Load the uploaded file (either CSV or Excel)
    @st.cache_data(persist=True, show_spinner=False)
    def load_uploaded_data(file):
        if file is not None:
            try:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    df = pd.read_excel(file)
                return df
            except Exception as e:
                st.error(f"Error: {e}")
                return None
        return None
    
    # Function to check if the uploaded data structure matches the template structure
    def validate_data_structure(uploaded_df, template_df):
        # Define the function to map data types to categories and numbers
        def standardize_dtypes(df):
            dtype_mapping = {
                'object': 'Categorical',
                'category': 'Categorical',
                'int64': 'Numerical',
                'float64': 'Numerical'
            }
            return df.dtypes.map(lambda x: dtype_mapping.get(str(x), x)).tolist()
        
        # Compare column names
        if list(uploaded_df.columns) != list(template_df.columns):
            return False
        
        # Compare data types
        if standardize_dtypes(uploaded_df) != standardize_dtypes(template_df):
            st.write(uploaded_df.dtypes.tolist())
            return False
        
        return True

    
    # Function to save the uploaded file as a SQLite database
    def save_uploaded_file_as_sqlite(file, username):
        # Ensure the directory exists
        save_dir = f"./data/{username}"
        os.makedirs(save_dir, exist_ok=True)

        # Define the path for the user's SQLite database
        db_path = os.path.join(save_dir, f"{username}.db")

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Get existing tables and determine the next table number
        existing_tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        existing_tables = [table[0] for table in conn.execute(existing_tables_query).fetchall()]
        
        # Filter tables to find those that match the user's naming pattern
        user_tables = [table for table in existing_tables if table.startswith(f"{username}_table")]

        if user_tables:
            # Extract the numeric part, convert to integer, and find the max value
            max_table_num = max([int(table.split(f"{username}_table")[1]) for table in user_tables])
            next_table_num = max_table_num + 1
        else:
            next_table_num = 1

        # Pad the table number with leading zeros based on the length of the highest table number
        pad_length = len(str(next_table_num))
        table_name = f"{username}_table{str(next_table_num).zfill(pad_length)}"

        # Save the DataFrame to the new table in the SQLite database
        try:
            file.seek(0)  
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file)

            if df is None or df.empty:
                st.error("The uploaded file is empty or improperly formatted. Please upload a valid file.")
                return None, None, None

            # Check if the uploaded data structure matches the template structure
            if not validate_data_structure(df, initial_df):
                st.error("""The structure of the uploaded file does not align with the expected template. 
                         Please review the column descriptions provided below to ensure that the column 
                         names and data types conform to the required specifications.
                         """)
                return None, None, None

            df.to_sql(table_name, conn, index=False, if_exists='replace')

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return None, None, None
        finally:
            conn.close()

        return df, table_name, db_path
    
    # Function to generate download buttons for the original data in multiple formats
    def generate_download_buttons_original(df):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Download as Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(
                label="Download as Excel",
                data=excel_buffer.getvalue(),
                file_name="data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="original_excel"
            )

        with col2:
            # Download as Stata
            stata_buffer = BytesIO()
            df.to_stata(stata_buffer, write_index=False)
            st.download_button(
                label="Download as Stata",
                data=stata_buffer.getvalue(),
                file_name="data.dta",
                mime="application/x-stata",
                key="original_stata"
            )

        with col3:
            # Download as HTML
            html = df.to_html(index=False).encode('utf-8')
            st.download_button(
                label="Download as HTML",
                data=html,
                file_name="data.html",
                mime="text/html",
                key="original_html"
            )

        with col4:
            # Download as JSON
            json = df.to_json(orient="records").encode('utf-8')
            st.download_button(
                label="Download as JSON",
                data=json,
                file_name="data.json",
                mime="application/json",
                key="original_json"
            )

    # Function to generate download buttons for the filtered data in multiple formats
    def generate_download_buttons_filtered(df):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Download as Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button(
                label="Download as Excel",
                data=excel_buffer.getvalue(),
                file_name="data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="filtered_excel"
            )

        with col2:
            # Download as Stata
            stata_buffer = BytesIO()
            df.to_stata(stata_buffer, write_index=False)
            st.download_button(
                label="Download as Stata",
                data=stata_buffer.getvalue(),
                file_name="data.dta",
                mime="application/x-stata",
                key="filtered_stata"
            )

        with col3:
            # Download as HTML
            html = df.to_html(index=False).encode('utf-8')
            st.download_button(
                label="Download as HTML",
                data=html,
                file_name="data.html",
                mime="text/html",
                key="filtered_html"
            )

        with col4:
            # Download as JSON
            json = df.to_json(orient="records").encode('utf-8')
            st.download_button(
                label="Download as JSON",
                data=json,
                file_name="data.json",
                mime="application/json",
                key="filtered_json"
            )

    # Load data from the uploaded file or use the initial data
    uploaded_df = load_uploaded_data(uploaded_file)
    df = uploaded_df if uploaded_df is not None else initial_df

    # Check if the dataset is the initial one or an uploaded one
    if uploaded_file is None:
        st.subheader("🧭 Template Dataset")
        st.write(
            """
            Displays the template dataset as a reference. 
            This section serves as the starting point for data exploration, 
            providing a visual representation of the data structure.
            """
        )
        
    else:
        st.subheader("📂 Uploaded Dataset")
        st.write(
            """
            Displays the dataset uploaded by the user. 
            This section serves as the starting point for data exploration, 
            providing a visual representation of the data structure.
            """
        )

        # Save the uploaded dataset        
        sqldf, table_name, db_path = save_uploaded_file_as_sqlite(uploaded_file, username)

        # Create a sidebar placeholder for the success message
        success_placeholder = st.sidebar.empty()

        # Show the success message
        success_placeholder.success(f"File successfully uploaded!")

        # Use a time delay to clear the message after 3 seconds
        time.sleep(3)

        # Clear the success message
        success_placeholder.empty()

        # Define the list of specific columns to check and coerce
        columns_to_coerce = ['MONTANT', 'FREQUENCE_RECH', 'DATA_VOLUME', 'ON_NET', 'ORANGE', 'TIGO', 'FREQ_TOP_PACK', 'REVENUE', 'ARPU_SEGMENT', 'FREQUENCE', 'REGULARITY']

        try:
            df = df.apply(pd.to_numeric, errors='ignore') 
            # Ensure numerical columns are correctly typed for specific columns
            for column in columns_to_coerce:
                if column in df.columns and df[column].dtype == 'object':
                    df[column] = pd.to_numeric(df[column], errors='coerce')
                    st.warning("""Although the data remains accessible for exploration, it is highly recommended to 
                               correct the file structure to ensure optimal performance on this page and to
                               guarantee accurate results on the analytics dashboard that truly reflect the
                               recently uploaded dataset.""")
        except Exception as e:
            st.error(f"An error occurred while processing the column '{column}': {e}")
            st.warning(
                """
                Please refer to the column description below to apply the correct data structure, 
                ensuring numerical columns have strictly numeric values and categorical columns 
                have strictly categorical values.
                """
            )
            st.stop() 
        
    # Check if 'customerID' exists as a column
    if 'user_id' in df.columns:
        df.set_index('user_id', inplace=True)

    # Capitalize the first letter of each column name if it starts with a lowercase letter
    df.columns = [col.capitalize() if col[0].islower() else col for col in df.columns]

    # Iterate through each column in the DataFrame except 'Churn'
    for column in df.columns:
        if column != 'CHURN':
            # Check if the column data type is either 'object' (for strings) or 'category'
            if df[column].dtype in ['object', 'category']:
                # Replace any NaN values in the column with 'Unknown'
                df[column].replace(np.nan, 'Unknown', inplace=True)

    # Convert 'Unknown' back to NaN in case it exists
    df['CHURN'].replace('Unknown', np.nan, inplace=True)

    # Impute missing values in 'Churn' using the most frequent value (mode)
    churn_imputer = SimpleImputer(strategy='most_frequent')
    df['CHURN'] = churn_imputer.fit_transform(df[['CHURN']]).flatten()

    # Ensure numerical columns are correctly typed
    df = df.apply(pd.to_numeric, errors='ignore') 

    # Handle missing values
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    int64_columns = df.select_dtypes(include=['int64']).columns.tolist()

    # Impute numerical columns with median
    numerical_imputer = SimpleImputer(strategy='median')
    df[numerical_columns] = numerical_imputer.fit_transform(df[numerical_columns])

    # Convert columns that were originally int64 back to int64
    for column in int64_columns:
        df[column] = df[column].astype('int64')

    # Sidebar widgets for numerical filters
    st.sidebar.header("Numerical Filter Options")

    if df is not None:
        # Display the DataFrame
        st.dataframe(df)

        with st.container():
            
            with st.expander("📊 Data Summary", expanded=False):
                st.write(
                """
                Displays a quick statistical overview of the dataset.
                This summary provides key insights into the data, such as mean, median,
                and distribution, helping users understand the general characteristics 
                of their data at a glance. 
                """
                )

                # Summary for numerical features
                numeric_summary_df = df.describe().T.reset_index()
                numeric_summary_df.rename(columns={'index': 'Feature'}, inplace=True)
                st.write("##### Numerical Features Summary")
                st.dataframe(numeric_summary_df.set_index('Feature'))

                # Summary for categorical features
                categorical_summary = df.select_dtypes(include=['object']).describe().T
                categorical_summary['unique'] = df.select_dtypes(include=['object']).nunique()
                categorical_summary['top'] = df.select_dtypes(include=['object']).mode().iloc[0]
                categorical_summary['freq'] = df.select_dtypes(include=['object']).apply(pd.Series.value_counts).max()

                categorical_summary = categorical_summary.reset_index()
                categorical_summary.rename(columns={'index': 'Feature'}, inplace=True)
                
                st.write("##### Categorical Features Summary")
                st.dataframe(categorical_summary.set_index('Feature'))

            with st.expander("🧹 Filter Data", expanded=False):
                st.write(
                    """
                    Enables interactive filtering of the dataset based on specific columns. 
                    This tool allows users to drill down into the data, focusing on subsets of interest,
                    and making the exploration more targeted and efficient.
                    """
                )

                # Dynamically detect numerical columns
                numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

                # Create a dictionary to hold slider values for numerical features
                slider_values = {}

                for column in numerical_columns:
                    if df[column].dtype == 'int64':
                        min_value = int(df[column].min())
                        max_value = int(df[column].max())
                    else:
                        min_value = float(df[column].min())
                        max_value = float(df[column].max())
                    slider_values[column] = st.sidebar.slider(
                        column,
                        min_value,
                        max_value,
                        (min_value, max_value)
                    )

                # First layer filter for categorical columns
                categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
                unique_customer_ids = df.index.unique()

                if categorical_columns:
                    selected_column = st.selectbox("Select a categorical feature to filter by", categorical_columns)

                    if not selected_column == '':
                        filtered_data = df                        
                        unique_values = df[selected_column].unique()
                        # Add an empty string option as the first option for selecting a value
                        unique_values_options = [''] + list(unique_values)
                        selected_value = st.selectbox(f"Select a value from {selected_column}", unique_values_options, format_func=lambda x: 'All Values' if x == '' else x)

                        # Add filter for specific customer IDs
                        options = [''] + list(unique_customer_ids)  
                        selected_customer_id = st.sidebar.selectbox("Select a User ID", options, format_func=lambda x: str(x) if x else 'All Users')

                        if selected_value == '' and selected_customer_id == '':
                            filtered_data = df
                            st.write("##### Filtered Data (showing all rows)")
                        elif selected_value != '' and selected_customer_id == '':
                            filtered_data = df[df[selected_column] == selected_value]
                            st.write(f"##### Filtered Data (showing rows where {selected_column} is {selected_value})")
                        elif selected_value == '' and selected_customer_id != '':
                            filtered_data = df[df.index == selected_customer_id]
                            st.write(f"##### Filtered Data (showing data for User ID {selected_customer_id})")
                        else:
                            # Filter by selected value and customer ID
                            filtered_data = df[(df[selected_column] == selected_value) & (df.index == selected_customer_id)]
                            if filtered_data.empty:
                                st.write(f"##### No data found for User ID {selected_customer_id} with {selected_column} = {selected_value}")
                            else:
                                st.write(f"##### Filtered Data (showing data for User ID {selected_customer_id} where {selected_column} is {selected_value})")


                        # Apply numerical filters to the filtered data
                        for column, (min_val, max_val) in slider_values.items():
                            filtered_data = filtered_data[
                                (filtered_data[column] >= min_val) & (filtered_data[column] <= max_val)
                            ]

                        # Display the filtered DataFrame
                        st.dataframe(filtered_data)

                        # Display numerical and categorical summaries only if no specific customer is selected
                        if selected_customer_id == '':
                            st.write("##### Numerical Features Summary for Filtered Data")
                            numeric_filtered_summary_df = filtered_data.describe().T.reset_index()
                            numeric_filtered_summary_df.rename(columns={'index': 'Feature'}, inplace=True)
                            st.dataframe(numeric_filtered_summary_df.set_index('Feature'))

                            categorical_filtered_summary = filtered_data.select_dtypes(include=['object']).describe().T
                            categorical_filtered_summary['unique'] = filtered_data.select_dtypes(include=['object']).nunique()
                            categorical_filtered_summary['top'] = filtered_data.select_dtypes(include=['object']).mode().iloc[0]
                            categorical_filtered_summary['freq'] = filtered_data.select_dtypes(include=['object']).apply(pd.Series.value_counts).max()

                            categorical_filtered_summary = categorical_filtered_summary.reset_index()
                            categorical_filtered_summary.rename(columns={'index': 'Feature'}, inplace=True)
                            
                            st.write("##### Categorical Features Summary for Filtered Data")
                            st.dataframe(categorical_filtered_summary.set_index('Feature'))

                else:
                    st.write("No categorical columns available for filtering.")

            with st.expander("📜 Column Description", expanded=False):
                st.write(
                    """
                    This section provides comprehensive descriptions of each column in the dataset, 
                    helping users understand the required structure and content to ensure alignment 
                    with analysis objectives. Consistency in data structure is critical, particularly 
                    when users upload datasets for analysis on the prediction page.

                    **Important:** It is highly recommended to upload clean data with minimal missing values 
                    for the best results. For categorical columns, missing values can be replaced with 'Unknown' 
                    to facilitate analysis. However, the app is designed to handle numerical missing values 
                    automatically to ensure proper data representation and accurate results. 
                    It is especially advisable to retain the original missing values for both categorical and numerical data
                    to ensure accuracy in forecasting models on the future projections page. 
                    
                    `Note:` The variable CHURN is the target variable for prediction and should therefore be excluded from the uploaded dataset.
                    """
                )
                    
                # Create the DataFrame
                df_info = pd.DataFrame({"Column": initial_df.columns, "Type": initial_df.dtypes})

                # Map dtype values to more descriptive terms
                df_info['Type'] = df_info['Type'].replace({
                    'object': 'Categorical',
                    'int64': 'Numerical',
                    'float64': 'Numerical'
                })

                # Delete rows where 'Column' contains 'CHURN'
                df_info = df_info[~df_info['Column'].str.contains('CHURN', na=False)]

                # Reset the index after deletion
                df_info = df_info.reset_index(drop=True)

                # Set the index to start from 1
                df_info.index = df_info.index + 1

                # Display the table
                st.table(df_info)

                # Create a description dictionary for the expected features
                descriptions = {
                    'user_id': 'Unique identifier for each client',
                    'REGION': 'The location of each client',
                    'TENURE': 'Duration in the network (months)',
                    'MONTANT': 'Top-up amount',
                    'FREQUENCE_RECH': 'Number of times the customer refilled',
                    'REVENUE': 'Monthly income of each client',
                    'ARPU_SEGMENT': 'Income over 90 days / 3',
                    'FREQUENCE': 'Number of times the client has made an income',
                    'DATA_VOLUME': 'Number of connections',
                    'ON_NET': 'Inter expresso call',
                    'ORANGE': 'Call to Orange',
                    'TIGO': 'Call to Tigo',
                    'ZONE1': 'Call to zones1',
                    'ZONE2': 'Call to zones2',
                    'MRG': 'A client who is going',
                    'REGULARITY': 'Number of times the client is active for 90 days',
                    'TOP_PACK': 'The most active packs',
                    'FREQ_TOP_PACK': 'Number of times the client has activated the top pack packages',
                }

                for col, desc in descriptions.items():
                    st.write(f"- *{col}*: {desc}")

            with st.expander("⬇️ Download Data", expanded=False):
                st.write(
                    """
                    Download the dataset in multiple formats beyond the default CSV for enhanced analysis or dissemination. 
                    Both the original and filtered datasets are available for download in the following formats: Excel, Stata, HTML, and JSON.
                    """
                )
                # Provide options to download the original data
                st.write("##### Download Original Data")
                generate_download_buttons_original(df)
                
                # Provide options to download the filtered data
                st.write("##### Download Filtered Data")
                generate_download_buttons_filtered(filtered_data)
else:
    st.warning("Please log in to explore your data.")


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