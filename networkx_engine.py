import networkx as nx


def find_restoration_paths():
    
    # Create distribution network graph
    G = nx.Graph()

    # Add buses
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

    # Normal feeder connections
    G.add_edge(
        "Grid Bus",
        "Main Feeder Bus",
        type="normal"
    )

    G.add_edge(
        "Main Feeder Bus",
        "Main LV Bus",
        type="normal"
    )

    G.add_edge(
        "Main LV Bus",
        "Residential Bus",
        type="normal"
    )

    G.add_edge(
        "Main LV Bus",
        "Industrial Bus",
        type="normal"
    )

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

    # Simulate fault on the normal industrial feeder
    G.remove_edge(
        "Main LV Bus",
        "Industrial Bus"
    )

    # Find available restoration paths
    restoration_paths = list(
        nx.all_simple_paths(
            G,
            source="Industrial Bus",
            target="Grid Bus"
        )
    )

    return restoration_paths
# Test the restoration path function

paths = find_restoration_paths()

print("\n===== NETWORKX ENGINE TEST =====")

for number, path in enumerate(paths, start=1):
    print(f"Candidate {number}:")
    print(" -> ".join(path))