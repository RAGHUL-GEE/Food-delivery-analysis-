import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


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
        'Delivery_Time_Min': np.random.normal(loc=35, scale=10, size=n_rows).round(1),
        'Delivery_Rating': np.random.choice([1, 2, 3, 4, 5], n_rows, p=[0.05, 0.05, 0.1, 0.3, 0.5]),
        'Order_Status': np.random.choice(statuses, n_rows)
    }
    df = pd.DataFrame(data)
    df['Final_Amount'] = df['Final_Amount'].clip(lower=100)
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


cities_list = ['All'] + list(df['City'].unique())
selected_city = st.sidebar.selectbox("Filter by City", cities_list)

cuisines_list = ['All'] + list(df['Cuisine_Type'].unique())
selected_cuisine = st.sidebar.selectbox("Filter by Cuisine", cuisines_list)


filtered_df = df.copy()
if selected_city != 'All':
    filtered_df = filtered_df[filtered_df['City'] == selected_city]
if selected_cuisine != 'All':
    filtered_df = filtered_df[filtered_df['Cuisine_Type'] == selected_cuisine]


st.title("🍕 Food Delivery Performance Dashboard")
st.markdown("Real-time executive summary of order volume, revenue, delivery speed, and customer satisfaction.")
st.markdown("---")


total_orders = len(filtered_df)
total_revenue = filtered_df[filtered_df['Order_Status'].str.lower() != 'cancelled']['Final_Amount'].sum()
avg_order_value = filtered_df[filtered_df['Order_Status'].str.lower() != 'cancelled']['Final_Amount'].mean()
avg_delivery_time = filtered_df['Delivery_Time_Min'].mean()

cancelled_orders = (filtered_df['Order_Status'].str.lower() == 'cancelled').sum()
cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0

avg_delivery_rating = filtered_df['Delivery_Rating'].dropna().mean()


col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(label="📦 Total Orders", value=f"{total_orders:,}")

with col2:
    st.metric(label="💰 Total Revenue", value=f"₹{total_revenue:,.2f}")

with col3:
    st.metric(label="🛍️ Avg Order Value", value=f"₹{avg_order_value:.2f}" if not np.isnan(avg_order_value) else "₹0.00")

with col4:
    st.metric(label="⏱️ Avg Delivery Time", value=f"{avg_delivery_time:.1f} mins" if not np.isnan(avg_delivery_time) else "0 mins")

with col5:
    st.metric(label="❌ Cancellation Rate", value=f"{cancellation_rate:.2f}%")

with col6:
    st.metric(label="⭐ Avg Rating", value=f"{avg_delivery_rating:.2f} / 5" if not np.isnan(avg_delivery_rating) else "0.0")

st.markdown("---")


chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Revenue & Order Volume Over Time")
    if 'Order_Date' in filtered_df.columns:
        daily_df = filtered_df.resample('D', on='Order_Date').agg(
            Revenue=('Final_Amount', 'sum'),
            Orders=('Order_ID', 'count')
        ).reset_index()

        fig_revenue = px.line(
            daily_df, 
            x='Order_Date', 
            y='Revenue', 
            title="Daily Revenue Trend",
            labels={'Order_Date': 'Date', 'Revenue': 'Revenue (₹)'},
            line_shape='spline'
        )
        fig_revenue.update_traces(line_color='#27ae60', line_width=3)
        st.plotly_chart(fig_revenue, use_container_width=True)

with chart_col2:
    st.subheader("🍛 Cuisine Revenue Breakdown")
    cuisine_revenue = filtered_df.groupby('Cuisine_Type')['Final_Amount'].sum().reset_index()
    fig_cuisine = px.pie(
        cuisine_revenue, 
        names='Cuisine_Type', 
        values='Final_Amount', 
        title="Revenue Share by Cuisine",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_cuisine, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("🌆 Delivery Performance by City")
    city_perf = filtered_df.groupby('City').agg(
        Avg_Delivery_Time=('Delivery_Time_Min', 'mean'),
        Avg_Rating=('Delivery_Rating', 'mean')
    ).reset_index()

    fig_city = px.bar(
        city_perf, 
        x='City', 
        y='Avg_Delivery_Time', 
        color='Avg_Rating',
        title="Avg Delivery Time (Mins) & Rating by City",
        labels={'Avg_Delivery_Time': 'Avg Time (mins)', 'Avg_Rating': 'Rating'},
        color_continuous_scale='Reds_r'
    )
    st.plotly_chart(fig_city, use_container_width=True)

with chart_col4:
    st.subheader("📋 Filtered Orders Data Preview")
    st.dataframe(
        filtered_df[['Order_ID', 'Order_Date', 'City', 'Cuisine_Type', 'Final_Amount', 'Delivery_Time_Min', 'Order_Status', 'Delivery_Rating']].head(100),
        use_container_width=True
    )
