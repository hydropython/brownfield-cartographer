from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from datetime import datetime
from enum import Enum

# === Enum Types ===

class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EvidenceType(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    HEURISTIC = "heuristic"
    LLM = "llm"

class SymbolType(str, Enum):
    MODULE = "Module"
    DATASET = "Dataset"
    FUNCTION = "Function"
    TRANSFORMATION = "Transformation"
    TEST = "Test"
    CONFIG = "Config"
    EXTERNAL = "External"

# === Base Node ===

class BaseNode(BaseModel):
    """Base class for all node types."""
    id: str
    symbol_type: SymbolType
    confidence_score: float = 1.0
    evidence_type: EvidenceType = EvidenceType.STATIC

# === Node Types ===

class ModuleNode(BaseNode):
    """Module node per Surveyor spec."""
    symbol_type: SymbolType = SymbolType.MODULE
    path: str = ""
    language: str = "python"
    purpose_statement: Optional[str] = None
    domain_cluster: Optional[str] = None
    complexity_score: float = 0.0
    change_velocity_30d: int = 0
    is_dead_code_candidate: bool = False
    last_modified: Optional[datetime] = None
    imports: List[str] = []
    exports: List[str] = []
    in_degree: int = 0
    out_degree: int = 0
    file_path: str = ""
    entry_point_type: Optional[str] = None
    reachability_status: Optional[str] = None
    is_ghost_node: bool = False
    external_package: Optional[str] = None

class DatasetNode(BaseNode):
    """Dataset node per spec."""
    symbol_type: SymbolType = SymbolType.DATASET
    name: str = ""
    storage_type: Literal["table", "file", "stream", "api"] = "table"
    schema_snapshot: Optional[dict] = None
    freshness_sla: Optional[str] = None
    owner: Optional[str] = None
    is_source_of_truth: bool = False

class FunctionNode(BaseNode):
    """Function node per spec."""
    symbol_type: SymbolType = SymbolType.FUNCTION
    qualified_name: str = ""
    parent_module: str = ""
    signature: str = ""
    purpose_statement: Optional[str] = None
    call_count_within_repo: int = 0
    is_public_api: bool = True

class TransformationNode(BaseNode):
    """Transformation node per spec."""
    symbol_type: SymbolType = SymbolType.TRANSFORMATION
    source_datasets: List[str] = []
    target_datasets: List[str] = []
    transformation_type: str = "sql"
    source_file: str = ""
    line_range: tuple = (0, 0)
    sql_query_if_applicable: Optional[str] = None

# === Graph Container ===

class CartographyGraph(BaseModel):
    """Container for the knowledge graph."""
    modules: List[ModuleNode] = []
    datasets: List[DatasetNode] = []
    functions: List[FunctionNode] = []
    transformations: List[TransformationNode] = []
    total_nodes: int = 0
    total_edges: int = 0
    architectural_hubs: List[str] = []
    dead_code_candidates: List[str] = []
    parse_warnings: List[str] = []
    
    def add_node(self, node: ModuleNode) -> None:
        self.modules.append(node)
        self.total_nodes += 1
    
    def add_edge(self, edge: "Edge") -> None:
        self.total_edges += 1
    
    def _update_stats(self) -> None:
        self.total_nodes = len(self.modules) + len(self.datasets) + len(self.functions) + len(self.transformations)
    
    def to_file(self, path: str) -> None:
        import json
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))
