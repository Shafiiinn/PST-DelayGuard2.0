import heapq

def build_network(roads):
    """
    Build an adjacency list representation of the network from road definitions.
    Assumes bidirectional edges when 'open' is True.
    """
    network = {}
    for (u, v), data in roads.items():
        if not data.get("open", True):
            continue
        if u not in network:
            network[u] = []
        if v not in network:
            network[v] = []
        
        network[u].append((v, data["hours"], data["km"]))
        network[v].append((u, data["hours"], data["km"]))
    return network

def shortest_path(network, start, target, weight="hours"):
    """
    Compute the shortest path using Dijkstra's algorithm.
    Returns: (path_list, total_hours, total_km) or ([], None, None) if unreachable.
    """
    if start not in network or target not in network:
        return [], None, None

    # Priority queue: (cost, current_node, current_hours, current_km, path)
    pq = [(0, start, 0.0, 0.0, [start])]
    visited = {}

    while pq:
        cost, current, total_h, total_k, path = heapq.heappop(pq)

        if current in visited and visited[current] <= cost:
            continue
        visited[current] = cost

        if current == target:
            return path, total_h, total_k

        for neighbor, hours, km in network.get(current, []):
            edge_cost = hours if weight == "hours" else km
            next_cost = cost + edge_cost
            if neighbor not in visited or next_cost < visited[neighbor]:
                heapq.heappush(pq, (
                    next_cost,
                    neighbor,
                    total_h + hours,
                    total_k + km,
                    path + [neighbor]
                ))

    return [], None, None
