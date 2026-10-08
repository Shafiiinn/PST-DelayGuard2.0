def recommend_recovery(route, route_hours, route_km, stockout_hours, sources,
                       priority, transfer_cost_per_unit=0.8):
    """Simple explainable rule-based recovery recommender for the prototype."""
    route_exists = bool(route) and route_hours is not None
    urgent_stock = stockout_hours <= 4
    source = sources[0] if sources else None
    explanations = []

    if not route_exists:
        explanations.append("The current road network has no available route to the destination.")
        if source and urgent_stock:
            action = f"Emergency transfer from {source['Warehouse']}"
            headline = "CRITICAL: Route unavailable and stock is running out."
            reason = "The route is blocked and destination inventory cannot safely cover the expected wait."
            urgency = "CRITICAL"
        elif source:
            action = f"Check transfer from {source['Warehouse']}"
            headline = "HIGH: Delivery route unavailable."
            reason = "Consider stock transfer while dispatch teams investigate an alternate route."
            urgency = "HIGH"
        else:
            action = "Escalate and locate alternate supply"
            headline = "CRITICAL: No route or replenishment source found."
            reason = "The prototype could not find a feasible delivery route or another warehouse with stock."
            urgency = "CRITICAL"
    elif urgent_stock:
        if source and priority != "Minimize cost":
            action = f"Transfer from {source['Warehouse']} + reroute"
            headline = "CRITICAL: Stockout may happen before replenishment."
            reason = "A stock transfer can provide a buffer while the shipment follows the fastest available route."
            urgency = "CRITICAL"
        elif source:
            action = f"Compare low-cost transfer from {source['Warehouse']}"
            headline = "HIGH: Low inventory detected; cost-sensitive recovery suggested."
            reason = "A transfer is available, but the selected priority favors minimizing cost."
            urgency = "HIGH"
        else:
            action = "Escalate shortage and seek external stock"
            headline = "CRITICAL: Destination stock is insufficient."
            reason = "No alternate warehouse with stock is listed in the demo inventory."
            urgency = "CRITICAL"
    elif route_hours > stockout_hours:
        action = f"Evaluate transfer from {source['Warehouse']}" if source else "Escalate inventory risk"
        headline = "HIGH: Shipment may arrive after stock runs out."
        reason = "Estimated travel time exceeds the destination's remaining stock cover."
        urgency = "HIGH"
    else:
        action = "Keep route and monitor conditions"
        headline = "Normal: Current plan appears feasible."
        reason = "The route is available and estimated travel time is within the destination's stock cover."
        urgency = "LOW"

    if route_exists:
        explanations.append(f"Selected route: {' → '.join(route)}.")
        explanations.append(f"Estimated route time is {route_hours:.2f} hours over {route_km:.1f} km.")
    explanations.append("Stock cover is estimated as current stock divided by hourly demand.")
    explanations.append(f"Recovery priority selected: {priority}.")
    explanations.append("Recommendations use transparent demo rules, not a trained AI model.")
    return {
        "urgency": urgency,
        "headline": headline,
        "reason": reason,
        "action": action,
        "explanations": explanations,
    }
