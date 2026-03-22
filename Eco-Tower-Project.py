import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# --- 1. SETTINGS & AI CONFIG ---
st.set_page_config(page_title="Eco-Tower AI Optimizer", layout="wide")

# Initialize Gemini using your Secret Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("AI Key missing! Please add GOOGLE_API_KEY to Streamlit Secrets.")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("🚛 Network Control")
penalty = st.sidebar.slider("Carbon Tax ($ per kg CO2)", 0, 100, 25)
demand_scale = st.sidebar.select_slider("Demand Scale", options=[0.5, 1.0, 1.5, 2.0], value=1.0)
traffic_impact = st.sidebar.slider("Traffic Congestion Factor", 1.0, 3.0, 1.2)
safety_buffer = st.sidebar.number_input("Safety Stock Buffer (%)", 0, 50, 15)

# --- 3. DATA & MATH ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/network_nodes.csv")
    df = df.rename(columns={'Lat': 'y', 'Lon': 'x'})
    return df

try:
    nodes_df = load_data()
    depot = nodes_df[nodes_df['Type'] == 'Depot'].iloc[0]
    miles_unit = 69 
    nodes_df['dist_miles'] = (abs(nodes_df['x'] - depot['x']) + abs(nodes_df['y'] - depot['y'])) * miles_unit
    nodes_df['q_j_dynamic'] = nodes_df['q_j'] * demand_scale * (1 + safety_buffer/100)
    nodes_df['Cost_S'] = ((nodes_df['dist_miles'] * 1.50) + (nodes_df['dist_miles'] * 0.05 * penalty)) * traffic_impact
    total_cost = nodes_df['Cost_S'].sum()
    total_co2 = 0.0 if penalty > 50 else (nodes_df['dist_miles'].sum() * 0.411 * traffic_impact)

    # --- 4. TABS ---
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🤖 AI Strategic Advisor"])

    with tab1:
        st.title("🌱 Eco-Tower Optimizer")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Cost", f"${total_cost:,.2f}")
        m2.metric("Carbon Footprint", f"{total_co2:,.1f} kg")
        m3.metric("Inventory Volume", f"{nodes_df['q_j_dynamic'].sum():,.0f} Units")

        # Map & Table logic (Same as before)
        st.write("### 📝 Suggested Delivery Sequence")
        manifest = nodes_df[nodes_df['Type'] == 'Customer'].sort_values(by=['p_j', 'dist_miles'], ascending=[False, True])
        st.dataframe(manifest[['Label', 'dist_miles', 'q_j_dynamic', 'p_j', 'Cost_S']].head(10), width='stretch')

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(nodes_df['x'], nodes_df['y'], c='blue', alpha=0.5)
        ax.scatter(depot['x'], depot['y'], color='red', marker='s', s=200)
        st.pyplot(fig)

    with tab2:
        st.header("🧠 Senior Logistics Advisor")
        st.write("Get AI-powered insights based on your current network settings.")
        
        if st.button("Generate Strategic Analysis"):
            with st.spinner("Analyzing NYC/NJ Network Data..."):
                prompt = f"""
                Act as a Senior Supply Chain Consultant. Analyze this NYC/NJ delivery network:
                - Total Cost: ${total_cost:,.2f}
                - CO2 Emissions: {total_co2} kg
                - Traffic Congestion Level: {traffic_impact}x
                - Safety Stock Buffer: {safety_buffer}%
                - Fleet Strategy: {'EV' if penalty > 50 else 'Diesel/Mixed'}
                
                Provide 3 brief, high-level strategic recommendations for Paul Otieno Ogola to improve ROI and sustainability.
                """
                response = model.generate_content(prompt)
                st.markdown(response.text)

except Exception as e:
    st.error(f"Error: {e}")