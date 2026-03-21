import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. THE "CONTROL TOWER" (DYNAMIC SIDEBAR) ---
st.sidebar.title("🚛 Network Control Center")
st.sidebar.markdown("Adjust parameters to re-calculate costs and emissions.")

# Dynamic Sliders
co2_penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
diesel_price = st.sidebar.slider("Diesel Price ($/gal)", 3.00, 6.00, 4.50)
demand_scale = st.sidebar.select_slider("Demand Multiplier (Peak Season)", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

# --- 2. DATA ENGINE ---
@st.cache_data
def load_data():
    nodes = pd.read_csv("data/network_nodes.csv")
    fleet = pd.read_csv("data/fleet_config.csv")
    return nodes, fleet

nodes_df, fleet_df = load_data()

# Apply the Multiplier to your 52 nodes
nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale

# --- 3. THE MATH: C(S) OPTIMIZATION LOGIC ---
def calculate_dynamic_metrics(df, penalty, d_price):
    # Manhattan Distance Math: |x| + |y| from Depot (0,0)
    df['dist'] = abs(df['x']) + abs(df['y'])
    
    # Cost Logic: Base distance cost + Carbon Penalty
    # As Carbon Tax (penalty) goes up, EV becomes more attractive
    df['Cost_S'] = (df['dist'] * 0.20) + (df['dist'] * 0.05 * penalty)
    
    # Emission Logic: If Tax > 50, assume fleet switches to 100% EV (0 emissions)
    emissions = 0.0 if penalty > 50 else (df['dist'].sum() * 0.12)
    
    return df['Cost_S'].sum(), emissions

total_cost, total_co2 = calculate_dynamic_metrics(nodes_df, co2_penalty, diesel_price)

# --- 4. THE DASHBOARD ---
st.title("🌱 Eco-Tower: Sustainable Network Optimizer")
st.markdown(f"**Current Strategy:** {'100% Green Fleet (EV)' if co2_penalty > 50 else 'Mixed Fleet (Diesel/EV)'}")

col1, col2, col3 = st.columns(3)
col1.metric("Total Cost C(S)", f"${total_cost:,.2f}")
col2.metric("Total CO2 Emissions", f"{total_co2:.1f} kg")
col3.metric("Fleet Size", f"{int(12 * demand_scale)} Vehicles")

# 5. THE ROUTING MAP
st.write("### 52-Node Optimized Network")
fig, ax = plt.subplots(figsize=(10, 6))
# Scatter nodes: size based on demand, color based on urgency
ax.scatter(nodes_df['x'], nodes_df['y'], c=nodes_df['p_j'], cmap='winter', s=nodes_df['q_j_dynamic']*15, alpha=0.7)
ax.scatter(0, 0, color='red', marker='s', s=150, label='Depot') # Depot at origin
ax.set_xlabel("East-West Distance")
ax.set_ylabel("North-South Distance")
ax.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig)