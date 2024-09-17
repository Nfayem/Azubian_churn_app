# Standard library imports
import base64
import os
import sqlite3
from io import BytesIO

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Local application imports
from utils.login import invoke_login_widget
from utils.lottie import display_lottie_on_page


# Invoke the login form
invoke_login_widget('History Overview')

# Fetch the authenticator from session state
authenticator = st.session_state.get('authenticator')

# Ensure the authenticator is available
if not authenticator:
    st.error("Authenticator not found. Please check the configuration.")
    st.stop()

# Function to randmize dates
def randomize_dates(df, column_name):
    # Ensure the column is in datetime format
    df[column_name] = pd.to_datetime(df[column_name])
    
    # Check for unique dates in the column
    unique_dates = df[column_name].unique()
    
    if len(unique_dates) == 1:
        # If only one unique date, create a date range around that date
        single_date = unique_dates[0]
        date_range = pd.date_range(
            start=single_date - pd.Timedelta(days=30), 
            end=single_date + pd.Timedelta(days=30),
            periods=len(df)
        )
        df[column_name] = np.random.choice(date_range, size=len(df), replace=False)
    else:
        # Otherwise, randomize existing dates
        random_dates = np.random.choice(unique_dates, size=len(df))
        df[column_name] = random_dates

    return df

# Function to generate download buttons for filtered data in multiple formats
def generate_download_buttons(df):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Download as Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        st.download_button(
            label="Download as Excel",
            data=excel_buffer.getvalue(),
            file_name="filtered_data.xlsx",
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
            file_name="filtered_data.dta",
            mime="application/x-stata",
            key="filtered_stata"
        )

    with col3:
        # Download as HTML
        html = df.to_html(index=False).encode('utf-8')
        st.download_button(
            label="Download as HTML",
            data=html,
            file_name="filtered_data.html",
            mime="text/html",
            key="filtered_html"
        )

    with col4:
        # Download as JSON
        json = df.to_json(orient="records").encode('utf-8')
        st.download_button(
            label="Download as JSON",
            data=json,
            file_name="filtered_data.json",
            mime="application/json",
            key="filtered_json"
        )

# Check authentication status
if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    st.title("Churn History Overview")
    st.write("---")

     # Page Introduction
    with st.container():       
        left_column, right_column = st.columns(2)
        with left_column:
            st.write("""
            Welcome to the **Churn History Overview** dashboard. This interactive platform allows you to:
            - **Explore and analyze** your churn prediction data across different prediction types.
            - **Apply dynamic filters** including date ranges, numerical, and categorical filters for in-depth analysis.
            - **Visualize trends and proportions** through interactive charts and graphs.
            - **Assess model performance** by comparing probability accuracies across different models.
            
            Utilize the sidebar options to select and filter data as per your requirements.
            """)
        with right_column:
            display_lottie_on_page("History Overview")
    
    # Sidebar Configuration
    
    # Prediction File Type Selection with Descriptions
    st.sidebar.header("🔧 Options")
    
    selected_file_type = st.sidebar.radio(
        "Select Prediction File Type:",
        ('Single Prediction', 'Bulk Prediction', 'Template Prediction'),
        help="Choose the type of prediction data you want to analyze."
    )
    
    file_descriptions = {
        'Single Prediction': """
        **Single Prediction** files contain individual customer churn predictions made over time. 
        This dataset grows with each new prediction and allows for time-series analysis of churn probabilities.
        """,
        'Bulk Prediction': """
        **Bulk Prediction** files consist of batch predictions made at specific times. 
        Each file corresponds to a bulk prediction event, enabling comparative analysis across different batches.
        """,
        'Template Prediction': """
        The **Template Preview** provides a static structure of the prediction data with actual prediction results. 
        """
    }   
    
    # Load Data from SQLite Database
    db_path1 = f"./data/{username}/{username}.db"
    db_path2 = f"./data/template/churn_predict.db"

    if not os.path.exists(db_path1):
        st.error("No database found for the user. Please ensure data has been uploaded on the Data Overview page.")
        st.stop()

    # Establishing database connections
    conn1 = sqlite3.connect(db_path1)
    conn2 = sqlite3.connect(db_path2)

    # Initialize session state for model, period, and data
    if 'model_name' not in st.session_state:
        st.session_state['model_name'] = None
    if 'selected_period' not in st.session_state:
        st.session_state['selected_period'] = ''
    if 'df' not in st.session_state:
        st.session_state['df'] = None

    # Function to load bulk prediction data
    def load_bulk_prediction(model_name, n=1):
        bulk_tables_query = f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE '{model_name}_bulk_predict%'
        ORDER BY name DESC LIMIT {n};
        """
        result = conn1.execute(bulk_tables_query).fetchall()
        if result:
            dfs = [pd.read_sql_query(f"SELECT * FROM {table_name[0]}", conn1, index_col='user_id') for table_name in result]
            st.info(f"Loaded {len(dfs)} prediction file(s) for {model_name}.")
            return pd.concat(dfs) if len(dfs) > 1 else dfs[0]
        else:
            st.warning(f"No {model_name} bulk prediction data found.")
            return None

    # Handle file type selection
    if selected_file_type == 'Single Prediction':
        st.markdown('## Single Prediction')
        st.write(file_descriptions[selected_file_type])
        st.session_state['df'] = pd.read_sql_query("SELECT * FROM single_predict", conn1, index_col='user_id')

    elif selected_file_type == 'Bulk Prediction':
        st.markdown('## Bulk Prediction')
        st.write(file_descriptions[selected_file_type])

        selected_period = st.selectbox(
            'Select a Period', 
            ['', 'Most Recent', 'Last 3 Predictions', 'Last 5 Predictions', 'Last 10 Predictions'], 
            index=0
        )
        st.session_state['selected_period'] = selected_period

        # First Row
        col1, col2, col3, col4 = st.columns(4)


        def button_click_handler(model_name):
            st.session_state['model_name'] = model_name
            if selected_period:
                df = load_bulk_prediction(model_name, {'Most Recent': 1, 'Last 3 Predictions': 3, 'Last 5 Predictions': 5, 'Last 10 Predictions': 10}[selected_period])
                if df is not None:
                    st.session_state['df'] = df

        # Load predictions for each model
        with col1:
            if st.button('Random Forest'):
                button_click_handler('random_forest')

        with col2:
            if st.button('K Nearest'):
                button_click_handler('k_nearest')

        with col3:
            if st.button('Feedforward'):
                button_click_handler('feedforward')

        with col4:
            if st.button('All Models'):
                model_names = ['random_forest', 'k_nearest', 'feedforward']
                dfs = []
                for model_name in model_names:
                    df = load_bulk_prediction(model_name, {'Most Recent': 1, 'Last 3 Predictions': 3, 'Last 5 Predictions': 5, 'Last 10 Predictions': 10}[selected_period])
                    if df is not None:
                        dfs.append(df)
                if dfs:
                    st.session_state['df'] = pd.concat(dfs, axis=0)
                    st.info("Loaded bulk predictions for all selected models.")
                else:
                    st.warning('No bulk prediction data found for the selected period.')

    elif selected_file_type == 'Template Prediction':
        st.markdown('## Template Prediction')
        st.write(file_descriptions[selected_file_type])

        # First Row
        col1, col2, col3, col4 = st.columns(4)

        def load_and_randomize_dates(table_name, conn):
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn, index_col='user_id')
            df = randomize_dates(df, 'PredictionTime')
            return df

        with col1:
            if st.button('Random Forest'):
                st.session_state['df'] = load_and_randomize_dates("random_forest_template_predict000000", conn2)

        with col2:
            if st.button('K Nearest'):
                st.session_state['df'] = load_and_randomize_dates("k_nearest_template_predict000000", conn2)

        with col3:
            if st.button('Feedforward'):
                st.session_state['df'] = load_and_randomize_dates("feedforward_template_predict000000", conn2)

        with col4:
            if st.button('All Models'):
                model_names = ['random_forest', 'k_nearest', 'feedforward']
                model_dfs = [load_and_randomize_dates(f"{name}_template_predict000000", conn2) for name in model_names]
                st.session_state['df'] = pd.concat([df for df in model_dfs if df is not None], axis=0)

    # Closing database connections
    conn1.close()
    conn2.close()

    # Check if DataFrame is available and display metrics
    df = st.session_state['df']
    if df is None:
        st.info("Select a model to load the corresponding prediction data.")
        st.stop()
    
    # Prediction Summary

    st.subheader("📊 Prediction Summary")

    # User inputs for past metrics, with values stored in session state
    st.markdown("#### Enter Previous Metrics for Comparison")

    if 'prev_churn_rate' not in st.session_state:
        st.session_state['prev_churn_rate'] = 0.0
    if 'prev_customers_at_risk' not in st.session_state:
        st.session_state['prev_customers_at_risk'] = 0
    if 'prev_revenue_loss' not in st.session_state:
        st.session_state['prev_revenue_loss'] = 0.0

    st.session_state['prev_churn_rate'] = st.number_input(
        "Previous Churn Rate (%)", 
        min_value=0.0, max_value=100.0, value=st.session_state['prev_churn_rate'], step=0.01,
        
    )
    st.session_state['prev_customers_at_risk'] = st.number_input(
        "Previous Customers at Risk", 
        min_value=0, value=st.session_state['prev_customers_at_risk'], step=1,
        
    )
    st.session_state['prev_revenue_loss'] = st.number_input(
        "Previous Predicted Revenue Loss (CFA, M)", 
        min_value=0.0, value=st.session_state['prev_revenue_loss'], step=0.01,
        
    )

    # Key metrics calculations
    if 'Prediction' in df.columns:
        # Calculate predicted churn rate
        churn_rate = df['Prediction'].map({'Yes': 1, 'No': 0}).mean() * 100
        churn_rate_delta = churn_rate - st.session_state['prev_churn_rate']

        # Calculate the number of customers at risk of churning
        customers_at_risk = df['Prediction'].map({'Yes': 1, 'No': 0}).sum()
        customers_at_risk_delta = customers_at_risk - st.session_state['prev_customers_at_risk']

        # Calculate predicted revenue loss
        if 'MONTANT' in df.columns:
            revenue_loss_raw = df.loc[df['Prediction'] == 'Yes', 'MONTANT'].sum()  
            
            # Check if revenue loss is less than a million
            if revenue_loss_raw >= 1e6:
                revenue_loss = revenue_loss_raw / 1e6  
                revenue_display = f"CFA {revenue_loss:.2f}M"  
            else:
                revenue_loss = revenue_loss_raw 
                revenue_display = f"CFA {revenue_loss:.2f}"  
        else:
            revenue_loss = "N/A"
            revenue_display = "N/A"

        # Calculate delta if revenue_loss is not "N/A"
        revenue_loss_delta = revenue_loss - st.session_state['prev_revenue_loss'] if revenue_loss != "N/A" else "N/A"

        # Update the display for delta depending on whether it's in millions or not
        if revenue_loss_delta != "N/A":
            if revenue_loss_raw >= 1e6:
                revenue_loss_delta_display = f"CFA {revenue_loss_delta:.2f}M"
            else:
                revenue_loss_delta_display = f"CFA {revenue_loss_delta:.2f}"
        else:
            revenue_loss_delta_display = "N/A"

        # Display key metrics 
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Predicted Churn Rate", 
            f"{churn_rate:.2f}%", 
            delta=f"{churn_rate_delta:.2f}%",
            delta_color="inverse",
            help="The delta indicates how much the predicted churn rate has changed compared to the previous churn rate you entered."
        )
        col2.metric(
            "Customers at Risk", 
            f"{customers_at_risk}", 
            delta=f"{customers_at_risk_delta}",
            help="The delta shows the change in the number of customers predicted to churn compared to the previous number of customers that churned."
        )
        col3.metric(
            "Predicted Revenue Loss", 
            revenue_display, 
            delta=revenue_loss_delta_display,  
            help="The delta reflects the difference in predicted revenue loss due to churn compared to your previous estimate."
        )

        # Display Churn Rate Gauge        
        fig_churn_rate = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=churn_rate,
            number={'suffix': "%", 'valueformat': ".2f"},
            title={'text': "Churn Rate"},
            gauge={
                "axis": {"range": [0, 100], "tickformat": ".2f%"},
                "bar": {"color": "blue"},
                "steps": [
                    {"range": [0, 30], "color": "green"},
                    {"range": [30, 70], "color": "yellow"},
                    {"range": [70, 100], "color": "red"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": churn_rate
                }
            },
            delta={
                'reference': churn_rate_delta,
                'relative': True, 
                'position': "top", 
                'valueformat': ".2f",
                'suffix': "%",  
                'increasing': {'color': "red"}, 
                'decreasing': {'color': "green"}
            }  
        ))
        st.plotly_chart(fig_churn_rate, use_container_width=True)

        # Description for the gauge
        st.markdown("""
        **Churn Rate Gauge:** This gauge displays the current predicted churn rate along with the percentage change (delta) compared to the previous churn rate you entered. It helps visualize how the churn rate has changed after applying the selected filters.

        - **Positive Delta (in red):** Indicates that the churn rate has increased after filtering, meaning more customers are leaving.
        - **Negative Delta (in green):** Indicates that the churn rate has decreased after filtering, meaning fewer customers are leaving.

        In simpler terms, the gauge shows not just the current churn rate but also how the current rate compares to the rate before you applied the filters. 
        For example, if the churn rate was 10% before filtering and now it’s 15%, a positive delta of 50% would show that the churn rate increased by half relative to the initial rate. 
        The gauge provides insights into whether customer retention has improved or worsened after applying your filters.
        """)
    else:
        st.warning("The 'Prediction' column is not available in the dataset.")

    
    # Conditional Date Range Filter
    date_filter_applicable = False
    if 'PredictionTime' in df.columns:
        df['PredictionTime'] = pd.to_datetime(df['PredictionTime'])
        unique_dates = df['PredictionTime'].dt.date.nunique()
        
        if selected_file_type == 'Single Prediction' or unique_dates > 1:
            date_filter_applicable = True
    
    if date_filter_applicable:
        st.sidebar.subheader("📅 Date Range Filter")
        min_date = df['PredictionTime'].dt.date.min()
        max_date = df['PredictionTime'].dt.date.max()
        start_date, end_date = st.sidebar.date_input(
            "Select Date Range:",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        if start_date > end_date:
            st.error("Start date must be before end date.")
            st.stop()
        
        df = df[(df['PredictionTime'].dt.date >= start_date) & (df['PredictionTime'].dt.date <= end_date)]
    
    # Numerical and Categorical Filters

    st.sidebar.subheader("🎛️ Data Filters")
    
    # Numerical Filters
    numerical_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    for column in numerical_columns:
        min_value = float(df[column].min())
        max_value = float(df[column].max())
        step = (max_value - min_value) / 100 if max_value != min_value else 0.10
        selected_range = st.sidebar.slider(
            f"{column}",
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
            step=step
        )
        df = df[df[column].between(selected_range[0], selected_range[1])]
    
    # Categorical Filters
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    for column in categorical_columns:
        unique_values = df[column].dropna().unique().tolist()
        if unique_values:
            selected_values = st.sidebar.multiselect(
                f"{column}",
                options=unique_values,
                default=unique_values
            )
            if selected_values:
                df = df[df[column].isin(selected_values)]
    
    # Display Filtered Data
    st.subheader("🔍 Filtered Data Preview")
    st.dataframe(df.head(50))
    st.write(f"Total Records: {df.shape[0]}")

    with st.expander("⬇️ Download Data", expanded=False):
        st.write(
            """
            Download the dataset in its currently displayed state, irrespective of any applied filters, 
            in various formats beyond the default CSV for comprehensive analysis or distribution.
            Available formats for download include: Excel, Stata, HTML, and JSON.
            """
        )
        generate_download_buttons(df)

    
    if df.empty:
        st.warning("No data available after applying filters.")
        st.stop()
    
    # Visualization Section
    st.subheader("📈 Data Visualizations")
    
    # Time-based Probability Trends
    if 'PredictionTime' in df.columns and 'Probability' in df.columns and 'Prediction' in df.columns:
        # Determine time aggregation level
        df['Year'] = df['PredictionTime'].dt.year
        df['Month'] = df['PredictionTime'].dt.to_period('M')
        df['Day'] = df['PredictionTime'].dt.date
        
        time_aggregation = 'Day'
        if df['Year'].nunique() > 1:
            time_aggregation = st.selectbox(
                "Select Time Aggregation Level:",
                options=['Year', 'Month', 'Day'],
                index=1
            )
        
        agg_column = time_aggregation
        
        # Aggregate data
        pagg_df = df.groupby(agg_column)['Probability'].mean().reset_index()        
        agg_df = df.groupby([agg_column, 'Predicted Churn'])['Probability'].mean().reset_index()
        
        # Line Chart for Probability Trends
        line_fig1 = px.line(
            pagg_df,
            x=agg_column,
            y='Probability',
            title="Overall Churn Probability Trends Over Time",
            markers=False
        )

        line_fig2 = px.line(
            agg_df,
            x=agg_column,
            y='Probability',
            color='Predicted Churn',
            title="Churn Probability Trends by Outcome Over Time",
            markers=False
        )

        line_fig2.update_layout(legend_title_text='Churn Outcome')

        # Donut Chart for Churn Proportion
        churn_counts = df['Predicted Churn'].value_counts().reset_index()
        churn_counts.columns = ['Predicted Churn', 'Count']
        donut_fig = px.pie(
            churn_counts,
            values='Count',
            names='Predicted Churn',
            hole=0.3,
            title="Churn Proportion",
            color='Predicted Churn',
            color_discrete_map={
                'No Churn': 'green',    
                'Churn': 'red'  
            }
        )

        
        # Display line charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(line_fig1, use_container_width=True)
        with col2:
            st.plotly_chart(line_fig2, use_container_width=True)

        # Display donut chart
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            st.plotly_chart(donut_fig, use_container_width=True)
    else:
        st.warning("Required columns for visualization ('PredictionTime', 'Probability', 'Prediction') are not available.")
    
    # Model Performance Analysis
    if 'ModelUsed' in df.columns and 'Probability' in df.columns:
        st.subheader("🤖 Model Performance Analysis")
        
        # Average Probability per Model
        model_performance = df.groupby('ModelUsed')['Probability'].mean().reset_index()
        bar_fig = px.bar(
            model_performance,
            x='ModelUsed',
            y='Probability',
            color='ModelUsed',
            title="Average Churn Probability per Model",
            labels={'Probability': 'Average Probability'},
            color_discrete_sequence=px.colors.qualitative.Dark2
        )

        # Churn Rate per Model
        churn_rate_per_model = df.groupby('ModelUsed')['Prediction'].apply(lambda x: (x == 'Yes').mean() * 100).reset_index()
        churn_rate_per_model.columns = ['ModelUsed', 'ChurnRate']

        # Plot the churn rate per model using the RdYlGn_r color scale
        churn_rate_fig = px.bar(
            churn_rate_per_model,
            x='ModelUsed',
            y='ChurnRate',
            color='ChurnRate',
            title="Churn Rate per Model",
            labels={'ChurnRate': 'Churn Rate (%)'},
            color_continuous_scale='RdYlGn_r',  
            range_color=[0, 100]  
        )

        # Update color bar for better context (optional)
        churn_rate_fig.update_coloraxes(colorbar_title="Churn Rate (%)")


        if df['ModelUsed'].nunique() == 1:
            col_center = st.columns([1, 4, 1])

            with col_center[1]:
                st.plotly_chart(bar_fig, use_container_width=True)

        else:
            # Display bar charts
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(bar_fig, use_container_width=True)
            with col2:
                st.plotly_chart(churn_rate_fig, use_container_width=True)
                avg_churn_rate = churn_rate_per_model['ChurnRate'].mean()
                st.info(f"**Average Churn Rate across models:** {avg_churn_rate:.2f}%")
    
    
    # Display detailed analysis if there is more than one unique model
    if df['ModelUsed'].nunique() > 1:
        st.subheader("📊 Detailed Analysis for Each Model")
        models = df['ModelUsed'].unique()
        
        for model in models:
            st.write(f"### Model: {model}")
            model_df = df[df['ModelUsed'] == model]
            
            # Line Chart for Model Probability Trends
            if 'PredictionTime' in model_df.columns and 'Probability' in model_df.columns and 'Prediction' in model_df.columns:
                model_pagg_df = model_df.groupby(agg_column)['Probability'].mean().reset_index()
                model_agg_df = model_df.groupby([agg_column, 'Predicted Churn'])['Probability'].mean().reset_index()
                
                model_line_fig1 = px.line(
                    model_pagg_df,
                    x=agg_column,
                    y='Probability',
                    title=f"Churn Probability Trends Over Time for {model}",
                    markers=False
                )
                model_line_fig1.update_layout(legend_title_text='Churn Outcome')
                
                model_line_fig2 = px.line(
                    model_agg_df,
                    x=agg_column,
                    y='Probability',
                    color='Predicted Churn',
                    title=f"Churn Probability Trends Over Time for {model}",
                    markers=False
                )
                model_line_fig2.update_layout(legend_title_text='Churn Outcome')
                
                # Donut Chart for Model Churn Proportion
                model_churn_counts = model_df['Predicted Churn'].value_counts().reset_index()
                model_churn_counts.columns = ['Predicted Churn', 'Count']
                model_donut_fig = px.pie(
                    model_churn_counts,
                    values='Count',
                    names='Predicted Churn',
                    hole=0.5,
                    title=f"Churn Proportion for {model}",
                    color='Predicted Churn',
                    color_discrete_map={
                        'No Churn': 'green',    
                        'Churn': 'red'  
                    }
                )

                # Display line charts
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(model_line_fig1, use_container_width=True)
                with col2:
                    st.plotly_chart(model_line_fig2, use_container_width=True)

                # Display donut chart
                col_center = st.columns([1, 2, 1])
                with col_center[1]:
                    st.plotly_chart(model_donut_fig, use_container_width=True)
            else:
                st.warning(f"Required columns for visualization are not available for model {model}.")
    else:
        st.info("Detailed analysis is not available as there is only one model used in the data.")
else:
    st.warning("Please log in to access and view past predictions.")
    

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