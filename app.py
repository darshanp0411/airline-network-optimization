%%writefile app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
import boto3
import s3fs

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Airline Strategic Hub", layout="wide")

# --- 1. S3 DATA LOADER (Cached for Speed) ---
@st.cache_data
def load_data(bucket_name, prefix=''):
    try:
        # Connect to S3
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        files = [obj.key for obj in bucket.objects.filter(Prefix=prefix) if obj.key.endswith('csv')]
        
        if not files:
            st.error("No CSV files found in S3.")
            return None
            
        df_list = []
        for file in files:
            path = f"s3://{bucket_name}/{file}"
            # Read CSV
            temp_df = pd.read_csv(path)
            temp_df.columns = [c.upper() for c in temp_df.columns]
            df_list.append(temp_df)
            
        df = pd.concat(df_list, ignore_index=True)
        
        # --- V4 FILTERS (Strict Logic) ---
        # 1. Remove Cargo (Must have seats)
        df = df[df['SEATS'] > 0]
        # 2. Remove Ghost Routes (Must have takeoffs)
        if 'DEPARTURES_PERFORMED' in df.columns:
            df = df[df['DEPARTURES_PERFORMED'] > 0]
            
        # --- COLUMN MAPPING ---
        if 'CARRIER_NAME' in df.columns: df['Airline_Label'] = df['CARRIER_NAME']
        else: df['Airline_Label'] = df.get('UNIQUE_CARRIER', 'Unknown')

        df['Origin_Label'] = df.get('ORIGIN_CITY_NAME', df.get('ORIGIN', 'Unknown'))
        df['Dest_Label'] = df.get('DEST_CITY_NAME', df.get('DEST', 'Unknown'))
        
        # Region Mapping
        if 'DEST_COUNTRY_NAME' in df.columns: df['Region'] = df['DEST_COUNTRY_NAME']
        elif 'DEST_STATE_ABR' in df.columns: df['Region'] = df['DEST_STATE_ABR']
        else: df['Region'] = 'Global'

        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- 2. ANALYTICS ENGINE ---
def run_audit(df, hub_code):
    # Filter for Hub & Max Year
    max_year = df['YEAR'].max()
    data = df[(df['YEAR'] == max_year) & (df['ORIGIN'] == hub_code)].copy()
    
    if data.empty: return None
    
    # Aggregate
    stats = data.groupby(['Region', 'Dest_Label', 'Airline_Label']).agg({
        'PASSENGERS': 'sum', 'SEATS': 'sum', 
        'DEPARTURES_PERFORMED': 'sum', 'DISTANCE': 'mean'
    }).reset_index()
    
    # Financials
    stats['Yield'] = 0.6 * (stats['DISTANCE'] ** -0.15)
    stats['Revenue'] = stats['PASSENGERS'] * (stats['DISTANCE'] * stats['Yield'])
    stats['Cost'] = (((stats['DISTANCE']/450)+0.5) * stats['DEPARTURES_PERFORMED']) * (5500 + (850*2.80))
    stats['Profit'] = stats['Revenue'] - stats['Cost']
    stats['Margin'] = (stats['Profit'] / stats['Revenue']) * 100
    
    # Market Position
    city_totals = stats.groupby('Dest_Label')['PASSENGERS'].sum().reset_index()
    city_totals.rename(columns={'PASSENGERS': 'City_Total'}, inplace=True)
    stats = pd.merge(stats, city_totals, on='Dest_Label')
    stats['Market_Share'] = (stats['PASSENGERS'] / stats['City_Total']) * 100
    
    conditions = [
        (stats['Market_Share'] > 50),
        (stats['Market_Share'] > 20) & (stats['Market_Share'] <= 50),
        (stats['Market_Share'] <= 20)
    ]
    stats['Status'] = np.select(conditions, ['👑 Monopoly', '⚔️ Competitive', '⚠️ Minor Player'])
    
    return stats

# --- 3. FORECAST ENGINE ---
def get_forecast(df, origin, dest):
    route = df[(df['ORIGIN'] == origin) & (df['DEST_CITY_NAME'] == dest)].copy()
    if route.empty: route = df[(df['ORIGIN'] == origin) & (df['DEST'] == dest)].copy()
    
    if route.empty: return None, "No Data"
        
    monthly = route.groupby(['YEAR', 'MONTH'])['PASSENGERS'].sum().reset_index()
    clean = monthly[~monthly['YEAR'].isin([2020, 2021])] # Remove Covid
    
    if len(clean) < 12: return None, "Not Enough Data"
    
    model = RandomForestRegressor(n_estimators=100)
    model.fit(clean[['YEAR', 'MONTH']], clean['PASSENGERS'])
    
    last_year = monthly['YEAR'].max()
    future = pd.DataFrame([{'YEAR': last_year+1, 'MONTH': m} for m in range(1, 13)])
    future['PASSENGERS'] = model.predict(future)
    
    monthly['Type'] = 'Historical'
    future['Type'] = 'Forecast'
    
    return pd.concat([monthly, future]), "Success"

# ==========================================
# 🚀 MAIN APP UI
# ==========================================

st.title("✈️ Airline Strategic Network Planner")

# --- SIDEBAR CONTROL ---
st.sidebar.header("🕹️ Control Panel")
BUCKET = st.sidebar.text_input("S3 Bucket Name", value="darshan-airline-project-2026")

df = load_data(BUCKET)

if df is not None:
    # Hub Selector
    hubs = sorted(df['ORIGIN'].unique())
    default_ix = hubs.index('JFK') if 'JFK' in hubs else 0
    selected_hub = st.sidebar.selectbox("Select Hub Airport", hubs, index=default_ix)
    
    # Run Analysis
    audit = run_audit(df, selected_hub)
    
    if audit is not None:
        # --- KPI ROW ---
        total_profit = audit['Profit'].sum()
        top_dest = audit.sort_values('Profit', ascending=False).iloc[0]['Dest_Label']
        monopolies = len(audit[audit['Status'].str.contains('Monopoly')])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Hub Profit", f"${total_profit/1e6:.1f}M")
        c2.metric("Top Destination", top_dest)
        c3.metric("Monopoly Routes", monopolies)
        
        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["🗺️ Strategy Map", "🌍 Country Report", "📈 AI Forecast"])
        
        with tab1:
            st.subheader("Strategic Market Map (Treemap)")
            st.markdown("**Size** = Passenger Volume | **Color** = Profit Margin (Green is Good)")
            fig = px.treemap(audit, 
                             path=[px.Constant(selected_hub), 'Region', 'Dest_Label', 'Airline_Label'], 
                             values='PASSENGERS', color='Margin',
                             color_continuous_scale='RdYlGn', color_continuous_midpoint=0,
                             hover_data=['Profit', 'Status'])
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            st.subheader("Detailed Route List (By Country/Region)")
            
            # Filter by Region
            regions = ['All'] + sorted(audit['Region'].unique().tolist())
            selected_region = st.selectbox("Filter Region:", regions)
            
            view_df = audit.copy()
            if selected_region != 'All':
                view_df = view_df[view_df['Region'] == selected_region]
            
            # Format for Display
            view_df = view_df[['Region', 'Dest_Label', 'Airline_Label', 'Status', 'Profit', 'Margin']]
            view_df = view_df.sort_values('Profit', ascending=False)
            
            st.dataframe(view_df.style.format({'Profit': '${:,.0f}', 'Margin': '{:.1f}%'}), use_container_width=True)
            
        with tab3:
            st.subheader(f"Demand Forecast: {selected_hub} -> ?")
            target_city = st.selectbox("Select Destination to Forecast", sorted(audit['Dest_Label'].unique()))
            
            if st.button("Generate AI Prediction"):
                data, msg = get_forecast(df, selected_hub, target_city)
                if msg == "Success":
                    data['Date'] = pd.to_datetime(data[['YEAR', 'MONTH']].assign(DAY=1))
                    fig_fc = px.line(data, x='Date', y='PASSENGERS', color='Type',
                                     color_discrete_map={'Historical': 'gray', 'Forecast': '#00CC96'})
                    st.plotly_chart(fig_fc, use_container_width=True)
                else:
                    st.error(msg)
    else:
        st.warning(f"No data found for Hub {selected_hub}")