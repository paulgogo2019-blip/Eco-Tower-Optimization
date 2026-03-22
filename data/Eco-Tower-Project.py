import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. DYNAMIC SIDEBAR ---
st.sidebar.title("🚛 Network Control Center")
co2_penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
diesel_price = st.sidebar.slider("Diesel Price ($/gal)", 3.00, 6.00, 4.50)
demand_scale = st.sidebar.select_slider("Demand Scale", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

# --- 2. DATA LOADING & AUTOMATIC CLEANING ---
@st.cache_data
def load_data():
    # Load the main node data
    df = pd.read_csv("data/network_nodes.csv")
    
    # Safety Check: Standardize headers to x and y regardless of the CSV format
    rename_map = {
        'Lat': 'y', 'lat': 'y', 'Latitude': 'y',
        'Lon': 'x', 'lon': 'x', 'Longitude': 'x',
        'q_j (Demand)': 'q_j', 'p_j (Urgency)': 'p_j'
    }
    df = df.rename(columns=rename_map)
    return df

nodes_df = load_data()

# --- 3. THE OPTIMIZATION MATH ---
# Calculate dynamic demand and Manhattan distance
nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale
nodes_df['dist'] = abs(nodes_df['x']) + abs(nodes_df['y'])

# Cost Function: Distance Cost + Carbon Tax impact
nodes_df['Cost_S'] = (nodes_df['dist'] * 0.20) + (nodes_df['dist'] * 0.05 * co2_penalty)
total_cost = nodes_df['Cost_S'].sum()
total_co2 = 0.0 if co2_penalty > 50 else (nodes_df['dist'].sum() * 0.12)

# --- 4. THE UI ---
st.title("🌱 Eco-Tower: Sustainable Network Optimizer")
st.markdown(f"**Current Strategy:** {'100% Green Fleet (EV)' if co2_penalty > 50 else 'Mixed Fleet (Diesel/EV)'}")

# High-Level Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total Cost C(S)", f"${total_cost:,.2f}")
c2.metric("Total CO2 Emissions", f"{total_co2:.1f} kg")
c3.metric("Fleet Size", f"{int(12 * demand_scale)} Vehicles")

# 5. GEOSPATIAL MAP
st.write("### 52-Node Optimized Network")
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(nodes_df['x'], nodes_df['y'], c=nodes_df['p_j'], cmap='winter', s=nodes_df['q_j_dynamic']*15, alpha=0.7)
ax.scatter(0, 0, color='red', marker='s', s=150, label='Depot') # Depot
ax.set_xlabel("Longitude (x)")
ax.set_ylabel("Latitude (y)")
ax.grid(True, linestyle='--', alpha=0.4)
st.pyplot(fig)