from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union, Dict, Any
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

class StorageType(str, Enum):
    TABLE = "table"
    FILE = "file"
    STREAM = "stream"
    API = "api"

# === Base Node ===

class BaseNode(BaseModel):
    """Base class for all node types."""
    id: str
    symbol_type: SymbolType
    confidence_score: float = 1.0
    evidence_type: EvidenceType = EvidenceType.STATIC

# === ModuleNode (Surveyor) - ALL required fields ===

class ModuleNode(BaseNode):
    """Module node per Surveyor spec - ALL required fields."""
    symbol_type: SymbolType = SymbolType.MODULE
    path: str = ""                                    #  Required
    language: str = "python"                          #  Required
    purpose_statement: Optional[str] = None           #  Required (LLM Phase 3)
    domain_cluster: Optional[str] = None              #  Required (infer from path)
    complexity_score: float = 0.0                     #  Required (LOC/cyclomatic)
    change_velocity_30d: int = 0                      #  Required (git commits)
    is_dead_code_candidate: bool = False              #  Required
    last_modified: Optional[datetime] = None          #  Required (file mtime)
    imports: List[str] = []
    exports: List[str] = []
    in_degree: int = 0
    out_degree: int = 0
    file_path: str = ""
    entry_point_type: Optional[str] = None
    reachability_status: Optional[str] = None
    is_ghost_node: bool = False
    external_package: Optional[str] = None

# === DatasetNode (Hydrologist) - ALL required fields ===

class DatasetNode(BaseNode):
    """Dataset node per Hydrologist spec - ALL required fields."""
    symbol_type: SymbolType = SymbolType.DATASET
    name: str = ""                                    #  Required
    storage_type: StorageType = StorageType.FILE      #  Required
    schema_snapshot: Optional[Dict[str, Any]] = None  #  Required (from YAML)
    freshness_sla: Optional[str] = None               #  Required
    owner: Optional[str] = None                       #  Required
    is_source_of_truth: bool = False                  #  Required (seeds=True)

# === FunctionNode (Future) - ALL required fields ===

class FunctionNode(BaseNode):
    """Function node - ALL required fields."""
    symbol_type: SymbolType = SymbolType.FUNCTION
    qualified_name: str = ""                          #  Required
    parent_module: str = ""                           #  Required
    signature: str = ""                               #  Required
    purpose_statement: Optional[str] = None           #  Required (LLM Phase 3)
    call_count_within_repo: int = 0                   #  Required
    is_public_api: bool = True                        #  Required

# === TransformationNode (Hydrologist) - ALL required fields ===

class TransformationNode(BaseNode):
    """Transformation node - ALL required fields."""
    symbol_type: SymbolType = SymbolType.TRANSFORMATION
    source_datasets: List[str] = []                   #  Required
    target_datasets: List[str] = []                   #  Required
    transformation_type: str = "sql"                  #  Required
    source_file: str = ""                             #  Required
    line_range: tuple = (0, 0)                        #  Required
    sql_query_if_applicable: Optional[str] = None     #  Required

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
