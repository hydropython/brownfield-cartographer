"""Pydantic models for Knowledge Graph edges — Rosetta Stone Architecture.

Aligns with Surveyor Blueprint:
- Unified edge types for cross-language graph traversal
- Confidence tiers per Reaper Protocol
- Evidence tracking per Constitution Rule 3
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


# === Unified Edge Types (Rosetta Stone Normalization) ===
EdgeType = Literal[
    # Code relationships
    "IMPORTS",           # module → module (Python import, SQL ref(), YAML config ref)
    "CALLS",             # function → function
    "INHERITS",          # class → parent class
    "IMPLEMENTS",        # class → interface/protocol
    
    # Data relationships
    "PRODUCES",          # transformation → dataset
    "CONSUMES",          # transformation ← dataset
    "TRANSFORMS",        # dataset → dataset (via transformation)
    
    # Config/Infra relationships
    "CONFIGURES",        # config file → module/pipeline
    "DEPLOYS",           # infra definition → resource
    "TRIGGERS",          # scheduler → pipeline/task
    
    # Test relationships
    "TESTS",             # test file → module
    "MOCKS",             # test → external dependency
    
    # Generic
    "DEPENDS_ON",        # fallback for unclear relationships
    "REFERENCES",        # soft reference (e.g., docstring mention)
]

EvidenceType = Literal["static", "algorithmic", "inference", "heuristic"]
ConfidenceTier = Literal[1.0, 0.9, 0.6, 0.3]


class Edge(BaseModel):
    """Represents a relationship between two nodes in the knowledge graph."""
    
    # === Connection ===
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    
    # === Relationship Type (Normalized) ===
    edge_type: EdgeType = Field(..., description="Normalized relationship type (Rosetta Stone)")
    
    # === Weight/Strength ===
    weight: float = Field(1.0, ge=0.0, description="Edge weight (e.g., import count, call frequency)")
    
    # === Location Evidence (for traceability) ===
    source_file: Optional[str] = Field(None, description="File where relationship was detected")
    source_line: Optional[int] = Field(None, ge=1, description="Line number in source file")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet (redacted if sensitive)")
    
    # === CONSTITUTION RULE 3: EVIDENCE-BASED OUTPUTS ===
    confidence_score: ConfidenceTier = Field(..., description="Confidence tier: 1.0=static parse, 0.9=algo, 0.6=inference, 0.3=heuristic")
    evidence_type: EvidenceType = Field(..., description="How this edge was derived")
    
    # === Incremental Sync Support ===
    is_stale: bool = Field(False, description="True if source file changed since last analysis")
    
    # === Optional Metadata ===
    meta: Optional[dict] = Field(None, description="Additional context (e.g., git blame, parser version)")  # ✅ FIXED: Added colon
    
    @field_validator('confidence_score')
    @classmethod
    def validate_confidence_tier(cls, v: ConfidenceTier) -> ConfidenceTier:
        if v not in [1.0, 0.9, 0.6, 0.3]:
            raise ValueError('confidence_score must be one of: 1.0, 0.9, 0.6, 0.3')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "models.staging.stg_customers",
                "target": "models.customers",
                "edge_type": "IMPORTS",
                "weight": 1.0,
                "source_file": "models/customers.sql",
                "source_line": 3,
                "code_snippet": "from {{ ref('stg_customers') }}",
                "confidence_score": 1.0,
                "evidence_type": "static"
            }
        }
    