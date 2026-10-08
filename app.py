import streamlit as st
import pandas as pd
import plotly.express as px
from route_optimizer import build_network, shortest_path
from inventory import stockout_hours, find_replenishment_sources
from recovery_engine import recommend_recovery

st.set_page_config(page_title="SupplyGuard AI", page_icon="🚚", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.metric-card {border: 1px solid rgba(128,128,128,.25); border-radius: 12px; padding: 14px;}
.small-note {color: #8b8b8b; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

st.title("🚚 SupplyGuard AI")
st.caption("Supply chain crisis prevention & recovery • Prototype using simulated data")

if "roads" not in st.session_state:
    st.session_state.roads = {
        ("Central Warehouse", "North Hub"): {"km": 18, "hours": 0.6, "open": True},
        ("Central Warehouse", "East Hub"): {"km": 22, "hours": 0.8, "open": True},
        ("North Hub", "Hospital"): {"km": 12, "hours": 0.5, "open": True},
        ("East Hub", "Hospital"): {"km": 9, "hours": 0.4, "open": True},
        ("North Hub", "East Hub"): {"km": 10, "hours": 0.35, "open": True},
        ("Central Warehouse", "Hospital"): {"km": 38, "hours": 1.3, "open": True},
    }

shipments = pd.DataFrame([
    {"Shipment": "SG-101", "Product": "Emergency medicine", "Origin": "Central Warehouse", "Destination": "Hospital", "Status": "At risk", "ETA (hours)": 7.0, "Priority": "Critical"},
    {"Shipment": "SG-102", "Product": "Surgical kits", "Origin": "Central Warehouse", "Destination": "North Hub", "Status": "On time", "ETA (hours)": 1.0, "Priority": "High"},
    {"Shipment": "SG-103", "Product": "Food supplies", "Origin": "East Hub", "Destination": "Hospital", "Status": "Delayed", "ETA (hours)": 3.5, "Priority": "Medium"},
    {"Shipment": "SG-104", "Product": "Water filters", "Origin": "Central Warehouse", "Destination": "East Hub", "Status": "On time", "ETA (hours)": 0.8, "Priority": "Low"},
])

inventory = pd.DataFrame([
    {"Warehouse": "Central Warehouse", "Product": "Emergency medicine", "Stock": 120, "Daily demand": 180},
    {"Warehouse": "North Hub", "Product": "Emergency medicine", "Stock": 80, "Daily demand": 96},
    {"Warehouse": "East Hub", "Product": "Emergency medicine", "Stock": 240, "Daily demand": 120},
    {"Warehouse": "Central Warehouse", "Product": "Surgical kits", "Stock": 60, "Daily demand": 30},
    {"Warehouse": "North Hub", "Product": "Surgical kits", "Stock": 18, "Daily demand": 24},
])

st.info("Demo data is simulated for a student prototype. Do not use these estimates for real logistics or medical decisions.")

# Sidebar controls
st.sidebar.header("⚠️ Crisis simulator")
disruption = st.sidebar.selectbox("Scenario", [
    "Normal operations", "Main route blocked", "Heavy traffic", "Demand spike"
])
stock_at_destination = st.sidebar.slider("Destination stock (units)", 0, 100, 12, 1)
demand_per_hour = st.sidebar.slider("Destination demand (units/hour)", 1, 30, 8, 1)
recovery_priority = st.sidebar.selectbox("Recovery priority", [
    "Balance cost and time", "Meet deadline first", "Minimize cost"
])
transfer_cost_per_unit = st.sidebar.number_input("Transfer cost per unit (demo)", min_value=0.0, value=0.8, step=0.1)

roads = {k: v.copy() for k, v in st.session_state.roads.items()}
if disruption == "Main route blocked":
    roads[("Central Warehouse", "Hospital")]["open"] = False
elif disruption == "Heavy traffic":
    roads[("Central Warehouse", "Hospital")]["hours"] *= 2.6
    roads[("North Hub", "Hospital")]["hours"] *= 1.8
elif disruption == "Demand spike":
    demand_per_hour = int(demand_per_hour * 1.7)

network = build_network(roads)
route, route_hours, route_km = shortest_path(network, "Central Warehouse", "Hospital", weight="hours")
hours_left = stockout_hours(stock_at_destination, demand_per_hour)
sources = find_replenishment_sources(inventory, "Emergency medicine", exclude="Hospital")
recommendation = recommend_recovery(
    route=route,
    route_hours=route_hours,
    route_km=route_km,
    stockout_hours=hours_left,
    sources=sources,
    priority=recovery_priority,
    transfer_cost_per_unit=transfer_cost_per_unit,
)

st.subheader("Crisis Control Center")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tracked shipments", len(shipments))
c2.metric("Delayed / at risk", int(shipments["Status"].isin(["Delayed", "At risk"]).sum()))
c3.metric("Destination stock", f"{stock_at_destination} units")
c4.metric("Estimated stock cover", "Immediate" if hours_left == 0 else f"{hours_left:.1f} hrs")

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Shipment monitor")
    st.dataframe(shipments, use_container_width=True, hide_index=True)
    st.subheader("Inventory risk")
    inv = inventory.copy()
    inv["Stock cover (hours)"] = inv.apply(lambda r: stockout_hours(r["Stock"], r["Daily demand"] / 24), axis=1)
    st.dataframe(inv, use_container_width=True, hide_index=True)
with right:
    st.subheader("Network & route")
    route_df = pd.DataFrame([
        {"Stop order": i + 1, "Location": place}
        for i, place in enumerate(route)
    ])
    if route:
        st.write(" → ".join(route))
        st.metric("Estimated route time", f"{route_hours:.2f} hours")
        st.metric("Route distance", f"{route_km:.1f} km")
    else:
        st.error("No open route found between the selected origin and destination.")
    st.caption("Route values are illustrative edge weights, not live map data.")

st.divider()
st.subheader("🧠 Recommended recovery plan")
if recommendation["urgency"] == "CRITICAL":
    st.error(recommendation["headline"])
elif recommendation["urgency"] == "HIGH":
    st.warning(recommendation["headline"])
else:
    st.success(recommendation["headline"])

st.write(recommendation["reason"])
a, b, c = st.columns(3)
a.metric("Recommended action", recommendation["action"])
b.metric("Estimated delivery", "No route" if route_hours is None else f"{route_hours:.2f} hrs")
c.metric("Stock cover", "0 hrs" if hours_left == 0 else f"{hours_left:.2f} hrs")

if sources:
    st.markdown("**Potential replenishment sources**")
    st.dataframe(pd.DataFrame(sources), use_container_width=True, hide_index=True)
else:
    st.write("No replenishment source with available stock was found in the demo inventory.")

st.subheader("Why did the system choose this?")
for reason in recommendation["explanations"]:
    st.markdown(f"- {reason}")

st.divider()
st.subheader("Shipment status overview")
status_counts = shipments["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
fig = px.bar(status_counts, x="Status", y="Count", title="Simulated shipment status counts")
st.plotly_chart(fig, use_container_width=True)

with st.expander("Project scope & next improvements"):
    st.markdown("""
    **Currently implemented**
    - Dijkstra shortest-path routing on a small sample graph
    - Inventory stock-cover calculations
    - Alternative warehouse stock-source suggestions
    - Rule-based recovery recommendation that reacts to scenario controls
    - Interactive dashboard and crisis simulator

    **Next improvements**
    - Import user-uploaded CSV data
    - Add real road-network / traffic data and map visualization
    - Train and evaluate a delay prediction model using a real dataset
    - Persist data in a database and add user authentication
    - Compare multiple recovery plans with explicit cost, time and stockout penalties
    """)
