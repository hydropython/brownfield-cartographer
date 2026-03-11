"""
Knowledge Graph - NetworkX wrapper with serialization

Central data store for structure and lineage.
"""

import networkx as nx
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class KnowledgeGraph:
    """
    NetworkX wrapper for knowledge graph with serialization.
    
    Stores module dependencies and data lineage as directed graphs.
    Supports JSON export to .cartography/ directory.
    """
    
    def __init__(self, name: str = "knowledge_graph"):
        """Initialize empty knowledge graph."""
        self.name = name
        self.graph = nx.DiGraph()
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, node_id: str, **attrs):
        """
        Add node with attributes.
        
        Args:
            node_id: Unique node identifier
            **attrs: Node attributes (type, label, file, etc.)
        """
        self.graph.add_node(node_id, **attrs)
    
    def add_edge(self, source: str, target: str, **attrs):
        """
        Add edge with attributes.
        
        Args:
            source: Source node ID
            target: Target node ID
            **attrs: Edge attributes (type, weight, confidence, etc.)
        """
        self.graph.add_edge(source, target, **attrs)
    
    def node_count(self) -> int:
        """Get node count."""
        return self.graph.number_of_nodes()
    
    def edge_count(self) -> int:
        """Get edge count."""
        return self.graph.number_of_edges()
    
    def get_nodes(self) -> List[str]:
        """Get all node IDs."""
        return list(self.graph.nodes())
    
    def get_edges(self) -> List[tuple]:
        """Get all edges as (source, target) tuples."""
        return list(self.graph.edges())
    
    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self.graph.nodes()
    
    def has_edge(self, source: str, target: str) -> bool:
        """Check if edge exists."""
        return self.graph.has_edge(source, target)
    
    def get_predecessors(self, node_id: str) -> List[str]:
        """Get upstream dependencies."""
        return list(self.graph.predecessors(node_id))
    
    def get_successors(self, node_id: str) -> List[str]:
        """Get downstream dependencies."""
        return list(self.graph.successors(node_id))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "metadata": self.metadata,
            "nodes": [
                {"id": n, **self.graph.nodes[n]}
                for n in self.graph.nodes()
            ],
            "edges": [
                {"source": e[0], "target": e[1], **self.graph.edges[e]}
                for e in self.graph.edges()
            ],
            "stats": {
                "node_count": self.node_count(),
                "edge_count": self.edge_count()
            }
        }
    
    def to_file(self, output_path: Path):
        """Serialize to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_file(cls, input_path: Path) -> "KnowledgeGraph":
        """Load from JSON file."""
        kg = cls()
        with open(input_path, "r") as f:
            data = json.load(f)
        
        kg.name = data.get("name", "knowledge_graph")
        kg.metadata = data.get("metadata", {})
        
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            kg.add_node(node_id, **node)
        
        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            kg.add_edge(source, target, **edge)
        
        return kg
    
    def blast_radius(self, target: str) -> Dict[str, Any]:
        """
        Calculate blast radius for a target node.
        
        Returns all downstream nodes that would be affected by changes.
        
        Args:
            target: Node ID to analyze
        
        Returns:
            Dictionary with count and list of affected nodes
        """
        try:
            downstream = list(nx.descendants(self.graph, target))
            return {
                "target": target,
                "downstream_count": len(downstream),
                "downstream_nodes": downstream,
                "risk_level": "HIGH" if len(downstream) > 10 else "MEDIUM" if len(downstream) > 3 else "LOW"
            }
        except nx.NetworkXError:
            return {
                "target": target,
                "downstream_count": 0,
                "downstream_nodes": [],
                "risk_level": "UNKNOWN"
            }
    
    def find_sources(self) -> List[str]:
        """Find source nodes (no incoming edges)."""
        return [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
    
    def find_sinks(self) -> List[str]:
        """Find sink nodes (no outgoing edges)."""
        return [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]
    
    def find_hubs(self, top_n: int = 5) -> List[str]:
        """Find top hubs by PageRank centrality."""
        try:
            pagerank = nx.pagerank(self.graph)
            sorted_hubs = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
            return [h[0] for h in sorted_hubs[:top_n]]
        except:
            return []
    
    def clear(self):
        """Clear all nodes and edges."""
        self.graph.clear()
        self.metadata.clear()
