import networkx as nx
import matplotlib.pyplot as plt

# Create the distribution network graph
G = nx.Graph()

# Add buses as nodes
G.add_nodes_from([
    "Grid Bus",
    "Main Feeder Bus",
    "Backup Feeder Bus",
    "Main LV Bus",
    "Residential Bus",
    "Industrial Bus",
    "Backup LV Bus",
    "Alternative Backup Bus"
])

# Add electrical connections with their types

# Normal feeder connections
G.add_edge("Grid Bus", "Main Feeder Bus", type="normal")
G.add_edge("Main Feeder Bus", "Main LV Bus", type="normal")
G.add_edge("Main LV Bus", "Residential Bus", type="normal")
G.add_edge("Main LV Bus", "Industrial Bus", type="normal")

# Backup feeder connections
G.add_edge(
    "Grid Bus",
    "Backup Feeder Bus",
    type="backup"
)

G.add_edge(
    "Backup Feeder Bus",
    "Backup LV Bus",
    type="backup"
)

# Backup LV connection
G.add_edge(
    "Backup LV Bus",
    "Alternative Backup Bus",
    type="backup"
)

# Normally-open tie switch
G.add_edge(
    "Industrial Bus",
    "Backup LV Bus",
    type="tie_switch",
    status="normally_open"
)

# Alternative normally-open tie switch
G.add_edge(
    "Industrial Bus",
    "Alternative Backup Bus",
    type="alternative_tie_switch",
    status="normally_open"
)

# Draw the network
plt.figure(figsize=(12, 7))

pos = nx.spring_layout(G, seed=42)

# Separate edges according to their type
normal_edges = [
    (u, v) for u, v, data in G.edges(data=True)
    if data.get("type") == "normal"
]

backup_edges = [
    (u, v) for u, v, data in G.edges(data=True)
    if data.get("type") == "backup"
]

tie_edges = [
    (u, v) for u, v, data in G.edges(data=True)
    if data.get("type") == "tie_switch"
]

alternative_tie_edges = [
    (u, v) for u, v, data in G.edges(data=True)
    if data.get("type") == "alternative_tie_switch"
]

# Draw the buses
nx.draw_networkx_nodes(
    G,
    pos,
    node_size=2500,
    node_color="lightblue"
)

# Draw normal feeders
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=normal_edges,
    width=2
)

# Draw backup feeders
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=backup_edges,
    width=2,
    style="dashed"
)

# Draw normal tie switch
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=tie_edges,
    width=3,
    style="dotted"
)

# Draw alternative tie switch
nx.draw_networkx_edges(
    G,
    pos,
    edgelist=alternative_tie_edges,
    width=3,
    style="dashdot"
)

# Add bus names
nx.draw_networkx_labels(
    G,
    pos,
    font_size=9,
    font_weight="bold"
)

plt.title("Distribution Network with Feeder and Tie-Switch Types")

plt.show()
# -------------------------------------------------
# FIND RESTORATION PATH
# -------------------------------------------------

source_bus = "Industrial Bus"
target_bus = "Grid Bus"

print("\n===== NETWORKX RESTORATION PATH SEARCH =====")

# Find all possible paths from Industrial Bus to Grid Bus
all_paths = nx.all_simple_paths(
    G,
    source=source_bus,
    target=target_bus
)

print("\nPossible paths:")

for path in all_paths:
    print(" -> ".join(path))

# -------------------------------------------------
# SIMULATE INDUSTRIAL FEEDER FAULT
# -------------------------------------------------

print("\n===== FAULT SIMULATION =====")

# Remove the normal industrial feeder connection
G.remove_edge("Main LV Bus", "Industrial Bus")

print("Industrial feeder fault simulated.")
print("Normal path is now unavailable.")

# Find restoration paths after the fault
restoration_paths = nx.all_simple_paths(
    G,
    source="Industrial Bus",
    target="Grid Bus"
)

print("\nAvailable restoration paths:")

for path in restoration_paths:
    print(" -> ".join(path))

# -------------------------------------------------
# RESTORATION CANDIDATE ANALYSIS
# -------------------------------------------------

print("\n===== RESTORATION CANDIDATE ANALYSIS =====")

restoration_paths = list(nx.all_simple_paths(
    G,
    source="Industrial Bus",
    target="Grid Bus"
))

for number, path in enumerate(restoration_paths, start=1):

    print(f"\nCandidate {number}")
    print("Path:", " -> ".join(path))
    print("Number of connections:", len(path) - 1)

    # Check which tie switch is used
    if "Alternative Backup Bus" in path:
        print("Tie Switch: Alternative Tie Switch")

    elif "Backup Feeder Bus" in path:
        print("Tie Switch: Normally Open Tie Switch")

