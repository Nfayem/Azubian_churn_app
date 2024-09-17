# Standard library imports
import base64
import os
import sqlite3

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
from sklearn.impute import SimpleImputer
import plotly.express as px
import plotly.graph_objects as go

# Local application imports
from utils.login import invoke_login_widget
from utils.lottie import display_lottie_on_page


# Invoke the login form
invoke_login_widget('Analytics Dashboard')

# Fetch the authenticator from session state
authenticator = st.session_state.get('authenticator')

# Ensure the authenticator is available
if not authenticator:
    st.error("Authenticator not found. Please check the configuration.")
    st.stop()

# Check authentication status
if st.session_state.get("authentication_status"):
    username = st.session_state['username']
    st.title('Telco Churn Analysis')
    st.write("---")

    # Page Introdution
    with st.container():        
        left_column, right_column = st.columns(2)
        with left_column:
            st.write("""
            Welcome to the **Telco Churn Analysis** dashboard. This page is designed to provide a comprehensive exploration of customer churn through the following analyses:

            1. **Exploratory Data Analysis (EDA):** Investigate customer data through visualizations to uncover trends and patterns related to customer demographics, engagement, and churn factors.
            2. **Key Performance Indicators (KPIs):** Review essential metrics such as total customers, retention rates, revenue, and churn rate, with interactive filters to analyze their impact on business performance.

            Select an analysis type from the dropdown menu to begin exploring data and derive actionable insights to enhance customer retention strategies and drive growth.
            """)
        with right_column:
            display_lottie_on_page("Analytics Dashboard")

    # Add selectbox to choose between EDA and KPIs
    selected_analysis = st.selectbox('Select Analysis Type', ['', '🔍 Exploratory Data Analysis (EDA)', '📊 Key Performance Indicators (KPIs)'], index=0)
    
    # Load the initial data from a local file
    @st.cache_data(persist=True, show_spinner=False)
    def load_initial_data():
        df = pd.read_csv('./data/CAP_template.csv')
        return df
    
    initial_df = load_initial_data()

    # Ensure 'data_source' is initialized in session state
    if 'data_source' not in st.session_state:
        st.session_state['data_source'] = 'initial'  

    # Function to load the most recent table from the user's SQLite database
    def load_most_recent_table(username):
        # Define the path for the user's SQLite database
        db_path = f"./data/{username}/{username}.db"

        if not os.path.exists(db_path):
            st.error("No database found for the user. Please ensure a file has been uploaded on the data overview page.")
            return None, None

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)

        # Get the most recent table name
        tables_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table'
        AND name LIKE ?
        ORDER BY tbl_name DESC LIMIT 1;
        """
        try:
            tables = conn.execute(tables_query, (f'{username}%',)).fetchall()
            most_recent_table = [table[0] for table in tables]

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

    # User interface for selecting the dataset
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Template Dataset"):
            st.session_state['data_source'] = 'initial'

    with col2:
        if st.button("Uploaded Dataset"):
            st.session_state['data_source'] = 'uploaded'

    # Load the appropriate dataset based on the user's choice
    if st.session_state['data_source'] == 'initial':
        df = initial_df
        table_name = "Template Dataset"
    else:
        uploaded_df, table_name = load_most_recent_table(username)
        df = uploaded_df if uploaded_df is not None else initial_df

    # Display the dataset currently in use
    st.write(f"Using dataset: {table_name}")

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

    # Check if there are any missing values in the 'CHURN' column
    if df['CHURN'].isna().sum() > 0:
        # Impute missing values in 'CHURN' using the most frequent value (mode)
        churn_imputer = SimpleImputer(strategy='most_frequent')
        df['CHURN'] = churn_imputer.fit_transform(df[['CHURN']]).flatten()

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
        st.stop() 
       
    # Handle missing values
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    int64_columns = df.select_dtypes(include=['int64']).columns.tolist()

    # Impute numerical columns with median
    numerical_imputer = SimpleImputer(strategy='median')
    df[numerical_columns] = numerical_imputer.fit_transform(df[numerical_columns])

    # Convert columns that were originally int64 back to int64
    for column in int64_columns:
        df[column] = df[column].astype('int64')


    # Create a function to apply filters
    def apply_filters(df):
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

        filtered_data = df.copy()
        for column, (min_val, max_val) in slider_values.items():
            filtered_data = filtered_data[
                (filtered_data[column] >= min_val) & (filtered_data[column] <= max_val)
            ]
        return filtered_data

    # Apply filters to the data
    filtered_data = apply_filters(df)

    # Exploratory Data Analysis
    if selected_analysis == '':
        st.write("Please select an analysis type to begin.")

    elif selected_analysis == '🔍 Exploratory Data Analysis (EDA)':
        st.subheader("🕵🏾‍♂️ Churn EDA Dashboard")
        st.write(
            """This dashboard provides an exploratory analysis of customer churn data, 
            focusing on customer demographics, engagement patterns, and key metrics. 
            By examining various attributes such as location, top-up amounts, and usage patterns, 
            this analysis helps identify factors influencing customer retention and churn. 
            The visualizations highlight significant trends and correlations to support strategic decision-making."""
        )
        
        # Customer Information Analysis
        st.markdown("#### Customer Information Analysis")
        st.write("""
        This section analyzes customer demographics, focusing on key attributes such as location 
        and their potential influence on customer retention and acquisition.
        """)

        with st.container():
            col_center = st.columns([1, 6, 1])

            with col_center[1]:
                region_plot = px.histogram(df, x="REGION", color="CHURN", barmode="group", title="Region Distribution")
                region_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(region_plot, use_container_width=False)
        
        # Customer Engagement Analysis
        st.markdown("#### Customer Engagement Analysis")
        st.write("""
        This section explores various customer account characteristics, and usage patterns
        such as top-up amounts, recharge frequency, tenure, and top packs. These metrics provide deeper insights 
        into customer spending, activity levels, and retention patterns.
        """)

        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                top_up_plot = px.histogram(df, x='MONTANT', nbins=20, color='CHURN', title='Top-Up Amount Distribution')
                top_up_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(top_up_plot, use_container_width=True)

            with col2:
                recharge_plot = px.histogram(df, x='FREQUENCE_RECH', nbins=20, color='CHURN', title='Recharge Frequency Distribution')
                recharge_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(recharge_plot, use_container_width=True)

        with st.container():
            # Define the correct order of tenure categories
            tenure_order = ['D 3-6 month', 'E 6-9 month', 'F 9-12 month', 'G 12-15 month', 
                'H 15-18 month', 'I 18-21 month', 'J 21-24 month', 'K > 24 month']
            
            col1, col2 = st.columns(2)
            with col1:
                regularity_plot = px.histogram(df, x='REGULARITY', nbins=20, color='CHURN', title='Regularity Distribution')
                regularity_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(regularity_plot, use_container_width=True)

            with col2:
                tenure_plot = px.histogram(df, x="TENURE", color="CHURN", barmode="group", title="Tenure Distribution", category_orders={"TENURE": tenure_order})
                tenure_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(tenure_plot, use_container_width=True)

        with st.container():
            
            col_center = st.columns([1, 6, 1])

            with col_center[1]:
                top_pack_plot = px.histogram(df, x="TOP_PACK", color="CHURN", barmode="group", title="Top Packages Distribution")
                top_pack_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(top_pack_plot, use_container_width=True)

        # Correlation and Pair Plot Analysis
        st.markdown("#### Correlation and Pair Plot Analysis")
        st.write(
            "This section investigates the relationships between key numerical features. The correlation heatmap highlights how features correlate with each other, while the pair plot provides a visual exploration of feature interactions."
        )

        with st.container():
            filtered_data['CHURN'] = filtered_data['CHURN'].map({'Yes': 1, 'No': 0})
            col1, col2 = st.columns(2)

            with col1:
                # Correlation Heatmap
                corr_features = ["CHURN", "MONTANT", "FREQUENCE_RECH", "REGULARITY", "DATA_VOLUME", "TIGO", "ORANGE", "REVENUE", "ARPU_SEGMENT", "FREQUENCE"]
                corr_matrix = filtered_data[corr_features].dropna().corr()

                # Annotate the heatmap with correlation values
                heatmap = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale="RdBu",
                    text=corr_matrix.values,  
                    texttemplate="%{text:.2f}",  
                    showscale=True  
                ))

                heatmap.update_layout(
                    title="Correlation Matrix",
                    xaxis_nticks=36
                )

                st.plotly_chart(heatmap)
            
            with col2:
                filtered_data['CHURN'] = filtered_data['CHURN'].map({1: 'Yes', 0: 'No'}).fillna('Unknown')
                # Pair Plot
                pairplot_features = ["CHURN", "MONTANT", "REGULARITY", "REVENUE"]
                pairplot_fig = px.scatter_matrix(
                    filtered_data[pairplot_features],
                    dimensions=["MONTANT", "REGULARITY", "REVENUE"],
                    color="CHURN",
                    title="Pairplot"
                )
                st.plotly_chart(pairplot_fig)

        # Key Business Insights for template dataset
        if st.session_state['data_source'] == 'initial':
            st.markdown("""
            #### Key Business Insights
                        
            ##### 1. **Regional Impact on Churn:**
            - **Dakar** has the highest concentration of customers, but there is a significant number of churners compared to other regions.
            - **Matam**, **Thies**, and **Diourbel** also have noticeable churn activity, but their overall customer base is much smaller compared to Dakar.
            - **Insight**: Marketing and retention strategies should prioritize Dakar, focusing on understanding why customers in that region are more likely to churn. 
                A tailored approach may help reduce churn, especially for regions with a higher customer concentration.

            #####  2. **Customer Engagement Patterns:**
            - **Top-Up Amount (MONTANT)**: A vast majority of customers have low top-up amounts, but even customers with high top-ups still churn, indicating that higher spending doesn't guarantee loyalty.
            - **Recharge Frequency (FREQUENCE_RECH)**: Most customers have lower recharge frequencies, and there seems to be a trend that low-frequency rechargers are more likely to churn.
            - **Regularity**: Customers who show more consistent usage (higher regularity) are less likely to churn. Churn is more prevalent among customers with irregular usage patterns.
            - **Insight**: Implementing reward-based programs for high top-up users and providing more incentives to low-frequency rechargers could reduce churn. 
                Additionally, encouraging consistent usage through promotions or loyalty programs may improve customer retention.

            ##### 3. **Top Pack Usage:**
            - **Voice Packages** are the most popular, but churn occurs even among customers using this pack frequently. Other packs such as **Data** and **PVR** packs have a relatively lower customer base, but churn behavior is still present.
            - **Insight**: While Voice Packs dominate, it would be valuable to investigate if customers using them are receiving the full benefits. Adding value to these packs (e.g., better data offers) might retain customers. 
                Focusing on customers with lower pack engagement (e.g., Data, PVR) and improving the appeal of these packs could reduce churn.

            ##### 4. **Tenure and Churn:**
            - There is a strong concentration of churn within customers who have been with the service for **less than 6 months**, suggesting that early disengagement is a major issue. Customers with longer tenures (e.g., 12 months or more) are less likely to churn.
            - **Insight**: Onboarding and customer education within the first few months is critical. Improving initial customer engagement, offering better welcome packages, or providing guidance on how to maximize value from the service could reduce early churn.

            ##### 5. **Correlation and Feature Relationships:**
            - **Correlation Matrix**: The churn correlation with **top-up amount (MONTANT)** and **frequency of recharge (FREQUENCE_RECH)** is weak, indicating that churn is not directly tied to these specific numerical factors.
            - **Regularity** shows a fair correlation, suggesting that customers with higher regularity are more engaged and less likely to churn.
            - **Insight**: Since the correlation with churn is not strong for numerical variables like MONTANT and FREQUENCE_RECH, the focus should be on qualitative factors (e.g., satisfaction, service quality) and customer engagement (Regularity). 
                Better understanding of customer behaviors beyond transactions might help identify churn triggers.

            ##### Overall Recommendations:
            - **Focus on Early Retention**: Customers tend to churn within the first 3 months, so efforts should be directed at improving the early customer experience.
            - **Tailor Regional Strategies**: Dakar requires targeted campaigns to reduce churn, and understanding the unique challenges of different regions could help localize marketing efforts.
            - **Engagement Incentives**: Implement loyalty programs that reward consistent activity, especially for customers with lower regularity and top-up amounts.
            - **Pack Optimization**: Review the value of the top packages, especially voice packages, to ensure that they meet customer expectations and prevent churn.
                """)

    # Key Performance Indicators
    elif selected_analysis == '📊 Key Performance Indicators (KPIs)':
        st.subheader("📈 Churn KPI Dashboard")

        st.markdown("""
        This dashboard provides key performance indicators (KPIs) related to customer churn. It offers insights into:

        - **Total Customers:** Number of customers after applying filters.
        - **Total Customers Retained:** Number of customers retained, showing changes after filtering.
        - **Average Monthly Income:** Changes in the average income of customers.
        - **Total Revenue:** How total revenue of the company has shifted with applied filters.
        - **Churn Rate Gauge:** Visual representation of churn rate changes relative to the unfiltered data.

        Use this dashboard to analyze the impact of various filters on customer retention and overall business metrics.
        """)

        # Apply a map to the data frame for the chun column
        df['CHURN'] = df['CHURN'].map({'Yes': 1, 'No': 0})
        filtered_data['CHURN'] = filtered_data['CHURN'].map({'Yes': 1, 'No': 0})
  
        # Calculate unfiltered values
        unfiltered_total_customers = df.shape[0]
        unfiltered_total_customers_retained = len(df[df["CHURN"] == 0])
        unfiltered_avg_monthly_income = df['REVENUE'].mean()
        unfiltered_total_revenue = df['MONTANT'].sum()

        # Churn KPI metrics
        with st.container():
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # KPI 1: Total Customers
                total_customers = filtered_data.shape[0]
                total_customers_delta = (total_customers - unfiltered_total_customers) / unfiltered_total_customers * 100
                st.metric(
                    label="Total Customers", 
                    value=f"{total_customers:,}", 
                    delta=f"{total_customers_delta:.2f}%", 
                    help="This percentage shows how the total number of customers has changed after applying the selected filters."
                )

            with col2:
                # KPI 2: Total Customers Retained
                total_customers_retained = len(filtered_data[filtered_data["CHURN"] == 0])
                total_customers_retained_delta = (total_customers_retained - unfiltered_total_customers_retained) / unfiltered_total_customers_retained * 100
                st.metric(
                    label="Total Customers Retained", 
                    value=f"{total_customers_retained:,}", 
                    delta=f"{total_customers_retained_delta:.2f}%",
                    help="This percentage shows the change in the number of customers retained after applying the selected filters."
                )

            with col3:
                # KPI 3: Average Monthly Income
                avg_monthly_income = filtered_data['REVENUE'].mean()
                avg_monthly_income_delta = (avg_monthly_income - unfiltered_avg_monthly_income) / unfiltered_avg_monthly_income * 100
                st.metric(
                    label="Avg. Monthly Income", 
                    value=f"CFA {avg_monthly_income:.2f}", 
                    delta=f"{avg_monthly_income_delta:.2f}%",
                    help="This percentage indicates how average monthly income of clients have changed after applying the selected filters."
                )

            with col4:
                # KPI 4: Total Revenue
                total_revenue = filtered_data['MONTANT'].sum()
                total_revenue_delta = (total_revenue - unfiltered_total_revenue) / unfiltered_total_revenue * 100
                st.metric(
                    label="Total Revenue", 
                    value=f"CFA {total_revenue/1e6:,.2f}M", 
                    delta=f"{total_revenue_delta:.2f}%",
                    help="This percentage shows how total revenue has shifted after applying the selected filters."
                )

        # KPI 6: Churn Rate Gauge
        churn_rate = filtered_data['CHURN'].mean() * 100
        unfiltered_churn_rate = df['CHURN'].mean() * 100

        fig_churn_rate = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=churn_rate,
            number={'suffix': "%", 'valueformat': ".2f"},
            delta={
                'reference': unfiltered_churn_rate, 
                'relative': True, 
                'position': "top", 
                'valueformat': ".2f",
                'suffix': "%",  
                'increasing': {'color': "red"}, 
                'decreasing': {'color': "green"}  
            },
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
            }
        ))

        st.plotly_chart(fig_churn_rate)

        # Display a description or Chunn Rate Gauge
        st.markdown("""
        **Churn Rate Gauge:** This gauge shows the churn rate based on the filtered dataset, reflecting any adjustments made.

        - **Positive Delta (in red):** Indicates that the churn rate has increased after filtering, meaning more customers are leaving.
        - **Negative Delta (in green):** Indicates that the churn rate has decreased after filtering, meaning fewer customers are leaving.

        In simpler terms, the gauge shows not just the current churn rate but also how the current rate compares to the rate before you applied the filters. 
        For example, if the churn rate was 10% before filtering and now it’s 15%, a positive delta of 50% would show that the churn rate increased by half relative to the initial rate. 
        The gauge provides insights into whether customer retention has improved or worsened after applying your filters.
        """)

        # Insights into Churn by Key Metrics
        st.markdown("#### Insights into Churn by Key Metrics")
        st.markdown("""
        This section explores key factors influencing churn:
        - **Churn Rates by Region:** Examines how churn varies across different regions.
        - **Churn Trends by Customer Tenure:** Illustrates how churn rates change with the length of customer tenure.
        - **Impact of Service Usage on Churn:** Evaluates the relationship between customer churn and their usage patterns, including calls made within the company’s network (ON_NET), calls to competitive providers (ORANGE, TIGO), and data consumption (DATA_VOLUME).
        """)

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Plot: Churn Rate by Region
                churn_by_region = filtered_data.groupby('REGION')['CHURN'].mean().reset_index()
                churn_by_region['Churn'] = churn_by_region['CHURN'] * 100
                fig_region_churn = px.bar(churn_by_region, x='REGION', y='CHURN', title='Churn Rate by Region')
                st.plotly_chart(fig_region_churn, use_container_width=True)

            with col2:
                # Plot: Churn Rate Over Tenure
                churn_rate_by_tenure = filtered_data.groupby('TENURE')['CHURN'].mean().reset_index()
                fig_churn_tenure = px.line(churn_rate_by_tenure, x='TENURE', y='CHURN', title='Churn Rate Over Tenure')
                st.plotly_chart(fig_churn_tenure, use_container_width=True)

        # Apply a map to the data frame for the chun column
        filtered_data['CHURN'] = filtered_data['CHURN'].map({1:'Yes', 0:'No'})

        # Define the numerical features and categorize them
        call_data_features = ['ON_NET', 'ORANGE', 'TIGO', 'DATA_VOLUME']

        # Function to categorize features based on quantiles
        def categorize_feature(df, feature):
            low_thresh = df[feature].quantile(0.33)
            high_thresh = df[feature].quantile(0.67)
            
            # Ensure that the thresholds are unique
            if low_thresh == high_thresh:
                high_thresh += 1e-5  # Add a small value to make them unique
            
            df[f'{feature}_category'] = pd.cut(df[feature],
                                            bins=[-np.inf, low_thresh, high_thresh, np.inf],
                                            labels=['Low', 'Medium', 'High'],
                                            duplicates='drop')

        # Assuming df is your DataFrame
        for feature in call_data_features:
            categorize_feature(filtered_data, feature)

        # Create a container and columns for the plots
        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Plot for ON_NET Usage
                on_net_plot = px.histogram(filtered_data, x='ON_NET_category', color='CHURN',
                                            title='ON_NET Usage vs. Churn Status',
                                            color_discrete_map={'Yes': 'red', 'No': 'green'})
                on_net_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(on_net_plot, use_container_width=True)

            with col2:
                # Plot for ORANGE Usage
                orange_plot = px.histogram(filtered_data, x='ORANGE_category', color='CHURN',
                                            title='ORANGE Usage vs. Churn Status',
                                            color_discrete_map={'Yes': 'red', 'No': 'green'})
                orange_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(orange_plot, use_container_width=True)

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Plot for TIGO Usage
                tigo_plot = px.histogram(filtered_data, x='TIGO_category', color='CHURN',
                                            title='TIGO Usage vs. Churn Status',
                                            color_discrete_map={'Yes': 'red', 'No': 'green'})
                tigo_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(tigo_plot, use_container_width=True)

            with col2:
                # Plot for DATA_VOLUME Usage
                data_volume_plot = px.histogram(filtered_data, x='DATA_VOLUME_category', color='CHURN',
                                                title='DATA_VOLUME Usage vs. Churn Status',
                                                color_discrete_map={'Yes': 'red', 'No': 'green'})
                data_volume_plot.update_layout(yaxis_title="Customers")
                st.plotly_chart(data_volume_plot, use_container_width=True)

        # Company Revenue and Customer Income Insights
        st.markdown("#### Company Revenue and Customer Income Insights")
        st.markdown("""
        This section provides detailed insights into company revenue and customer income patterns:
        - **Average Monthly Income by Region:** Shows the average income that customers generate per month across different regions.
        - **Average Revenue by Region:** Displays the average revenue earned by the company from customers in each region.
        - **Average Monthly Income by Tenure:** Illustrates how the average monthly income of customers changes with their length of tenure.
        - **Average Revenue by Tenure:** Highlights the average revenue the company earns from customers based on their tenure.
        """)


        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Plot: Average Monthly Income by Region
                avg_income_by_region = filtered_data.groupby('REGION')['REVENUE'].mean().reset_index()
                fig_avg_income_by_region = px.bar(avg_income_by_region, x='REGION', y='REVENUE', title='Avg. Monthly Income by Region')
                st.plotly_chart(fig_avg_income_by_region)

            with col2:
                # Plot: Average Revenue by Region
                total_revenue_by_region = filtered_data.groupby('REGION')['MONTANT'].mean().reset_index()
                fig_total_revenue_by_region = px.bar(total_revenue_by_region, x='REGION', y='MONTANT', title='Avg. Revenue by Region')
                st.plotly_chart(fig_total_revenue_by_region)

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                # Plot: Average Monthly Income by Tenure
                avg_income_by_tenure = filtered_data.groupby('TENURE')['REVENUE'].mean().reset_index()
                fig_avg_income_by_tenure = px.bar(avg_income_by_tenure, x='TENURE', y='REVENUE', title='Avg. Monthly Income by Tenure')
                st.plotly_chart(fig_avg_income_by_tenure)

            with col2:
                # Plot: Average Revenue by Tenure
                total_revenue_by_tenure = filtered_data.groupby('TENURE')['MONTANT'].mean().reset_index()
                fig_total_revenue_by_tenure = px.bar(total_revenue_by_tenure, x='TENURE', y='MONTANT', title='Avg. Revenue by Tenure')
                st.plotly_chart(fig_total_revenue_by_tenure)

        # KPI data
        kpi_data = {
            'KPI': ['Total Customers', 'Total Customers Retained', 'Churn Rate', 'Avg. Monthly Income', 'Total Revenue'],
            'Value': [f"{total_customers:,}", f"{total_customers_retained:,}", f"{churn_rate:.2f}%", f"CFA {avg_monthly_income:.2f}", f"CFA {total_revenue:,.2f}"]
        }

        # Create DataFrame
        kpi_df = pd.DataFrame(kpi_data)
        kpi_df.set_index('KPI', inplace=True)

        # Function to apply conditional formatting based on the value
        def color_kpi_value(value):
            if '%' in value:
                percent_value = float(value.strip('%'))
                if percent_value < 30:
                    color = 'green'
                elif 30 <= percent_value < 70:
                    color = 'yellow'
                else:  
                    color = 'red'
            else:
                color = 'lightblue'
            return f'color: {color}'

        # Function to apply conditional formatting
        def highlight_churn(index):
            color = 'background-color: #4B61F5' if index.name == 'Total Revenue' else ''
            return [color] * len(index)

        # Apply the color_negative_red function to the 'Value' column
        styled_df = kpi_df.style.applymap(color_kpi_value, subset=['Value'])

        # Apply the highlight_churn function to the entire row
        styled_df = styled_df.apply(highlight_churn, axis=1)

        # Display the styled DataFrame
        st.markdown("#### Key Performance Indicators (KPIs)")
        st.table(styled_df)

        # Key Business Insights for template dataset
        if st.session_state['data_source']== "initial":
            st.markdown("""
            #### Key Business Insights
            
            ##### 1. **Overall Churn Rate:**
            - The churn rate is **8.19%**, indicating that nearly one in every twelve customers is leaving the service.
            - **Insight**: While this churn rate is not critically high, it still represents a significant portion of the customer base. 
                Reducing churn by improving retention efforts can help retain a larger customer pool and increase revenue.

            ##### 2. **Churn by Region:**
            - **Dakar** has the highest churn rates, followed by regions like **Sedhiou**, **Diourbel**, and **Kaolack**.
            - **Insight**: Region-specific strategies should be employed to address churn, with a focus on customer retention in Dakar. 
                This could include regional marketing campaigns, improved services, or incentives to retain customers.

            ##### 3. **Churn by Tenure:**
            - Customers with **less than 6 months** of tenure exhibit the highest churn, while churn gradually decreases for customers with longer tenure.
            - **Insight**: Early-stage customer engagement is crucial. It would be beneficial to focus on onboarding processes, early incentives, and customer satisfaction during the first three months to reduce churn among new customers.

            ##### 4. **Impact of Usage on Churn:**
            - **ON_NET Usage**:  Low usage of the company's internal network services (ON_NET) is associated with higher churn rates. 
                This indicates that customers relying more on competing networks may be more likely to leave the service. High ON_NET usage corresponds with reduced churn, as these customers are more engaged with the company’s own network.
            - **Orange and Tigo Usage**: Churn is significantly higher among customers who frequently make calls to competitors like **Orange** and **Tigo**. 
                This suggests that customers who are heavily reliant on external networks may be less loyal and more inclined to switch to those competitors if they perceive better value or service quality.
            - **Data Volume Usage**: Churn is low for both high and low data users but notably higher for medium users.
            - **Insight**: To reduce churn, the company should incentivize ON_NET usage, offer competitive advantages against Orange and Tigo, and create targeted offers for medium data users.

            ##### 5. **Revenue and Income Insights:**
            - **Average Monthly Income by Region**: Customers in **Dakar**, **Saint-Louis**, **Theis**, **Ziguinchor** and **Tambacounda** generate the highest average monthly income.
            - **Average Revenue by Region**: Similarly, the highest revenue is generated from these regions.
            - **Average Monthly Income by Tenure**: Customers who have been with the service for **9-12 months** generate the highest income, while those with very short (less than 3 months) or long tenure (24-27 months) have relatively lower average income.
            - **Average Revenue by Tenure**: Revenue trends match income patterns, peaking between **9-12 months**.
            - **Insight**: While shorter-tenured customers generate less income, those with 9-12 months of tenure show high revenue potential. Focusing on retention during this period could stabilize income streams. 
                Additionally, customers with longer tenure may benefit from loyalty programs to boost their engagement and maintain revenue generation.

            ##### 6. **Key Performance Indicators (KPIs):**
            - **Total Customers**: 15,000 customers, with **13,772 retained**, shows a high retention rate of over 90%.
            - **Total Revenue**: The company’s total revenue is **CFA 74.89M**, and the **average monthly income** per customer is **CFA 5002.22**.
            - **Insight**: The retention rate is relatively strong, but the churn rate still leaves room for improvement. Focused retention efforts could further improve these metrics and increase the revenue per customer.

            ##### Overall Recommendations:
            - **Focus on Early Engagement**: High churn within the first 6 months suggests the need for better onboarding and early customer retention strategies. Offering welcome packages or more personalized services during this period can help.
            - **Region-Specific Campaigns**: Since churn and revenue trends vary by region, targeted marketing and customer engagement campaigns, particularly in **Sedhiou**, **Diourbel**, and **Kaolack** could yield better results.
            - **Increase ON_NET Usage and Target Medium Data Users**: To decrease churn, the company should focus on incentivizing ON_NET usage through attractive packages and loyalty rewards, while offering targeted promotions for medium data users to improve their engagement.
                    """)

else:
    st.warning("Please log in to visualize your data.")
    

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