from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum

class EdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    PRODUCES = "PRODUCES"
    CONSUMES = "CONSUMES"
    CALLS = "CALLS"
    CONFIGURES = "CONFIGURES"
    DBT_REF = "DBT_REF"
    DEPENDS_ON = "DEPENDS_ON"
    TESTS = "TESTS"
    RELATIONSHIP = "RELATIONSHIP"

class Edge(BaseModel):
    """Edge per spec."""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    confidence_score: float = 1.0
    evidence_type: str = "static"
