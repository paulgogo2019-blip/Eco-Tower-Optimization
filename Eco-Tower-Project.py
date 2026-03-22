import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# --- 1. SETTINGS & AI CONFIG ---
st.set_page_config(page_title="Eco-Tower AI Optimizer", layout="wide")

# Universal Key Discovery: Checks both names used in your previous project
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Using the stable 2026 model endpoint
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"AI Engine Error: {e}")
else:
    st.warning("⚠️ No API Key found in Streamlit Secrets. Advisor tab is disabled.")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("🚛 Network Control Center")
st.sidebar.subheader("Basic Parameters")
penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
demand_scale = st.sidebar.select_slider("Demand Scale", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

st.sidebar.write("---")
st.sidebar.subheader("⚠️ Advanced Risk Settings")
traffic_impact = st.sidebar.slider("Traffic Congestion Factor", 1.0, 3.0, 1.2, help="Multiplies fuel & labor costs")
safety_buffer = st.sidebar.number_input("Safety Stock Buffer (%)", 0, 50, 15)

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data():
    # Dynamic column mapping for various CSV formats
    df = pd.read_csv("data/network_nodes.csv")
    df = df.rename(columns={'Lat': 'y', 'lat': 'y', 'Lon': 'x', 'lon': 'x'})
    return df

try:
    nodes_df = load_data()
    depot = nodes_df[nodes_df['Type'] == 'Depot'].iloc[0]

    # --- 4. OPTIMIZATION MATH ---
    miles_unit = 69 
    nodes_df['dist_miles'] = (abs(nodes_df['x'] - depot['x']) + abs(nodes_df['y'] - depot['y'])) * miles_unit
    
    # Calculate demand + safety buffer
    buffer_mult = 1 + (safety_buffer / 100)
    nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale * buffer_mult

    # Prescriptive Costing
    base_cost = (nodes_df['dist_miles'] * 1.50) + (nodes_df['dist_miles'] * 0.05 * penalty)
    nodes_df['Cost_S'] = base_cost * traffic_impact
    
    total_cost = nodes_df['Cost_S'].sum()
    total_co2 = 0.0 if penalty > 50 else (nodes_df['dist_miles'].sum() * 0.411 * traffic_impact)

    # --- 5. THE TABBED INTERFACE ---
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🤖 AI Strategic Advisor"])

    with tab1:
        st.title("🌱 Eco-Tower: Sustainable Network Optimizer")
        st.markdown(f"**Current Fleet Strategy:** {'🟢 100% Green Fleet (EV)' if penalty > 50 else '🟠 Mixed Fleet (Diesel/EV)'}")

        # KPI Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Op. Cost", f"${total_cost:,.2f}", delta=f"{traffic_impact}x Traffic", delta_color="inverse")
        m2.metric("Carbon Footprint", f"{total_co2:,.1f} kg CO2")
        m3.metric("Inventory Volume", f"{nodes_df['q_j_dynamic'].sum():,.0f} Units", delta=f"+{safety_buffer}% Buffer")

        # Route Manifest with 2026-compliant width
        st.write("### 📝 Suggested Delivery Sequence")
        manifest = nodes_df[nodes_df['Type'] == 'Customer'].sort_values(by=['p_j', 'dist_miles'], ascending=[False, True])
        formatted_df = manifest[['Label', 'dist_miles', 'q_j_dynamic', 'p_j', 'Cost_S']].rename(
            columns={'Label': 'Node ID', 'dist_miles': 'Miles', 'q_j_dynamic': 'Units', 'p_j': 'Urgency', 'Cost_S': 'Cost'}
        )
        st.dataframe(formatted_df.head(15), width='stretch')

        # Download Functionality
        csv_data = formatted_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Export for Dispatch", data=csv_data, file_name='NYC_NJ_Routes.csv', mime='text/csv')

        # Network Visualization
        st.write("### 📍 Optimized Network Map")
        fig, ax = plt.subplots(figsize=(10, 5))
        cust = nodes_df[nodes_df['Type'] == 'Customer']
        ax.scatter(cust['x'], cust['y'], c=cust['p_j'], cmap='viridis', s=cust['q_j_dynamic']*20, alpha=0.6)
        ax.scatter(depot['x'], depot['y'], color='red', marker='s', s=250, label='Hub')
        for _, row in cust.iterrows():
            ax.plot([depot['x'], row['x']], [depot['y'], row['y']], color='gray', linestyle='--', alpha=0.1, linewidth=0.5)
        st.pyplot(fig)

    with tab2:
        st.header("🧠 Senior Logistics Advisor")
        st.info("AI-powered strategic analysis for Paul Otieno Ogola's NYC/NJ Network.")
        
        if api_key:
            if st.button("Generate Executive Analysis"):
                with st.spinner("Consulting Gemini 2.5 Strategic Intelligence..."):
                    prompt = f"""
                    Role: Senior Supply Chain Consultant.
                    Scenario: Optimization for NYC/NJ Metro Delivery.
                    Metrics:
                    - Operational Cost: ${total_cost:,.2f}
                    - CO2 Emissions: {total_co2} kg
                    - Traffic Congestion Level: {traffic_impact}x
                    - Safety Stock Buffer: {safety_buffer}%
                    - Strategy: {'100% EV' if penalty > 50 else 'Standard/Mixed Fleet'}
                    
                    Goal: Provide 3 high-impact strategic recommendations to optimize ROI and reduce environmental friction.
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
        else:
            st.error("Missing API Key. Ensure GOOGLE_API_KEY is in Streamlit Secrets.")

except Exception as e:
    st.error(f"System Error: {e}")