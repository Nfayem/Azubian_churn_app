# Standard library imports
import base64
import os
import sqlite3
import datetime
import time

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
import joblib

# Local application imports
from utils.login import invoke_login_widget
from utils.lottie import display_lottie_on_page


# Invoke the login form
invoke_login_widget('Future Projections')

# Fetch the authenticator from session state
authenticator = st.session_state.get('authenticator')

# Ensure the authenticator is available
if not authenticator:
    st.error("Authenticator not found. Please check the configuration.")
    st.stop()

# Check authentication status
if st.session_state.get("authentication_status"):
    username = st.session_state['username']
    st.title("Churn Prediction Dashboard")
    st.write("---")

    # Page Introduction
    with st.container():        
        left_column, right_column = st.columns(2)
        with left_column:
            st.write("""
            Welcome to the Churn Prediction Dashboard.
            Utilize this dashboard to project customer churn and develop targeted retention strategies. 
            By uploading your customer data, you enable our models to assess the probability of churn. 
            You can perform single, bulk, or template predictions by selecting the appropriate option from the sidebar and adhering to the provided instructions. 
            This functionality will assist you in directing your efforts where they are most needed.
            """)
        with right_column:
            display_lottie_on_page("Future Projections")

    # Load the initial data from a local file
    @st.cache_data(persist=True, show_spinner=False)
    def load_initial_data():
        df = pd.read_csv('./data/CAP_tempred.csv', index_col='user_id')
        return df
    
    initial_df = load_initial_data()

    # Ensure 'data_source' is initialized in session state
    if 'data_source' not in st.session_state:
        st.session_state['data_source'] = 'initial' 

    # Function to load the most recent table from the user's SQLite database
    def load_most_recent_table(username):
        # Define the path for the user's SQLite database
        db_path = os.path.join("data", username, f"{username}.db")

        if not os.path.exists(db_path):
            st.error("No database found for the user. Please ensure a file has been uploaded on the data overview page.")
            return None, None

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Get the most recent table name
        tables_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE ?
        ORDER BY name DESC LIMIT 1;
        """
        try:
            most_recent_table = conn.execute(tables_query, (f"{username}_table%",)).fetchone()

            if most_recent_table:
                table_name = most_recent_table[0]
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn, index_col='user_id')
                st.session_state['data_source'] = 'uploaded'
            else:
                st.error("No tables found in the database.")
                return None, None
        except Exception as e:
            st.error(f"An error occurred while loading the table: {e}")
            return None, None
        finally:
            conn.close()

        return df, table_name


    # Load models
    @st.cache_resource(show_spinner=False)
    def models():
        rf_model = joblib.load('./models/RF_pipeline.joblib')
        knn_model = joblib.load('./models/KNN_pipeline.joblib')
        fnn_model = joblib.load('./models/FNN_pipeline.joblib')
        return rf_model, knn_model, fnn_model

    RF, KNN, FNN = models()

    # Sidebar radio buttons for selecting prediction type
    prediction_type = st.sidebar.radio(
        "Choose Prediction Type:",
        ('Single Prediction', 'Bulk Prediction', 'Template Prediction')
    )

    # Select model 
    selected_model = st.selectbox('Select a Model', ['', 'Random Forest', 'K Nearest', 'Feedforward'], 
                                    key='selected_model',
                                    index=0)

    # Function to get the selected model
    @st.cache_resource(show_spinner='Loading models...')
    def get_model(selected_model):
        if selected_model == '':
            st.warning('Please select a model before making a prediction.')
            return None, None
        elif selected_model == 'Random Forest':
            pipeline = RF
        elif selected_model == 'K Nearest':
            pipeline = KNN            
        else:
            pipeline = FNN
        encoder = joblib.load('./models/churn_encoder.joblib')
        return pipeline, encoder
    
    # Initialize session states for relevant variables
    if 'prediction' not in st.session_state:
        st.session_state['prediction'] = None
    if 'probability' not in st.session_state:
        st.session_state['probability'] = None
    if 'probability' not in st.session_state:
        st.session_state['probability'] = None
    if 'USER_ID' not in st.session_state:
        st.session_state['USER_ID'] = None

    # Define patterns for different package types
    patterns = {
        'On net 200F=Unlimited _call24H', 'nan', 'Data:490F=1GB,7d', 
        'All-net 500F=2000F;5d', 'On-net 500=4000,10d', 'Data:3000F=10GB,30d', 
        'Data:200F=Unlimited,24H', 'IVR Echat_Daily_50F', 'Data:1000F=2GB,30d', 
        'Mixt 250F=Unlimited_call24H', 'On-net 1000F=10MilF;10d', 
        'MIXT:500F=2500F on net _2500F off net;2d', 'Data:200F=100MB,24H', 
        'All-net 600F=3000F ;5d', 'On-net 200F=60mn;1d', 'Twter_U2opia_Daily', 
        'Data:100F=40MB,24H', 'All-net 500F=2000F_AllNet_Unlimited', 
        'On net 200F=3000F_10Mo ;24H', '200=Unlimited1Day', 'Jokko_Daily', 
        'Data:1000F=5GB,7d', 'Data:700F=1.5GB,7d', 'All-net 1000=5000;5d', 
        'Data:150F=SPPackage1,24H', 'IVR Echat_Monthly_500F', 'VAS(IVR_Radio_Daily)', 
        'MIXT:390F=04HOn-net_400SMS_400Mo;4h', 'MIXT:200mnoffnet_unlonnet_5Go;30d', 
        'On-net 500F_FNF;3d', 'MIXT:590F=02H_On-net_200SMS_200Mo;24h', 
        'Data:1500F=3GB,30D', 'Data:300F=100MB,2d', 'Data:500F=2GB,24H', 
        'Data:490F=Night,00H-08H', 'All-net 1000F=(3000FOn+3000FOff);5d', 
        'New_YAKALMA_4_ALL', 'MIXT:10000F=10hAllnet_3Go_1h_Zone3;30d', 
        'Yewouleen_PKG', 'Data:1500F=SPPackage1,30d', 'WIFI_Family_2MBPS', 
        'All-net 500F=1250F_AllNet_1250_Onnet;48h', 'On-net 300F=1800F;3d', 
        'Twter_U2opia_Weekly', 'Data:50F=30MB_24H', 'MIXT:1000F=4250Offnet_4250FOnnet_100Mo;5d', 
        'WIFI_Family_4MBPS', 'Data:700F=SPPackage1,7d', 'Jokko_promo', 
        'CVM_on-netbundle500=5000', 'Pilot_Youth4_490', 'All-net 300=600;2d', 
        'Twter_U2opia_Monthly', 'IVR_Echat_Weekly_200F', 'TelmunCRBT_daily', 
        'MROMO_TIMWES_RENEW', 'MIXT:500F=75(SMS,ONNET,Mo)_1000FAllNet;24h', 
        'Pilot_Youth1_290', 'On-net 2000f_One_Month_100H;30d', 
        'Data:DailyCycle_Pilot_1.5GB', 'Jokko_Monthly', 'Facebook_MIX_2D', 
        'CVM_200f=400MB', 'YMGX100=1hourFNF,24H/1month', 'Jokko_Weekly', 
        'Internat:1000F_Zone_1;24H', 'Data:30Go_V30_Days', 'SUPERMAGIK_5000', 
        'FNF2(JAPPANTE)', '200F=10mnOnNetValid1H', 
        'MIXT:5000F=80Konnet_20Koffnet_250Mo;30d', 'pilot_offer6', 
        '500=Unlimited3Day', 'VAS(IVR_Radio_Monthly)', 'MROMO_TIMWES_OneDAY', 
        'Mixt:500F=2500Fonnet_2500Foffnet;5d', 'Internat:1000F_Zone_3;24h', 
        'All-net5000=20000off+20000on;30d', 'EVC_500=2000F', 
        'Data:200F=1GB,24H', 'Staff_CPE_Rent', 'SUPERMAGIK_1000', 
        'All-net500F=4000F;5d', '305155009', 'DataPack_Incoming', 
        'Incoming_Bonus_woma', 'FIFA_TS_daily', 'VAS(IVR_Radio_Weekly)', 
        '1000=Unlimited7Day', 'Internat:2000F_Zone_2;24h', 'FNF_Youth_ESN', 
        'WIFI_Family_10MBPS', 'Data_EVC_2Go24H', 'MIXT:4900F=10HOnnet_1,5Go;30d', 
        'EVC_Jokko_Weekly', 'EVC_JOKKO30', 'Data_Mifi_20Go', 'Data_Mifi_10Go_Monthly', 
        'CVM_150F_unlimited', 'CVM_100F_unlimited', 'CVM_100f=200MB', 
        'FIFA_TS_weekly', '150=unlimitedpilotoauto', 'CVM_100f=500OnNet', 
        'GPRS_3000Equal10GPORTAL', 'EVC_100Mo', 'GPRS_PKG_5GO_ILLIMITE', 
        'NEW_CLIR_PERMANENT_LIBERTE_MOBILE', 'EVC_1Go', 'pilot_offer4', 
        'CVM_500f=2GB', 'pack_chinguitel_24h', 'PostpaidFORFAIT10HPackage', 
        'EVC_700Mo', 'CVM_On-net400f=2200F', 'CVM_On-net1300f=12500', 
        'All-net500=4000off+4000on;24H', 'SMSMax', 'EVC_4900=12000F', 
        'APANews_weekly', 'NEW_CLIR_TEMPALLOWED_LIBERTE_MOBILE', 
        'Data:OneTime_Pilot_1.5GB', 'YMGXon-net100=700F,24H', '301765007', 
        '1500=Unlimited7Day', 'APANews_monthly', '200=unlimitedpilotoauto'
    }

    # Define classification function
    def classify_top_pack(top_pack):
        if pd.isna(top_pack):
            return np.nan
        top_pack = top_pack.lower()
        if any(keyword in top_pack for keyword in ['data', 'gb', 'mb', 'internet', 'web', 'wifi', 'internat', 'mifi', 'unlimited3day', 'unlimited1day', 'unlimited7day']):
            return 'Data Package'
        elif any(keyword in top_pack for keyword in ['call', 'unlimited call', 'minutes', 'on net', 'on-net', 'all-net', 'onnet']):
            return 'Voice Package'
        elif 'sms' in top_pack or 'text' in top_pack:
            return 'SMS Package'
        elif 'ivr' in top_pack:
            return 'IVR Package'
        elif 'twter' in top_pack:
            return 'Twitter Package'
        elif 'facebook' in top_pack:
            return 'Facebook Package'
        elif 'evr' in top_pack:
            return 'EVR Package'
        elif 'evc' in top_pack:
            return 'EVC Package'
        elif 'jokko' in top_pack:
            return 'Jokko Package'
        elif 'pilot' in top_pack:
            return 'Pilot Package'
        elif 'cvm' in top_pack:
            return 'CVM Package'
        elif 'gprs' in top_pack:
            return 'GPRS Package'
        elif any(keyword in top_pack for keyword in ['combo', 'mixt', 'package', 'bundle']):
            return 'Combo Package'
        elif any(keyword in top_pack for keyword in ['news', 'fifa', 'postpaid', 'bonus', 'fnf', 'incoming']):
            return 'Subscription or Bonus Package'
        else:
            return 'Other Package'

    # Function to make a single prediction
    def make_single_prediction(pipeline, encoder):
        if pipeline is None:
            return  

        else:
        # Collect user input from session state
            user_input = {
                'user_id': st.session_state['USER_ID'],
                'REGION': st.session_state['REGION'],
                'TENURE': st.session_state['TENURE'],
                'MONTANT': st.session_state['MONTANT'],
                'FREQUENCE_RECH': st.session_state['FREQUENCE_RECH'],
                'REVENUE': st.session_state['REVENUE'],
                'ARPU_SEGMENT': st.session_state['ARPU_SEGMENT'],
                'FREQUENCE': st.session_state['FREQUENCE'],
                'DATA_VOLUME': st.session_state['DATA_VOLUME'],
                'ON_NET': st.session_state['ON_NET'],
                'ORANGE': st.session_state['ORANGE'],
                'TIGO': st.session_state['TIGO'],
                'REGULARITY': st.session_state['REGULARITY'],
                'TOP_PACK': st.session_state['TOP_PACK'],
                'FREQ_TOP_PACK': st.session_state['FREQ_TOP_PACK'],
                }

            # Convert the input data to a DataFrame
            df = pd.DataFrame(user_input, index=[0])

            # Set 'customerID' as the index
            if 'user_id' in df.columns:
                df.set_index('user_id', inplace=True)
            else:
                st.error("Column 'user_id' not found in the dataset.")

            # Ensure numerical columns are correctly typed
            df = df.apply(pd.to_numeric, errors='ignore')  

            # Make predictions
            pred = pipeline.predict(df) 
            pred_int = int(pred[0])   
            prediction = encoder.inverse_transform([[pred_int]])[0]

            # Calculate the probability of churn
            probability = pipeline.predict_proba(df)
            prediction_labels = "Churn" if pred == 1 else "No Churn"

            # Display prediction results
            user_id = st.session_state['USER_ID']

            # Update the session state with the prediction and probabilities
            st.session_state['prediction'] = prediction
            st.session_state['probability'] = probability
            st.session_state['prediction_labels'] = prediction_labels

            # Copy the original dataframe to the new dataframe
            hist_df = df.copy()
            hist_df['PredictionTime'] = datetime.date.today()
            hist_df['ModelUsed'] = st.session_state['selected_model']
            hist_df['Prediction'] = prediction
            hist_df['Predicted Churn'] = prediction_labels
            hist_df['Probability'] = np.where(pred == 1, np.round(probability[:, 1] * 100, 2), np.round(probability[:, 0] * 100, 2))

            # Create a directory for the database if it doesn't exist
            db_dir = f"./data/{st.session_state['username']}"
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Save the history dataframe to SQLite database
            db_path = f"{db_dir}/{st.session_state['username']}.db"
            conn = sqlite3.connect(db_path)
            hist_df.to_sql('single_predict', conn, if_exists='append', index=True)
            conn.close()

            return prediction, probability, prediction_labels

    # Function to get user input
    def get_user_input():
        pipeline, encoder = get_model(selected_model)

        if pipeline == None:
            return
        else:
            st.info('Please ensure all fields are properly filled.')
            with st.form('input-feature', clear_on_submit=True):
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write('### Customer Information')
                    st.text_input('User_ID', key='USER_ID')
                    st.write('### Customer Information')
                    st.selectbox('Region', options=['DAKAR', 'SAINT-LOUIS', 'THIES', 'LOUGA', 'MATAM', 'FATICK', 'KAFFRINE','KAOLACK', 'KEDOUGOU', 'KOLDA', 'DIOURBEL', 'SEDHIOU', 'TAMBACOUNDA', 'ZIGUINCHOR'], key='REGION')
                
                with col2:
                    st.write('### Customer Usage Patterns')
                    st.selectbox('Key in tenure', options=['D3-6 month', 'E6-9 month', 'F9-12 month', 'G12-15 month', 'H15-18 month', 'I18-21 month', 'J21-24 month', 'K>24 month'], key='TENURE')
                    st.number_input('Key in top-up amount(MONTANT)', min_value=0.00, max_value=1000000.00, step=0.10, key='MONTANT')
                    st.number_input('Key in frequency of top-up (FREQUENCE_RECH)', min_value=0.00, max_value=500.00, step=0.10, key='FREQUENCE_RECH')
                    st.number_input('Enter data volume (DATA_VOLUME)', min_value=0.00, max_value=1000000.00, step=0.10, key='DATA_VOLUME')
                    st.number_input('Enter the number calls made within Azubian Expresso (ON_NET)', min_value=0.00, max_value=100000.00, step=0.10, key='ON_NET')
                    st.number_input('Enter the number of calls to ORANGE', min_value=0.00, max_value=100000.00, step=0.10, key='ORANGE')
                    st.number_input('Enter the number of calls to TIGO', min_value=0.00, max_value=100000.00, step=0.10, key='TIGO')
                    st.selectbox('Enter the most active package (TOP_PACK)', options=['data_pack', 'voice_pack', 'mixed_pack', 'jokko_pack', 'vas_pack', 'international_pack', 'sms_pack', 'social_pack', 'eve_pack'], key='TOP_PACK')
                    st.number_input('Enter the number of times customer activated the top package (FREQ_TOP_PACK)', min_value=0.00, max_value=1000.00, step=1.00, key='FREQ_TOP_PACK')

                with col3:
                    st.write('### Customer Revenue and Revenue Generation')
                    st.number_input('Key in the monthly revenue per customer (REVENUE)', min_value=0.00, max_value=1000000.00, step=0.10, key='REVENUE')
                    st.number_input('Key in customer income over the 90 day period (ARPU_SEGMENT)', min_value=0.00, max_value=1000000.00, step=0.10, key='ARPU_SEGMENT')
                    st.number_input('Key in the frequency of income over the 90 day period (FREQUENCE)', min_value=0.00, max_value=200.00, step=0.10, key='FREQUENCE')
                
                with col4:
                    st.write('### Customer Activity and Churn Indicators')
                    st.number_input('Enter the number of times customer is active over the 90 period (REGULARITY)', min_value=0.00, max_value=100.00, step=0.10, key='REGULARITY')
                st.form_submit_button('Make Prediction', on_click=make_single_prediction, kwargs=dict(pipeline=pipeline, encoder=encoder))
        
            st.info('Prediction results will be shown here.')

    # Function to make bulk predictions using uploaded dataset
    def make_bulk_prediction(pipeline, encoder, bulk_input_df):
        # Convert the input data to a DataFrame
        df = bulk_input_df.copy()

        # Set 'customerID' column as the index
        if 'user_id' in df.columns:
            df.set_index('user_id', inplace=True)

        # Drop 'Churn' column if it exists
        if 'CHURN' in df.columns:
            df.drop('CHURN', axis=1, inplace=True)

        # Ensure numerical columns are correctly typed
        df = df.apply(pd.to_numeric, errors='ignore')

        # Define the list of specific columns to check and coerce
        columns_to_coerce = ['MONTANT', 'FREQUENCE_RECH', 'DATA_VOLUME', 'ON_NET', 'ORANGE', 'TIGO', 'FREQ_TOP_PACK', 'REVENUE', 'ARPU_SEGMENT', 'FREQUENCE', 'REGULARITY']

        try:
            # Ensure numerical columns are correctly typed for specific columns
            for column in columns_to_coerce:
                if column in df.columns and df[column].dtype == 'object':
                    df[column] = pd.to_numeric(df[column], errors='coerce')
        except Exception as e:
            st.error(f"An error occurred while processing the column '{column}': {e}")
            st.warning(
                """
                Please refer to the Data Overview page to apply the correct data structure, 
                ensuring numerical columns have strictly numeric values and categorical columns 
                have strictly categorical values.
                """
            )

        # Drop 'ZONE1' and 'ZONE2' columns if they exist
        df.drop(columns=[col for col in ['ZONE1', 'ZONE2', 'MRG'] if col in df.columns], inplace=True)

        # Apply the classification function to the TOP_PACK column
        df['TOP_PACK'] = df['TOP_PACK'].apply(classify_top_pack)

        # Check if both 'TOP_PACK' and 'FREQ_TOP_PACK' have missing values and the same number of missing values
        if df['TOP_PACK'].isna().sum() == df['FREQ_TOP_PACK'].isna().sum() and df['TOP_PACK'].isna().sum() > 0:
            # Fill missing values in TOP_PACK with the most frequent value (mode)
            df['TOP_PACK'] = df['TOP_PACK'].fillna(df['TOP_PACK'].mode()[0])
            
            # Fill missing values in FREQ_TOP_PACK based on the median of the respective TOP_PACK group
            df['FREQ_TOP_PACK'] = df.groupby('TOP_PACK')['FREQ_TOP_PACK'].transform(lambda x: x.fillna(x.median()))

        # Check if both 'MONTANT' and 'FREQUENCE_RECH' have missing values and the same number of missing values
        if df['MONTANT'].isna().sum() == df['FREQUENCE_RECH'].isna().sum() and df['MONTANT'].isna().sum() > 0:
            # Fill missing values in MONTANT with its overall median
            df['MONTANT'] = df['MONTANT'].fillna(df['MONTANT'].median())
            
            # Fill missing values in FREQUENCE_RECH based on the median of the respective MONTANT group
            df['FREQUENCE_RECH'] = df.groupby('MONTANT')['FREQUENCE_RECH'].transform(lambda x: x.fillna(x.median()))

        # Check if 'REVENUE', 'ARPU_SEGMENT', and 'FREQUENCE' have the same number of missing values
        if df['REVENUE'].isna().sum() == df['ARPU_SEGMENT'].isna().sum() == df['FREQUENCE'].isna().sum() and df['REVENUE'].isna().sum() > 0:
            # Fill missing values in REVENUE with its overall median
            df['REVENUE'] = df['REVENUE'].fillna(df['REVENUE'].median())
            
            # Fill missing values in ARPU_SEGMENT based on the median of the respective REVENUE group
            df['ARPU_SEGMENT'] = df.groupby('REVENUE')['ARPU_SEGMENT'].transform(lambda x: x.fillna(x.median()))
            
            # Fill missing values in FREQUENCE based on the median of the respective REVENUE group
            df['FREQUENCE'] = df.groupby('REVENUE')['FREQUENCE'].transform(lambda x: x.fillna(x.median()))

        # Check if 'DATA_VOLUME' has more missing values than 'REGION' and 'TENURE'
        if df['DATA_VOLUME'].isna().sum() > df['REGION'].isna().sum() and df['DATA_VOLUME'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in DATA_VOLUME based on the median of the respective REGION and TENURE groups
            df['DATA_VOLUME'] = df.groupby(['REGION', 'TENURE'])['DATA_VOLUME'].transform(lambda x: x.fillna(x.median()))

        # Check if 'TIGO' has more missing values than 'REGION' and 'TENURE'
        if df['TIGO'].isna().sum() > df['REGION'].isna().sum() and df['TIGO'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in TIGO based on the median of the respective REGION and TENURE groups
            df['TIGO'] = df.groupby(['REGION', 'TENURE'])['TIGO'].transform(lambda x: x.fillna(x.median()))

        # Check if 'ORANGE' has more missing values than 'REGION' and 'TENURE'
        if df['ORANGE'].isna().sum() > df['REGION'].isna().sum() and df['ORANGE'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in ORANGE based on the median of the respective REGION and TENURE groups
            df['ORANGE'] = df.groupby(['REGION', 'TENURE'])['ORANGE'].transform(lambda x: x.fillna(x.median()))

        # Make predictions
        predictions = pipeline.predict(df)
        probabilities = pipeline.predict_proba(df)
        prediction_labels = encoder.inverse_transform(predictions)

        # Update the session state with the prediction and probabilities
        st.session_state['predictions'] = predictions
        st.session_state['probability'] = probabilities
        st.session_state['prediction_labels'] = prediction_labels
        
        # Add prediction columns to the DataFrame
        df['PredictionTime'] = datetime.date.today()
        df['ModelUsed'] = st.session_state['selected_model']
        df['Prediction'] = prediction_labels
        df['Predicted Churn'] = predictions
        df['Predicted Churn'] = df['Predicted Churn'].map({1: 'Churn', 0: 'No Churn'})
        df['Probability'] = np.where(predictions == 1, np.round(probabilities[:, 1] * 100, 2), np.round(probabilities[:, 0] * 100, 2))

        # Make a copy of the dataframe
        dfp = df.copy()

        # Determine the correct file name for bulk predictions
        db_path = f"./data/{st.session_state['username']}/{st.session_state['username']}.db"
        conn = sqlite3.connect(db_path)
        
        # Create a unique table name based on the selected model
        model_name = st.session_state['selected_model'].replace(" ", "_").lower()
        db_path = f"./data/{st.session_state['username']}/{st.session_state['username']}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Determine the next table name for the selected model with padding
        tables_query = f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '{model_name}_bulk_predict%'
        ORDER BY name DESC LIMIT 1;
        """
        result = cursor.execute(tables_query).fetchone()
        if result:
            last_table_name = result[0]
            last_table_number = int(last_table_name.split("_")[-1])
            new_table_number = last_table_number + 1
        else:
            new_table_number = 0

        # Add padding of 5 zeros to the table number
        new_table_name = f"{model_name}_bulk_predict_{str(new_table_number).zfill(6)}"

        # Save the DataFrame to the new bulk_predict table
        df.to_sql(new_table_name, conn, if_exists='replace', index=True)

        # Close the database connection
        conn.close()

        return predictions, probabilities, dfp
    
    # Fuction to make bulk predictions using template dataset
    def make_template_prediction(pipeline, encoder, template_df):
        # Convert the input data to a DataFrame
        df = template_df.copy()

        # Set 'customerID' column as the index
        if 'user_id' in df.columns:
            df.set_index('user_id', inplace=True)

        # Drop 'Churn' column if it exists
        if 'CHURN' in df.columns:
            df.drop('CHURN', axis=1, inplace=True)

        # Ensure numerical columns are correctly typed
        df = df.apply(pd.to_numeric, errors='ignore')

        # Define the list of specific columns to check and coerce
        columns_to_coerce = ['MONTANT', 'FREQUENCE_RECH', 'DATA_VOLUME', 'ON_NET', 'ORANGE', 'TIGO', 'FREQ_TOP_PACK', 'REVENUE', 'ARPU_SEGMENT', 'FREQUENCE', 'REGULARITY']

        try:
            # Ensure numerical columns are correctly typed for specific columns
            for column in columns_to_coerce:
                if column in df.columns and df[column].dtype == 'object':
                    df[column] = pd.to_numeric(df[column], errors='coerce')
        except Exception as e:
            st.error(f"An error occurred while processing the column '{column}': {e}")
            st.warning(
                """
                Please refer to the Data Overview page to apply the correct data structure, 
                ensuring numerical columns have strictly numeric values and categorical columns 
                have strictly categorical values.
                """
            )

        # Drop 'ZONE1' and 'ZONE2' columns if they exist
        df.drop(columns=[col for col in ['ZONE1', 'ZONE2', 'MRG'] if col in df.columns], inplace=True)

        # Apply the classification function to the TOP_PACK column
        df['TOP_PACK'] = df['TOP_PACK'].apply(classify_top_pack)

        # Check if both 'TOP_PACK' and 'FREQ_TOP_PACK' have missing values and the same number of missing values
        if df['TOP_PACK'].isna().sum() == df['FREQ_TOP_PACK'].isna().sum() and df['TOP_PACK'].isna().sum() > 0:
            # Fill missing values in TOP_PACK with the most frequent value (mode)
            df['TOP_PACK'] = df['TOP_PACK'].fillna(df['TOP_PACK'].mode()[0])
            
            # Fill missing values in FREQ_TOP_PACK based on the median of the respective TOP_PACK group
            df['FREQ_TOP_PACK'] = df.groupby('TOP_PACK')['FREQ_TOP_PACK'].transform(lambda x: x.fillna(x.median()))

        # Check if both 'MONTANT' and 'FREQUENCE_RECH' have missing values and the same number of missing values
        if df['MONTANT'].isna().sum() == df['FREQUENCE_RECH'].isna().sum() and df['MONTANT'].isna().sum() > 0:
            # Fill missing values in MONTANT with its overall median
            df['MONTANT'] = df['MONTANT'].fillna(df['MONTANT'].median())
            
            # Fill missing values in FREQUENCE_RECH based on the median of the respective MONTANT group
            df['FREQUENCE_RECH'] = df.groupby('MONTANT')['FREQUENCE_RECH'].transform(lambda x: x.fillna(x.median()))

        # Check if 'REVENUE', 'ARPU_SEGMENT', and 'FREQUENCE' have the same number of missing values
        if df['REVENUE'].isna().sum() == df['ARPU_SEGMENT'].isna().sum() == df['FREQUENCE'].isna().sum() and df['REVENUE'].isna().sum() > 0:
            # Fill missing values in REVENUE with its overall median
            df['REVENUE'] = df['REVENUE'].fillna(df['REVENUE'].median())
            
            # Fill missing values in ARPU_SEGMENT based on the median of the respective REVENUE group
            df['ARPU_SEGMENT'] = df.groupby('REVENUE')['ARPU_SEGMENT'].transform(lambda x: x.fillna(x.median()))
            
            # Fill missing values in FREQUENCE based on the median of the respective REVENUE group
            df['FREQUENCE'] = df.groupby('REVENUE')['FREQUENCE'].transform(lambda x: x.fillna(x.median()))

        # Check if 'DATA_VOLUME' has more missing values than 'REGION' and 'TENURE'
        if df['DATA_VOLUME'].isna().sum() > df['REGION'].isna().sum() and df['DATA_VOLUME'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in DATA_VOLUME based on the median of the respective REGION and TENURE groups
            df['DATA_VOLUME'] = df.groupby(['REGION', 'TENURE'])['DATA_VOLUME'].transform(lambda x: x.fillna(x.median()))

        # Check if 'TIGO' has more missing values than 'REGION' and 'TENURE'
        if df['TIGO'].isna().sum() > df['REGION'].isna().sum() and df['TIGO'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in TIGO based on the median of the respective REGION and TENURE groups
            df['TIGO'] = df.groupby(['REGION', 'TENURE'])['TIGO'].transform(lambda x: x.fillna(x.median()))

        # Check if 'ORANGE' has more missing values than 'REGION' and 'TENURE'
        if df['ORANGE'].isna().sum() > df['REGION'].isna().sum() and df['ORANGE'].isna().sum() > df['TENURE'].isna().sum():
            # Contextually fill missing values in ORANGE based on the median of the respective REGION and TENURE groups
            df['ORANGE'] = df.groupby(['REGION', 'TENURE'])['ORANGE'].transform(lambda x: x.fillna(x.median()))

        # Make predictions
        predictions = pipeline.predict(df)
        probabilities = pipeline.predict_proba(df)
        prediction_labels = encoder.inverse_transform(predictions)

        # Update the session state with the prediction and probabilities
        st.session_state['predictions'] = predictions
        st.session_state['probability'] = probabilities
        st.session_state['prediction_labels'] = prediction_labels
        
        # Add prediction columns to the DataFrame
        df['PredictionTime'] = datetime.date.today()
        df['ModelUsed'] = st.session_state['selected_model']
        df['Prediction'] = prediction_labels
        df['Predicted Churn'] = predictions
        df['Predicted Churn'] = df['Predicted Churn'].map({1: 'Churn', 0: 'No Churn'})
        df['Probability'] = np.where(predictions == 1, np.round(probabilities[:, 1] * 100, 2), np.round(probabilities[:, 0] * 100, 2))

        # Make a copy of the dataframe
        dfp = df.copy()

        # Create a unique table name based on the selected model
        model_name = st.session_state['selected_model'].replace(" ", "_").lower()
        
        # Define the path to the user's database
        db_path = f"./data/template/churn_predict.db"
        
        # Check if the database directory exists, create if not
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to the SQLite database (creates the database if it doesn't exist)
        conn = sqlite3.connect(db_path)

        # Save the template DataFrame to the SQLite database as 'template_predict'
        df.to_sql(f'{model_name}_template_predict000000', conn, if_exists='replace', index=True)

        # Close the database connection
        conn.close()

        return predictions, probabilities, dfp
    
    # Functionality for Single Prediction
    if prediction_type == 'Single Prediction':
        st.subheader("Single Prediction")     
        get_user_input()
        
        # Display prediction results
        prediction = st.session_state['prediction']
        probability = st.session_state['probability']

        if prediction is None:
            st.stop()
        elif prediction == "Yes":
            st.markdown("##### Prediction Results:")
            probability_of_churn = probability[0][1] * 100
            st.markdown(f'Customer {st.session_state["USER_ID"]} is likely to churn with a probability of {round(probability_of_churn, 2)}%.')
            st.info("Visit the History page to view and download the most recent single prediction dataset.")
        else:
            st.markdown("##### Prediction Results:")
            probability_of_no_churn = probability[0][0] * 100
            st.markdown(f'Customer {st.session_state["USER_ID"]} is unlikely to churn with a probability of {round(probability_of_no_churn, 2)}%.')
            st.info("Visit the History page to view and download the most recent single prediction dataset.")

    # Functionality for Bulk Prediction
    if prediction_type == 'Bulk Prediction':
        st.subheader("Bulk Prediction")
        # Sidebar for file upload
        st.sidebar.title("Data Upload")
        upload_option = st.sidebar.selectbox("Choose data source", ("SQLite Database", "Upload CSV/Excel"))

        if upload_option == "Upload CSV/Excel":
            uploaded_file = st.sidebar.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx", "xls"])

            if uploaded_file is not None:
                # Determine the file type and load accordingly
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, index_col='user_id')
                elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file, index_col='user_id')

                st.session_state['data_source'] = 'user_uploaded'
                st.success("File uploaded successfully!", icon="✅")
                table_name = 'Uploaded Dataset'
            else:
                st.warning("Please upload a CSV or Excel file.")

        elif upload_option == "SQLite Database":
            username = st.sidebar.text_input("Enter your username")
            
            if username:
                # Load the most recent table from the SQLite database
                df, table_name = load_most_recent_table(username)
                if df is not None:
                    st.session_state['data_source'] = 'uploaded'
                    st.success(f"Loaded data from table: {table_name}", icon="✅")
            else:
                st.warning("Please enter a username to load data from the SQLite database.")

        pipeline, encoder = get_model(selected_model)
        if pipeline is None:
            st.stop()

        if st.button("Run Bulk Prediction"):
            st.write(f"Using dataset: {table_name}")
            if df is not None:
                st.write("First 5 rows of the uploaded dataset:")
                st.dataframe(df.head())                
                predictions, probabilities, dfp = make_bulk_prediction(pipeline, encoder, df)
                st.write("First 5 rows of the prediction results:")
                st.dataframe(dfp.head())
                st.info("Visit the History page to view and download the full bulk prediction dataset.")

    # Functionality for Template Prediction
    if prediction_type == 'Template Prediction':
        st.subheader("Template Prediction")

        pipeline, encoder = get_model(selected_model)
        if pipeline is None:
            st.stop()

        if st.button("Run Template Prediction"):
            st.session_state['data_source'] = 'initial'
            table_name = "Template Dataset"
            st.write(f"Using dataset: {table_name}")
            df = initial_df

            if df is not None:
                st.write("First 5 rows of the template dataset:")
                st.dataframe(df.head())                
                predictions, probabilities, dfp = make_template_prediction(pipeline, encoder, df)
                st.write("First 5 rows of the prediction results:")
                st.dataframe(dfp.head())
                st.info("Visit the History page to view and download the full template prediction dataset.")
else:
    st.warning("Please log in to make predictions.")
    

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