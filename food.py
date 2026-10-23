import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


st.set_page_config(
    page_title="Food Delivery Analytics Dashboard",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_sample_data():
    np.random.seed(42)
    n_rows = 1000
    dates = pd.date_range(start="2026-01-01", periods=n_rows, freq="h")
    cities = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad']
    cuisines = ['North Indian', 'South Indian', 'Chinese', 'Italian', 'Biryani', 'Fast Food']
    statuses = ['Delivered', 'Delivered', 'Delivered', 'Delivered', 'Cancelled']
    
    data = {
        'Order_ID': [f'ORD-{1000 + i}' for i in range(n_rows)],
        'Order_Date': np.random.choice(dates, n_rows),
        'City': np.random.choice(cities, n_rows),
        'Cuisine_Type': np.random.choice(cuisines, n_rows),
        'Final_Amount': np.random.normal(loc=450, scale=150, size=n_rows).round(2),
        'Cost_Price': np.random.normal(loc=300, scale=100, size=n_rows).round(2),  # Cost field
        'Delivery_Time_Min': np.random.normal(loc=35, scale=10, size=n_rows).round(1),
        'Delivery_Rating': np.random.choice([1, 2, 3, 4, 5], n_rows, p=[0.05, 0.05, 0.1, 0.3, 0.5]),
        'Order_Status': np.random.choice(statuses, n_rows)
    }
    df = pd.DataFrame(data)
    df['Final_Amount'] = df['Final_Amount'].clip(lower=100)
    df['Cost_Price'] = (df['Final_Amount'] * 0.65).round(2)  # Proxy cost if missing
    df['Delivery_Time_Min'] = df['Delivery_Time_Min'].clip(lower=15)
    return df


st.sidebar.title("📌 Dashboard Controls")
uploaded_file = st.sidebar.file_uploader("Upload Orders CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'Order_Date' in df.columns:
        df['Order_Date'] = pd.to_datetime(df['Order_Date'])
else:
    df = load_sample_data()


if 'Cost_Price' not in df.columns and 'Final_Amount' in df.columns:
   
    df['Cost_Price'] = df['Final_Amount'] * 0.70


cities_list = ['All'] + list(df['City'].unique())
selected_city = st.sidebar.selectbox("Filter by City", cities_list)

cuisines_list = ['All'] + list(df['Cuisine_Type'].unique())
selected_cuisine = st.sidebar.selectbox("Filter by Cuisine", cuisines_list)


filtered_df = df.copy()
if selected_city != 'All':
    filtered_df = filtered_df[filtered_df['City'] == selected_city]
if selected_cuisine != 'All':
    filtered_df = filtered_df[filtered_df['Cuisine_Type'] == selected_cuisine]


delivered_df = filtered_df[filtered_df['Order_Status'].str.lower() != 'cancelled']


st.title("🍕 Food Delivery Performance Dashboard")
st.markdown("Executive summary of operational performance, logistics speed, customer sentiment, and profit margins.")
st.markdown("---")


total_orders = len(filtered_df)
total_revenue = delivered_df['Final_Amount'].sum() if not delivered_df.empty else 0.0
total_cost = delivered_df['Cost_Price'].sum() if not delivered_df.empty else 0.0
total_profit = total_revenue - total_cost

profit_margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
avg_order_value = delivered_df['Final_Amount'].mean() if not delivered_df.empty else 0.0
avg_delivery_time = filtered_df['Delivery_Time_Min'].mean()

cancelled_orders = (filtered_df['Order_Status'].str.lower() == 'cancelled').sum()
cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0.0

avg_delivery_rating = filtered_df['Delivery_Rating'].dropna().mean()


kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6, kpi_col7 = st.columns(7)

with kpi_col1:
    st.metric(label="📦 Total Orders", value=f"{total_orders:,}")

with kpi_col2:
    st.metric(label="💰 Total Revenue", value=f"₹{total_revenue:,.2f}")

with kpi_col3:
    st.metric(label="🛍️ Avg Order Value", value=f"₹{avg_order_value:.2f}" if not np.isnan(avg_order_value) else "₹0.00")

with kpi_col4:
    st.metric(label="⏱️ Avg Delivery Time", value=f"{avg_delivery_time:.1f} m" if not np.isnan(avg_delivery_time) else "0 m")

with kpi_col5:
    st.metric(label="❌ Cancellation Rate", value=f"{cancellation_rate:.2f}%")

with kpi_col6:
    st.metric(label="⭐ Avg Rating", value=f"{avg_delivery_rating:.2f}" if not np.isnan(avg_delivery_rating) else "0.0")

with kpi_col7:
    st.metric(label="📈 Profit Margin %", value=f"{profit_margin_pct:.2f}%")

st.markdown("---")


chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Revenue & Profit Trend")
    if 'Order_Date' in filtered_df.columns:
        daily_df = delivered_df.resample('D', on='Order_Date').agg(
            Revenue=('Final_Amount', 'sum'),
            Cost=('Cost_Price', 'sum')
        ).reset_index()
        daily_df['Profit'] = daily_df['Revenue'] - daily_df['Cost']
        
        fig_financials = px.line(
            daily_df, 
            x='Order_Date', 
            y=['Revenue', 'Profit'], 
            title="Daily Revenue vs. Profit Trend",
            labels={'Order_Date': 'Date', 'value': 'Amount (₹)', 'variable': 'Metric'},
            line_shape='spline',
            color_discrete_map={'Revenue': '#27ae60', 'Profit': '#2980b9'}
        )
        st.plotly_chart(fig_financials, use_container_width=True)

with chart_col2:
    st.subheader("🏙️ City Performance & Margin Breakdown")
    city_summary = delivered_df.groupby('City').agg(
        Revenue=('Final_Amount', 'sum'),
        Cost=('Cost_Price', 'sum')
    ).reset_index()
    city_summary['Profit_Margin_%'] = ((city_summary['Revenue'] - city_summary['Cost']) / city_summary['Revenue'] * 100).round(2)
    
    fig_city_margin = px.bar(
        city_summary, 
        x='City', 
        y='Profit_Margin_%', 
        color='Profit_Margin_%',
        title="Profit Margin % by City",
        labels={'Profit_Margin_%': 'Profit Margin (%)'},
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_city_margin, use_container_width=True)


st.subheader("📋 Order Dataset Preview")
st.dataframe(filtered_df.head(50), use_container_width=True)