"""Pydantic models for Knowledge Graph nodes — Rosetta Stone Architecture.

Aligns with Surveyor Blueprint:
- Universal Node Factory: normalized_symbol_type unifies language-specific AST nodes
- Confidence-Based Reaper Protocol: reachability_status + confidence_score tiers
- Evidence-Backed Outputs: confidence_score + evidence_type on every node (Constitution Rule 3)
- Incremental Sync: git_sha + last_analyzed_commit for git diff-based re-analysis
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime


# === Universal Symbol Types (Rosetta Stone Normalization) ===
SymbolType = Literal[
    # Code structures
    "Module", "Class", "Function", "Method", "Variable", "Constant",
    # Data structures
    "Table", "View", "Stream", "Schema", "Column",
    # Config/Infra
    "Pipeline", "Task", "Trigger", "Resource", "Secret",
    # Special
    "GhostNode",  # 3rd-party lib or external dependency
    "Unknown"
]

EvidenceType = Literal["static", "algorithmic", "inference", "heuristic"]
ReachabilityStatus = Literal["reachable", "unreachable", "entry_point", "unknown"]
ConfidenceTier = Literal[1.0, 0.9, 0.6, 0.3]  # Per Confidence-Based Reaper Protocol


class BaseNode(BaseModel):
    """Base class for all knowledge graph nodes — enforces Constitution Rule 3."""
    
    # === Core Identification ===
    id: str = Field(..., description="Unique node identifier (path or qualified name)")
    symbol_type: SymbolType = Field(..., description="Normalized symbol type (Rosetta Stone)")
    
    # === Location ===
    file_path: Optional[str] = Field(None, description="Relative file path from repo root")
    line_start: Optional[int] = Field(None, ge=1, description="Start line number (1-indexed)")
    line_end: Optional[int] = Field(None, ge=1, description="End line number")
    
    # === Semantic Understanding ===
    purpose_statement: Optional[str] = Field(None, description="LLM-generated or static purpose")
    domain_cluster: Optional[str] = Field(None, description="Assigned domain (e.g., 'ingestion', 'ml')")
    
    # === Structural Metrics ===
    cyclomatic_complexity: Optional[int] = Field(None, ge=0, description="Decision node count (if, for, while, etc.)")
    comment_to_code_ratio: Optional[float] = Field(None, ge=0.0, description="Comments / lines of code")
    lines_of_code: Optional[int] = Field(None, ge=0, description="Total lines (excluding blanks/comments)")
    
    # === Git Analytics ===
    git_sha: Optional[str] = Field(None, description="Last commit hash affecting this node")
    last_analyzed_commit: Optional[str] = Field(None, description="Commit SHA at time of analysis")
    change_velocity_30d: int = Field(0, ge=0, description="Git commits in last 30 days (git log --follow)")
    
    # === Reachability Analysis (Confidence-Based Reaper Protocol) ===
    reachability_status: ReachabilityStatus = Field("unknown", description="Reachable from entry points?")
    in_degree: int = Field(0, ge=0, description="Number of incoming edges (imports/calls)")
    out_degree: int = Field(0, ge=0, description="Number of outgoing edges")
    is_dead_code_candidate: bool = Field(False, description="Heuristic: exported but unreachable")
    
    # === Ghost Node Protocol (3rd-party boundary mapping) ===
    is_ghost_node: bool = Field(False, description="True if represents 3rd-party lib or external system")
    external_package: Optional[str] = Field(None, description="Package name if ghost node (e.g., 'pandas')")
    
    # === CONSTITUTION RULE 3: EVIDENCE-BASED OUTPUTS ===
    confidence_score: ConfidenceTier = Field(..., description="Confidence tier per Reaper Protocol: 1.0=static, 0.9=algo, 0.6=inference, 0.3=heuristic")
    evidence_type: EvidenceType = Field(..., description="How this node's data was derived")
    
    # === Incremental Sync Support ===
    is_stale: bool = Field(False, description="True if file changed since last analysis (git diff)")
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_tier(cls, v: ConfidenceTier) -> ConfidenceTier:
        """Ensure confidence matches allowed tiers per Reaper Protocol."""
        if v not in [1.0, 0.9, 0.6, 0.3]:
            raise ValueError('confidence_score must be one of: 1.0, 0.9, 0.6, 0.3')
        return v
    
    @model_validator(mode='after')
    def validate_ghost_node_consistency(self) -> 'BaseNode':
        """Ghost nodes must have external_package set."""
        if self.is_ghost_node and not self.external_package:
            raise ValueError('Ghost nodes must specify external_package')
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "models.customers.build_customer_dim",
                "symbol_type": "Function",
                "file_path": "models/customers.sql",
                "cyclomatic_complexity": 3,
                "comment_to_code_ratio": 0.15,
                "reachability_status": "reachable",
                "confidence_score": 1.0,
                "evidence_type": "static"
            }
        }


class ModuleNode(BaseNode):
    """Represents a code module/file — primary node type for Surveyor."""
    
    # Language-specific metadata (normalized via Rosetta Stone)
    language: Literal["python", "sql", "yaml", "go", "java", "unknown"] = Field(..., description="Source language")
    
    # Import/export analysis
    imports: list[str] = Field(default_factory=list, description="Resolved module paths this file imports")
    exports: list[str] = Field(default_factory=list, description="Public symbols this file exposes")
    
    # Entry point detection (for reachability analysis)
    entry_point_type: Optional[Literal["main_block", "route_handler", "dag_definition", "cli_command", "none"]] = Field(
        None, description="Type of entry point if this module is one"
    )
    
    # Tree-sitter query references (S-Expression Query Library)
    query_files: list[str] = Field(default_factory=list, description="Reference .scm files used for extraction (e.g., 'python/imports.scm')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "models.customers",
                "symbol_type": "Module",
                "file_path": "models/customers.sql",
                "language": "sql",
                "imports": ["staging.stg_customers", "staging.stg_orders"],
                "entry_point_type": None,
                "query_files": ["sql/tables.scm", "sql/lineage.scm"],
                "confidence_score": 1.0,
                "evidence_type": "static"
            }
        }


class DatasetNode(BaseNode):
    """Represents a data table/dataset — for Hydrologist integration."""
    
    # Data identity
    dataset_name: str = Field(..., description="Table/view/stream name")
    storage_type: Literal["table", "view", "stream", "file", "api"] = Field(..., description="Storage mechanism")
    
    # Schema info (if extractable)
    schema_snapshot: Optional[dict] = Field(None, description="Column names + types (if parseable)")
    freshness_sla: Optional[str] = Field(None, description="Expected freshness (e.g., 'daily', 'hourly')")
    
    # Ownership + governance
    owner: Optional[str] = Field(None, description="Team or person responsible")
    is_source_of_truth: bool = Field(False, description="Is this the canonical source for this data?")
    contains_pii: bool = Field(False, description="Flag for PII/security scanning")
    
    # Lineage metadata (populated by Hydrologist)
    upstream_datasets: list[str] = Field(default_factory=list, description="Parent datasets in lineage")
    downstream_datasets: list[str] = Field(default_factory=list, description="Child datasets in lineage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "analytics.customers",
                "symbol_type": "Table",
                "dataset_name": "customers",
                "storage_type": "table",
                "is_source_of_truth": True,
                "confidence_score": 1.0,
                "evidence_type": "static"
            }
        }


class FunctionNode(BaseNode):
    """Represents a function/method — for call graph + complexity analysis."""
    
    # Identity
    qualified_name: str = Field(..., description="module.class.function or module.function")
    parent_module: str = Field(..., description="Parent module path")
    signature: Optional[str] = Field(None, description="Function signature string")
    
    # Usage metrics
    call_count_within_repo: int = Field(0, ge=0, description="Times called within this repo (static analysis)")
    is_public_api: bool = Field(False, description="Is this part of public interface (not _prefixed)?")
    
    # Complexity details
    decision_nodes: Optional[dict] = Field(None, description="Breakdown: {'if': 3, 'for': 2, 'while': 1, ...}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "utils.helpers.normalize_name",
                "symbol_type": "Function",
                "qualified_name": "utils.helpers.normalize_name",
                "parent_module": "utils.helpers",
                "cyclomatic_complexity": 4,
                "decision_nodes": {"if": 2, "for": 1, "try": 1},
                "confidence_score": 1.0,
                "evidence_type": "static"
            }
        }


class TransformationNode(BaseNode):
    """Represents a data transformation (SQL query, pandas op, etc.) — for lineage."""
    
    # Data flow
    source_datasets: list[str] = Field(..., description="Input dataset names/IDs")
    target_datasets: list[str] = Field(..., description="Output dataset names/IDs")
    transformation_type: Literal["select", "join", "aggregate", "filter", "pivot", "custom"] = Field(...)
    
    # Code location
    source_file: str = Field(..., description="File containing transformation")
    sql_query_if_applicable: Optional[str] = Field(None, description="Extracted SQL if parseable")
    
    # Parsing metadata
    parse_method: Literal["sqlglot", "tree-sitter", "regex", "manual"] = Field(..., description="How this transformation was extracted")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "models.customers.build_customer_dim",
                "symbol_type": "Function",
                "source_datasets": ["staging.raw_customers", "staging.raw_orders"],
                "target_datasets": ["analytics.customers"],
                "transformation_type": "join",
                "parse_method": "sqlglot",
                "confidence_score": 0.9,
                "evidence_type": "algorithmic"
            }
        }