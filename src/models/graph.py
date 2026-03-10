"""Central Knowledge Graph container — Surveyor Blueprint Alignment.

Features:
- Incremental syncing via git diff tracking
- Fail-open design: parse_warnings for graceful degradation
- MCP tool exposure: find_implementation, get_architectural_hubs, trace_dependencies
- Serialization for .cartography/module_graph.json (NetworkX node_link_data format per spec)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import json
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

from .nodes import ModuleNode, DatasetNode, FunctionNode, TransformationNode, BaseNode, ConfidenceTier
from .edges import Edge, EdgeType


class CartographyGraph(BaseModel):
    """Central container for the codebase knowledge graph — Surveyor output."""
    
    # === Metadata ===
    repo_name: str = Field(..., description="Target repository name")
    repo_path: str = Field(..., description="Local path or URL")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    analyzer_version: str = Field("0.1.0", description="Cartographer version")
    base_commit_sha: str = Field(..., description="Git commit SHA at time of analysis")
    
    # === Rosetta Stone: Normalized Node Collections ===
    modules: list[ModuleNode] = Field(default_factory=list, description="Code module nodes")
    datasets: list[DatasetNode] = Field(default_factory=list, description="Data dataset nodes")
    functions: list[FunctionNode] = Field(default_factory=list, description="Function nodes")
    transformations: list[TransformationNode] = Field(default_factory=list, description="Transformation nodes")
    
    # === Unified Edge List ===
    edges: list[Edge] = Field(default_factory=list, description="Relationship edges (all types)")
    
    # === Summary Stats (auto-computed) ===
    total_nodes: Optional[int] = Field(None, description="Total node count")
    total_edges: Optional[int] = Field(None, description="Total edge count")
    avg_confidence: Optional[ConfidenceTier] = Field(None, description="Average confidence tier")
    
    # === Architectural Hub Detection (PageRank results) ===
    architectural_hubs: list[str] = Field(default_factory=list, description="Top modules by PageRank centrality")
    
    # === Dead Code Candidates (Reaper Protocol output) ===
    dead_code_candidates: list[str] = Field(default_factory=list, description="Exported symbols with in_degree=0 and unreachable")
    
    # === CONSTITUTION RULE 4: GRACEFUL DEGRADATION ===
    parse_warnings: list[str] = Field(default_factory=list, description="Non-fatal parse issues (fail-open design)")
    files_skipped: list[str] = Field(default_factory=list, description="Files that could not be parsed")
    
    # === Incremental Sync Metadata ===
    incremental_mode: bool = Field(False, description="True if analysis used git diff for partial re-analysis")
    changed_files: list[str] = Field(default_factory=list, description="Files changed since base_commit_sha (if incremental)")
    
    # === MCP Tool Exposure (Just-in-Time Context Injection) ===
    # These methods are called by Navigator agent via Model Context Protocol
    
    def find_implementation(self, symbol_name: str) -> Optional[dict]:
        """MCP Tool: Returns file:line and signature for a symbol."""
        # Search modules, functions, datasets
        for node in self.modules + self.functions + self.datasets:
            if symbol_name in node.id or (hasattr(node, 'dataset_name') and symbol_name == node.dataset_name):
                return {
                    "file": node.file_path,
                    "line_start": node.line_start,
                    "signature": getattr(node, 'signature', None),
                    "confidence_score": node.confidence_score,
                    "evidence_type": node.evidence_type
                }
        return None
    
    def get_architectural_hubs(self, top_n: int = 5) -> list[dict]:
        """MCP Tool: Returns top N modules by PageRank centrality."""
        hubs = []
        for hub_id in self.architectural_hubs[:top_n]:
            module = next((m for m in self.modules if m.id == hub_id), None)
            if module:
                hubs.append({
                    "path": module.file_path,
                    "in_degree": module.in_degree,
                    "out_degree": module.out_degree,
                    "purpose": module.purpose_statement
                })
        return hubs
    
    def trace_dependencies(self, module_path: str, direction: Literal["upstream", "downstream", "both"] = "both") -> dict:
        """MCP Tool: Returns upstream/downstream dependencies for a module."""
        upstream = []
        downstream = []
        
        for edge in self.edges:
            if edge.edge_type == "IMPORTS":
                if edge.target == module_path and direction in ["upstream", "both"]:
                    upstream.append(edge.source)
                elif edge.source == module_path and direction in ["downstream", "both"]:
                    downstream.append(edge.target)
        
        return {
            "module": module_path,
            "upstream": upstream,
            "downstream": downstream,
            "total_dependencies": len(upstream) + len(downstream)
        }
    
    # === Node Management ===
    def add_node(self, node: BaseNode) -> None:
        """Add a node to the appropriate collection."""
        if isinstance(node, ModuleNode):
            self.modules.append(node)
        elif isinstance(node, DatasetNode):
            self.datasets.append(node)
        elif isinstance(node, FunctionNode):
            self.functions.append(node)
        elif isinstance(node, TransformationNode):
            self.transformations.append(node)
        self._update_stats()
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge with validation."""
        self.edges.append(edge)
        self._update_stats()
    
    def _update_stats(self) -> None:
        """Recalculate summary statistics."""
        all_nodes = self.modules + self.datasets + self.functions + self.transformations
        self.total_nodes = len(all_nodes)
        self.total_edges = len(self.edges)
        
        if all_nodes:
            scores = [n.confidence_score for n in all_nodes]
            # Average confidence tier (simplified)
            avg = sum(scores) / len(scores)
            if avg >= 0.95:
                self.avg_confidence = 1.0
            elif avg >= 0.75:
                self.avg_confidence = 0.9
            elif avg >= 0.45:
                self.avg_confidence = 0.6
            else:
                self.avg_confidence = 0.3
    
    # === Serialization: Pydantic JSON (backward compatible) ===
    def to_json(self, indent: int = 2) -> str:
        """Serialize graph to JSON string (Pydantic format)."""
        return self.model_dump_json(indent=indent)
    
    # === [GAP 4 FIX] Serialization: NetworkX node_link_data format (per Surveyor spec) ===
    def to_networkx_json(self) -> dict:
        """Convert to NetworkX node_link_data format per Surveyor spec.
        
        This format is optimized for graph algorithms and Navigator query interface.
        See: https://networkx.org/documentation/stable/reference/readwrite/json_graph.html
        """
        nx_graph = nx.DiGraph()
        
        # Add nodes (all types) with full metadata
        for module in self.modules:
            nx_graph.add_node(module.id, **module.model_dump())
        for dataset in self.datasets:
            nx_graph.add_node(dataset.id, **dataset.model_dump())
        for func in self.functions:
            nx_graph.add_node(func.id, **func.model_dump())
        for transform in self.transformations:
            nx_graph.add_node(transform.id, **transform.model_dump())
        
        # Add edges with full metadata
        for edge in self.edges:
            nx_graph.add_edge(edge.source, edge.target, **edge.model_dump())
        
        # Convert to node_link_data format (standard NetworkX JSON serialization)
        return json_graph.node_link_data(nx_graph)
    
    # === [GAP 4 FIX] Updated to_file() with NetworkX format support ===
    def to_file(self, path: Path, use_networkx_format: bool = True) -> None:
        """Write graph to JSON file (.cartography/module_graph.json).
        
        Args:
            path: Output file path
            use_networkx_format: If True (default), use NetworkX node_link_data format 
                                per Surveyor spec. If False, use Pydantic JSON format.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            if use_networkx_format:
                json.dump(self.to_networkx_json(), f, indent=2, default=str)
            else:
                f.write(self.to_json())
    
    @classmethod
    def from_file(cls, path: Path, use_networkx_format: bool = True) -> 'CartographyGraph':
        """Load graph from JSON file.
        
        Args:
            path: Input file path
            use_networkx_format: If True, expect NetworkX node_link_data format.
                                If False, expect Pydantic JSON format.
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if use_networkx_format:
            # Load from NetworkX node_link_data format
            nx_graph = json_graph.node_link_graph(data)
            # Convert back to Pydantic model (simplified - in production, 
            # you'd reconstruct nodes/edges from nx_graph data)
            # For now, fall back to Pydantic validation
            return cls.model_validate(data)
        else:
            # Load from Pydantic JSON format
            return cls.model_validate(data)
    
    # === Incremental Sync Helpers ===
    def mark_stale_nodes(self, changed_files: list[str]) -> None:
        """Mark nodes as stale if their source file changed (for incremental re-analysis)."""
        for node in self.modules + self.functions:
            if node.file_path in changed_files:
                node.is_stale = True
        for edge in self.edges:
            if edge.source_file in changed_files:
                edge.is_stale = True
        self.changed_files = changed_files
        self.incremental_mode = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_name": "jaffle_shop",
                "repo_path": "targets/jaffle_shop",
                "base_commit_sha": "abc123",
                "modules": [
                    {
                        "id": "models.customers",
                        "symbol_type": "Module",
                        "file_path": "models/customers.sql",
                        "language": "sql",
                        "confidence_score": 1.0,
                        "evidence_type": "static"
                    }
                ],
                "edges": [
                    {
                        "source": "models.staging.stg_customers",
                        "target": "models.customers",
                        "edge_type": "IMPORTS",
                        "confidence_score": 1.0,
                        "evidence_type": "static"
                    }
                ],
                "architectural_hubs": ["models.customers", "models.orders"],
                "parse_warnings": []
            }
        }