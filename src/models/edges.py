from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum

class EdgeType(str, Enum):
    """ALL required edge types per spec."""
    IMPORTS = "IMPORTS"              #  source_module  target_module
    PRODUCES = "PRODUCES"            #  transformation  dataset
    CONSUMES = "CONSUMES"            #  transformation  dataset
    CALLS = "CALLS"                  #  function  function
    CONFIGURES = "CONFIGURES"        #  config_file  module/pipeline
    DBT_REF = "DBT_REF"              #  dbt-specific
    DEPENDS_ON = "DEPENDS_ON"        #  SQL-specific
    TESTS = "TESTS"                  #  dbt-specific
    RELATIONSHIP = "RELATIONSHIP"    #  dbt-specific

class Edge(BaseModel):
    """Edge per spec - ALL required fields."""
    source: str                                       #  Required
    target: str                                       #  Required
    edge_type: EdgeType                               #  Required
    weight: float = 1.0                               #  Required (import_count)
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    confidence_score: float = 1.0
    evidence_type: str = "static"
