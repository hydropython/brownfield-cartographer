from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
from src.models.graph import CartographyGraph

print("=== Loading Cartography Graph ===")

# Load the graph from .cartography/module_graph.json
carto_path = Path(".cartography/module_graph.json")
if carto_path.exists():
    with open(carto_path, "r") as f:
        import json
        data = json.load(f)
    
    # Convert from NetworkX node_link_data format
    nx_graph = json_graph.node_link_graph(data)
    
    print(f"Loaded: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges")
    
    # Create visualization
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(nx_graph, k=0.5, iterations=50)
    
    # Draw
    nx.draw(nx_graph, pos, with_labels=True, node_color="lightblue", 
            node_size=2000, font_size=8, arrows=True)
    
    plt.title("Cartography Graph  Network Visualization")
    plt.savefig("cartography_network.png", dpi=300, bbox_inches="tight")
    print(" Saved to: cartography_network.png")
    plt.show()
else:
    print(f" File not found: {carto_path}")
    print("  Run the Hydrologist agent first to generate the graph")
