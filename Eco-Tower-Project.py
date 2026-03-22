import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# --- 1. SETTINGS & AI CONFIG ---
st.set_page_config(page_title="Eco-Tower AI Optimizer", layout="wide")

# Initialize Gemini using your Secret Key
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Using the latest stable endpoint to avoid 404 errors
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"AI Initialization Error: {e}")
else:
    st.warning("AI Key not detected in Secrets. The Advisor tab will be limited.")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("🚛 Network Control Center")
st.sidebar.subheader("Basic Parameters")
penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
demand_scale = st.sidebar.select_slider("Demand Scale", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

st.sidebar.write("---")
st.sidebar.subheader("⚠️ Advanced Risk Settings")
traffic_impact = st.sidebar.slider("Traffic Congestion Factor", 1.0, 3.0, 1.2)
safety_buffer = st.sidebar.number_input("Safety Stock Buffer (%)", 0, 50, 15)

# --- 3. DATA ENGINE ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/network_nodes.csv")
    df = df.rename(columns={'Lat': 'y', 'lat': 'y', 'Lon': 'x', 'lon': 'x'})
    return df

try:
    nodes_df = load_data()
    depot = nodes_df[nodes_df['Type'] == 'Depot'].iloc[0]

    # --- 4. OPTIMIZATION MATH ---
    miles_unit = 69 
    nodes_df['dist_miles'] = (abs(nodes_df['x'] - depot['x']) + abs(nodes_df['y'] - depot['y'])) * miles_unit
    
    buffer_multiplier = 1 + (safety_buffer / 100)
    nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale * buffer_multiplier

    base_cost = (nodes_df['dist_miles'] * 1.50) + (nodes_df['dist_miles'] * 0.05 * penalty)
    nodes_df['Cost_S'] = base_cost * traffic_impact
    
    total_cost = nodes_df['Cost_S'].sum()
    total_co2 = 0.0 if penalty > 50 else (nodes_df['dist_miles'].sum() * 0.411 * traffic_impact)

    # --- 5. TABBED INTERFACE ---
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🤖 AI Strategic Advisor"])

    with tab1:
        st.title("🌱 Eco-Tower: Sustainable Network Optimizer")
        st.markdown(f"**Current Fleet Strategy:** {'🟢 100% Green Fleet (EV)' if penalty > 50 else '🟠 Mixed Fleet (Diesel/EV)'}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Operational Cost", f"${total_cost:,.2f}", delta=f"{traffic_impact}x Traffic", delta_color="inverse")
        m2.metric("Carbon Footprint", f"{total_co2:,.1f} kg CO2")
        m3.metric("Inventory Volume", f"{nodes_df['q_j_dynamic'].sum():,.0f} Units")

        st.write("### 📝 Suggested Delivery Sequence")
        manifest = nodes_df[nodes_df['Type'] == 'Customer'].sort_values(by=['p_j', 'dist_miles'], ascending=[False, True])
        formatted_df = manifest[['Label', 'dist_miles', 'q_j_dynamic', 'p_j', 'Cost_S']].rename(
            columns={'Label': 'Node ID', 'dist_miles': 'Miles', 'q_j_dynamic': 'Units', 'p_j': 'Urgency', 'Cost_S': 'Cost'}
        )
        st.dataframe(formatted_df.head(15), width='stretch')

        csv = formatted_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Route Manifest", data=csv, file_name='NYC_NJ_Routes.csv', mime='text/csv')

        st.write("### 📍 Optimized Network Map")
        fig, ax = plt.subplots(figsize=(10, 5))
        cust = nodes_df[nodes_df['Type'] == 'Customer']
        ax.scatter(cust['x'], cust['y'], c=cust['p_j'], cmap='viridis', s=cust['q_j_dynamic']*20, alpha=0.6)
        ax.scatter(depot['x'], depot['y'], color='red', marker='s', s=250, label='Hub')
        for _, row in cust.iterrows():
            ax.plot([depot['x'], row['x']], [depot['y'], row['y']], color='gray', linestyle='--', alpha=0.1, linewidth=0.5)
        st.pyplot(fig)

    with tab2:
        st.header("🧠 AI Strategic Advisor")
        st.write("Generate executive summaries and risk mitigation strategies.")
        
        if st.button("Generate Strategic Analysis"):
            if "GOOGLE_API_KEY" in st.secrets:
                with st.spinner("Consulting Gemini AI..."):
                    prompt = f"""
                    Context: NYC/NJ Logistics Network.
                    Data Summary:
                    - Cost: ${total_cost:,.2f}
                    - CO2: {total_co2} kg
                    - Traffic: {traffic_impact}x
                    - Inventory Buffer: {safety_buffer}%
                    
                    Provide 3 professional, high-level strategic recommendations for Paul Otieno Ogola to optimize this network.
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"AI Error: {e}")
            else:
                st.error("No API Key found. Please add GOOGLE_API_KEY to Streamlit Secrets.")

except Exception as e:
    st.error(f"Configuration Error: {e}")