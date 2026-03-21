# 🌱 Eco-Tower: Sustainable Network Optimizer
**An Interactive Decision Support System for Green Logistics & Route Optimization**

## 📌 Project Overview
This project addresses the **Capacitated Vehicle Routing Problem (CVRP)** with a focus on sustainability. It simulates a 52-node delivery network in the New York/New Jersey metropolitan area, allowing supply chain managers to visualize the trade-offs between operational costs and carbon emissions.

## 🚀 Key Features
- **Dynamic Optimization:** Real-time re-calculation of costs based on fuel prices and carbon taxes.
- **Sustainability Modeling:** Logic-driven fleet selection between Electric Vehicles (EV) and Diesel trucks.
- **Sensitivity Analysis:** Interactive "Control Tower" (Sidebar) to stress-test the network during peak seasons.
- **Geospatial Visualization:** 52-node coordinate mapping using Manhattan Distance logic.

## 🛠️ The Tech Stack
- **Language:** Python 3.9
- **Dashboard:** Streamlit (Web Interface)
- **Data Science:** Pandas (Data Wrangling), NumPy (Mathematical Modeling)
- **Visualization:** Matplotlib (Network Mapping)

## 📊 Mathematical Logic
The engine utilizes **Manhattan Distance** to simulate urban grid travel:
$$d(i,j) = |x_i - x_j| + |y_i - y_j|$$

The objective function minimizes total cost $C(S)$, which factors in carbon penalties:
$$min \sum (\text{Distance Cost}) + (\text{CO}_2 \text{ Emissions} \times \text{Carbon Tax})$$

## 📂 Project Structure
- `Eco-Tower-Project.py`: The main optimization engine and Streamlit UI.
- `data/`: Contains `network_nodes.csv` (52-node GPS data) and `fleet_config.csv`.

---
**Developer:** [Your Name]  
**Background:** MS in Supply Chain Management, Washington University in St. Louis