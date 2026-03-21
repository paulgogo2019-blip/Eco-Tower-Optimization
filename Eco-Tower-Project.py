import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# --- 1. CORE MATH: MANHATTAN DISTANCE ---
def get_dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

# --- 2. THE ECO-TOWER SOLVER ---
def solve_eco_cvrp(nodes, fleet, Q_type, cost_rate, urgency_weight):
    # Filter fleet based on selection
    v_profile = fleet[fleet['Vehicle_ID'] == Q_type].iloc[0]
    Q_max = v_profile['Q_Capacity']
    e_factor = v_profile['Emission_Factor']
    
    unvisited = nodes.iloc[1:-1].copy()
    depot = nodes.iloc[0]
    routes = []
    total_cost = 0
    total_co2 = 0
    
    while not unvisited.empty:
        curr_route = [depot]
        curr_load = 0
        curr_pos = depot
        
        while not unvisited.empty:
            # Weighted Utility: dist + urgency penalty
            dists = unvisited.apply(lambda r: get_dist((curr_pos['Lat'], curr_pos['Lon']), (r['Lat'], r['Lon'])), axis=1)
            # Eq 7 & 8: Capacity Constraint
            feasible = unvisited[unvisited['q_j'] <= (Q_max - curr_load)]
            
            if feasible.empty: break
            
            # Selection Logic: Minimize (Dist - Urgency Bonus)
            scores = dists[feasible.index] - (feasible['p_j'] * urgency_weight)
            next_idx = scores.idxmin()
            next_node = unvisited.loc[next_idx]
            
            dist_km = dists[next_idx]
            total_cost += dist_km * cost_rate * next_node['Cost_Multiplier']
            total_co2 += dist_km * e_factor
            curr_load += next_node['q_j']
            curr_route.append(next_node)
            curr_pos = next_node
            unvisited = unvisited.drop(next_idx)
            
        curr_route.append(depot)
        routes.append(curr_route)
        
    return routes, total_cost, total_co2

# --- 3. UI LAYOUT ---
st.set_page_config(layout="wide", page_title="Eco-Tower Control Room")
st.title("🌱 Eco-Tower: Sustainable Network Optimizer")

# Sidebar
st.sidebar.header("Control Panel")
selected_v = st.sidebar.selectbox("Select Fleet Type", ["EV_02", "DIESEL_02"])
u_weight = st.sidebar.slider("Urgency Priority Weight", 0.0, 5.0, 1.0)
c_rate = st.sidebar.slider("Transport Rate ($/unit)", 1.0, 10.0, 2.5)

# Load Data
try:
    nodes = pd.read_csv("data/network_nodes.csv")
    fleet = pd.DataFrame({
        'Vehicle_ID': ['EV_02', 'DIESEL_02'],
        'Q_Capacity': [150, 350],
        'Emission_Factor': [0.0, 3.1]
    })
    
    routes, t_cost, t_co2 = solve_eco_cvrp(nodes, fleet, selected_v, c_rate, u_weight)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Cost C(S)", f"${t_cost:,.2f}")
    c2.metric("Total CO2 Emissions", f"{t_co2:,.1f} kg")
    c3.metric("Fleet Size", f"{len(routes)} Vehicles")

    # Map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)
    for i, r in enumerate(routes):
        r_df = pd.DataFrame(r)
        folium.PolyLine(r_df[['Lat', 'Lon']].values.tolist(), color="blue", weight=2).add_to(m)
    st_folium(m, width="100%", height=500)
    
except Exception as e:
    st.error(f"Waiting for data: {e}")