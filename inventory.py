def stockout_hours(stock, demand_per_hour):
    """Estimate hours until stockout from current stock and hourly demand."""
    stock = max(0.0, float(stock))
    demand = float(demand_per_hour)
    if demand <= 0:
        return float("inf")
    return stock / demand

def find_replenishment_sources(inventory, product, exclude=None):
    """Return warehouses with available stock for the requested product."""
    rows = inventory[
        (inventory["Product"].str.lower() == product.lower()) &
        (inventory["Warehouse"] != exclude) &
        (inventory["Stock"] > 0)
    ].copy()
    rows = rows.sort_values("Stock", ascending=False)
    return [
        {
            "Warehouse": row["Warehouse"],
            "Available stock": int(row["Stock"]),
            "Daily demand": int(row["Daily demand"])
        }
        for _, row in rows.iterrows()
    ]
