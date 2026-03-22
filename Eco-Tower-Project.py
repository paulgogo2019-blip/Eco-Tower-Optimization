import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. SETTINGS & SIDEBAR ---
st.set_page_config(page_title="Eco-Tower Optimizer", layout="wide")

st.sidebar.title("🚛 Network Control Center")
st.sidebar.info("Adjust the Carbon Tax to see the 'Tipping Point' where EV becomes cheaper than Diesel.")

# User Controls
penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
demand_scale = st.sidebar.select_slider("Demand Scale", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

# --- 2. DATA ENGINE ---
@st.cache_data
def load_data():
    # Load and clean coordinates for NYC/NJ Metro Area
    df = pd.read_csv("data/network_nodes.csv")
    df = df.rename(columns={'Lat': 'y', 'lat': 'y', 'Lon': 'x', 'lon': 'x'})
    return df

try:
    nodes_df = load_data()
    depot = nodes_df[nodes_df['Type'] == 'Depot'].iloc[0]

    # --- 3. OPTIMIZATION MATH (Prescriptive Analytics) ---
    # Convert GPS degrees to Miles (Approx 69 miles per degree in NYC)
    miles_unit = 69 
    
    # Calculate distance from Hub for every node
    nodes_df['dist_miles'] = (abs(nodes_df['x'] - depot['x']) + abs(nodes_df['y'] - depot['y'])) * miles_unit
    nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale

    # Cost logic: $1.50/mile base + $0.05 per mile per carbon tax unit
    nodes_df['Cost_S'] = (nodes_df['dist_miles'] * 1.50) + (nodes_df['dist_miles'] * 0.05 * penalty)
    
    total_cost = nodes_df['Cost_S'].sum()
    
    # Emission factor: ~0.411 kg CO2 per mile for medium-duty delivery truck
    # If penalty > 50, we assume the fleet has transitioned to 100% EV (0 emissions)
    total_co2 = 0.0 if penalty > 50 else (nodes_df['dist_miles'].sum() * 0.411)

    # --- 4. DASHBOARD UI ---
    st.title("🌱 Eco-Tower: Sustainable Network Optimizer")
    st.markdown(f"**Current Fleet Strategy:** {'🟢 100% Green Fleet (EV)' if penalty > 50 else '🟠 Mixed Fleet (Diesel/EV)'}")

    # Top Level Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Operational Cost", f"${total_cost:,.2f}")
    m2.metric("Carbon Footprint", f"{total_co2:,.1f} kg CO2")
    m3.metric("Required Fleet Size", f"{int(12 * demand_scale)} Vehicles")

    # --- 5. ROUTE MANIFEST & DOWNLOAD ---
    st.write("---")
    st.write("### 📝 Suggested Delivery Sequence")
    st.write("Priority is determined by **Urgency (1-5)** and **Proximity** to the Hub.")
    
    # Create the manifest: Sort by Urgency (High to Low) then Distance (Short to Long)
    manifest = nodes_df[nodes_df['Type'] == 'Customer'].sort_values(by=['p_j', 'dist_miles'], ascending=[False, True])
    
    # Display Table
    formatted_df = manifest[['Label', 'dist_miles', 'q_j_dynamic', 'p_j', 'Cost_S']].rename(
        columns={
            'Label': 'Node ID',
            'dist_miles': 'Miles from Hub',
            'q_j_dynamic': 'Current Demand',
            'p_j': 'Urgency (1-5)',
            'Cost_S': 'Individual Cost'
        }
    )
    st.dataframe(formatted_df.head(15), use_container_width=True)

    # DOWNLOAD BUTTON
    csv = formatted_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Full Route Manifest as CSV",
        data=csv,
        file_name='NYC_NJ_Optimized_Routes.csv',
        mime='text/csv',
    )

    # --- 6. GEOSPATIAL VISUALIZATION ---
    st.write("---")
    st.write("### 📍 52-Node Optimized Network Map")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    cust = nodes_df[nodes_df['Type'] == 'Customer']
    # Color by Urgency, Size by Demand
    scatter = ax.scatter(cust['x'], cust['y'], 
                         c=cust['p_j'], cmap='viridis', 
                         s=cust['q_j_dynamic']*30, alpha=0.6, label='Customers')
    
    ax.scatter(depot['x'], depot['y'], color='red', marker='s', s=250, label='Global Hub (Depot)')
    
    # Draw Radial Assignment Lines
    for _, row in cust.iterrows():
        ax.plot([depot['x'], row['x']], [depot['y'], row['y']], color='gray', linestyle='--', alpha=0.1, linewidth=0.5)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.4)
    st.pyplot(fig)

except Exception as e:
    st.error(f"Configuration Error: {e}")