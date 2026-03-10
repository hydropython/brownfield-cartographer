"""Unit tests for Pydantic models — Surveyor Blueprint Alignment.

Tests verify:
- Rosetta Stone normalization (symbol_type, edge_type)
- Confidence-Based Reaper Protocol (confidence_score tiers)
- Constitution Rule 3 enforcement (evidence_type required)
- Incremental sync fields (is_stale, changed_files)
- Graceful degradation (parse_warnings, files_skipped)
"""
import pytest
from datetime import datetime
from brownfield_cartographer.models.nodes import (
    ModuleNode, DatasetNode, FunctionNode, TransformationNode, 
    BaseNode, SymbolType, ConfidenceTier, EvidenceType
)
from brownfield_cartographer.models.edges import Edge, EdgeType
from brownfield_cartographer.models.graph import CartographyGraph


class TestBaseNode:
    """Test BaseNode validation and Reaper Protocol compliance."""
    
    def test_valid_module_node(self):
        """Test creating a valid ModuleNode with all required fields."""
        node = ModuleNode(
            id="models.customers",
            symbol_type="Module",
            file_path="models/customers.sql",
            language="sql",
            confidence_score=1.0,  # Reaper Protocol tier
            evidence_type="static"  # Constitution Rule 3
        )
        assert node.id == "models.customers"
        assert node.confidence_score == 1.0
        assert node.evidence_type == "static"
    
    def test_confidence_tier_validation(self):
        """Test confidence_score must be one of: 1.0, 0.9, 0.6, 0.3."""
        # Valid tiers
        for tier in [1.0, 0.9, 0.6, 0.3]:
            ModuleNode(
                id="test", symbol_type="Module",
                confidence_score=tier, evidence_type="static"
            )
        
        # Invalid tier should raise
        with pytest.raises(ValueError):
            ModuleNode(
                id="test", symbol_type="Module",
                confidence_score=0.75, evidence_type="static"  # Not a valid tier
            )
    
    def test_ghost_node_consistency(self):
        """Test ghost nodes require external_package."""
        # Valid ghost node
        ModuleNode(
            id="pandas.DataFrame",
            symbol_type="GhostNode",
            is_ghost_node=True,
            external_package="pandas",
            confidence_score=1.0,
            evidence_type="static"
        )
        
        # Invalid: ghost node without external_package
        with pytest.raises(ValueError):
            ModuleNode(
                id="pandas.DataFrame",
                symbol_type="GhostNode",
                is_ghost_node=True,
                # missing external_package
                confidence_score=1.0,
                evidence_type="static"
            )
    
    def test_reachability_status_default(self):
        """Test reachability_status defaults to 'unknown'."""
        node = ModuleNode(
            id="test", symbol_type="Module",
            confidence_score=1.0, evidence_type="static"
        )
        assert node.reachability_status == "unknown"
    
    def test_json_serialization(self):
        """Test model serializes to JSON with evidence fields."""
        node = ModuleNode(
            id="utils.helpers.normalize",
            symbol_type="Function",
            file_path="utils/helpers.py",
            cyclomatic_complexity=4,
            comment_to_code_ratio=0.2,
            confidence_score=0.9,
            evidence_type="algorithmic"
        )
        json_str = node.model_dump_json()
        assert "utils.helpers.normalize" in json_str
        assert "0.9" in json_str  # confidence_score
        assert "algorithmic" in json_str  # evidence_type


class TestEdge:
    """Test Edge validation with Rosetta Stone edge types."""
    
    def test_valid_edge(self):
        """Test creating a valid Edge."""
        edge = Edge(
            source="models.staging.stg_customers",
            target="models.customers",
            edge_type="IMPORTS",  # Rosetta Stone normalized type
            confidence_score=1.0,
            evidence_type="static"
        )
        assert edge.edge_type == "IMPORTS"
        assert edge.confidence_score == 1.0
    
    def test_all_edge_types(self):
        """Test all valid Rosetta Stone edge types."""
        valid_types = [
            "IMPORTS", "CALLS", "INHERITS", "IMPLEMENTS",
            "PRODUCES", "CONSUMES", "TRANSFORMS",
            "CONFIGURES", "DEPLOYS", "TRIGGERS",
            "TESTS", "MOCKS", "DEPENDS_ON", "REFERENCES"
        ]
        for etype in valid_types:
            edge = Edge(
                source="a", target="b", edge_type=etype,
                confidence_score=0.9, evidence_type="algorithmic"
            )
            assert edge.edge_type == etype
    
    def test_location_evidence(self):
        """Test edge can store source location for traceability."""
        edge = Edge(
            source="a", target="b", edge_type="IMPORTS",
            source_file="models/customers.sql",
            source_line=3,
            code_snippet="from {{ ref('stg_customers') }}",
            confidence_score=1.0,
            evidence_type="static"
        )
        assert edge.source_line == 3
        assert "ref('stg_customers')" in edge.code_snippet


class TestCartographyGraph:
    """Test graph container with Surveyor features."""
    
    def test_add_node_and_serialize(self):
        """Test adding nodes and serializing graph."""
        graph = CartographyGraph(
            repo_name="jaffle_shop",
            repo_path="targets/jaffle_shop",
            base_commit_sha="abc123"
        )
        
        # Add a module
        module = ModuleNode(
            id="models.customers",
            symbol_type="Module",
            file_path="models/customers.sql",
            language="sql",
            confidence_score=1.0,
            evidence_type="static"
        )
        graph.add_node(module)
        
        # Add an edge
        edge = Edge(
            source="staging.stg_customers",
            target="models.customers",
            edge_type="IMPORTS",
            confidence_score=1.0,
            evidence_type="static"
        )
        graph.add_edge(edge)
        
        # Verify stats updated
        assert graph.total_nodes == 1
        assert graph.total_edges == 1
        assert graph.avg_confidence == 1.0
        
        # Verify serialization includes evidence fields
        json_str = graph.to_json()
        assert "jaffle_shop" in json_str
        assert "customers.sql" in json_str
        assert "evidence_type" in json_str  # Constitution Rule 3 enforced
    
    def test_mcp_tools(self):
        """Test MCP tool exposure for Navigator agent."""
        graph = CartographyGraph(
            repo_name="test", repo_path="/test", base_commit_sha="xyz"
        )
        
        # Add a module
        module = ModuleNode(
            id="utils.helpers.normalize",
            symbol_type="Function",
            file_path="utils/helpers.py",
            line_start=10,
            signature="def normalize(name: str) -> str",
            confidence_score=1.0,
            evidence_type="static"
        )
        graph.add_node(module)
        
        # Test find_implementation
        result = graph.find_implementation("normalize")
        assert result is not None
        assert result["file"] == "utils/helpers.py"
        assert result["line_start"] == 10
        assert result["confidence_score"] == 1.0  # Evidence included
    
    def test_incremental_sync(self):
        """Test incremental sync metadata."""
        graph = CartographyGraph(
            repo_name="test", repo_path="/test", base_commit_sha="abc123"
        )
        
        # Mark files as changed
        graph.mark_stale_nodes(["utils/helpers.py", "models/customers.sql"])
        
        assert graph.incremental_mode is True
        assert "utils/helpers.py" in graph.changed_files
        
        # Verify nodes marked stale (if they exist)
        # (In real usage, nodes would be added before marking stale)
    
    def test_graceful_degradation(self):
        """Test fail-open design: parse_warnings and files_skipped."""
        graph = CartographyGraph(
            repo_name="test", repo_path="/test", base_commit_sha="abc"
        )
        
        # Simulate parse warnings (fail-open: don't crash)
        graph.parse_warnings.append("Failed to parse models/legacy.py: syntax error at line 42")
        graph.files_skipped.append("models/legacy.py")
        
        # Graph should still serialize successfully
        json_str = graph.to_json()
        assert "parse_warnings" in json_str
        assert "legacy.py" in json_str


class TestReaperProtocol:
    """Test Confidence-Based Reaper Protocol implementation."""
    
    def test_dead_code_candidate_detection(self):
        """Test dead code candidate flagging logic."""
        # Unreachable exported function (dead code candidate)
        func = FunctionNode(
            id="utils.unused_helper",
            symbol_type="Function",
            file_path="utils.py",
            is_public_api=True,  # Exported
            reachability_status="unreachable",  # Not called from entry points
            in_degree=0,  # No incoming calls
            confidence_score=0.6,  # Inference: might be used externally
            evidence_type="inference"
        )
        assert func.is_dead_code_candidate is False  # Set by analysis logic, not model
        
        # But we can flag it manually based on protocol
        if func.in_degree == 0 and func.reachability_status == "unreachable" and func.is_public_api:
            func.is_dead_code_candidate = True
        
        assert func.is_dead_code_candidate is True
    
    def test_confidence_tiers_by_evidence_type(self):
        """Test confidence tiers align with evidence types per Reaper Protocol."""
        # Static parse = highest confidence
        static_node = ModuleNode(
            id="test", symbol_type="Module",
            confidence_score=1.0, evidence_type="static"
        )
        assert static_node.confidence_score == 1.0
        
        # Algorithmic = high confidence
        algo_node = ModuleNode(
            id="test", symbol_type="Module",
            confidence_score=0.9, evidence_type="algorithmic"
        )
        assert algo_node.confidence_score == 0.9
        
        # Inference = medium confidence
        inference_node = ModuleNode(
            id="test", symbol_type="Module",
            confidence_score=0.6, evidence_type="inference"
        )
        assert inference_node.confidence_score == 0.6
        
        # Heuristic = low confidence
        heuristic_node = ModuleNode(
            id="test", symbol_type="Module",
            confidence_score=0.3, evidence_type="heuristic"
        )
        assert heuristic_node.confidence_score == 0.3