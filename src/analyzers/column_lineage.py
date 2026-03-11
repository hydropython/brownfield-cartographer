"""Column-Level Lineage Analyzer  Extract column dependencies for architectural hubs.

Hybrid Heuristic Approach:
1. Syntactic Layer: Extract ref()/source() via regex BEFORE sqlglot parsing
2. Edge Injection: Treat extracted refs as High Confidence (1.0) edges
3. SQLGlot Layer: Extract column-level lineage within models (0.6-0.8 confidence)

This distinguishes CTEs (temporary logic) from Models/Seeds (authoritative assets).

Risk Mitigation: Only run on PageRank-identified hubs.
"""
from pathlib import Path
from typing import List, Dict, Optional, Set
import re

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    sqlglot = None


class ColumnLineageAnalyzer:
    """Extract column-level lineage for high-priority hub tables with dbt awareness."""
    
    # Known dbt seed files in jaffle_shop (from manual reconnaissance)
    KNOWN_SEEDS = {"raw_customers", "raw_orders", "raw_payments"}
    
    def __init__(self, dialect: str = "postgres"):
        self.dialect = dialect
        self.parse_warnings = []
    
    def _extract_dbt_refs(self, content: str) -> List[dict]:
        """
        Syntactic Layer: Extract dbt ref() and source() calls via regex.
        
        Returns high-confidence edges representing the "Sacred Structure" 
        (intended architecture from dbt configs).
        
        Confidence: 1.0 (explicit dbt syntax)
        """
        edges = []
        
        # Extract {{ ref('model_name') }} calls
        ref_pattern = r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        for match in re.finditer(ref_pattern, content):
            ref_name = match.group(1)
            edges.append({
                "ref_type": "model",
                "name": ref_name,
                "is_seed": ref_name in self.KNOWN_SEEDS,
                "confidence": 1.0,
            })
        
        # Extract {{ source('schema', 'table') }} calls
        source_pattern = r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        for match in re.finditer(source_pattern, content):
            schema_name = match.group(1)
            table_name = match.group(2)
            edges.append({
                "ref_type": "source",
                "name": f"{schema_name}.{table_name}",
                "is_seed": False,
                "confidence": 1.0,
            })
        
        return edges
    
    def _get_cte_names(self, content: str) -> Set[str]:
        """
        Extract CTE names to distinguish them from actual model refs.
        
        CTEs are temporary logic (WITH cte_name AS ...).
        Models/Seeds are authoritative assets (via ref()/source()).
        """
        cte_names = set()
        
        # Match: WITH cte_name AS (
        cte_pattern = r"WITH\s+(\w+)\s+AS\s*\("
        for match in re.finditer(cte_pattern, content, re.IGNORECASE):
            cte_names.add(match.group(1).lower())
        
        # Match additional CTEs: , cte_name AS (
        more_cte_pattern = r",\s*(\w+)\s+AS\s*\("
        for match in re.finditer(more_cte_pattern, content, re.IGNORECASE):
            cte_names.add(match.group(1).lower())
        
        return cte_names
    
    def get_column_edges(self, file_path: Path, target_table: str) -> List[dict]:
        """
        Extract column-level lineage edges from a SQL file.
        
        Hybrid approach:
        1. Extract dbt refs (high confidence)  these are REAL dependencies
        2. Extract column lineage via sqlglot (medium confidence)
        3. Filter out CTE names that aren't actual model refs
        """
        edges = []
        
        if not file_path.exists():
            return edges
        
        try:
            raw_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.parse_warnings.append(f"Read error {file_path}: {e}")
            return edges
        
        # === LAYER 1: Syntactic dbt ref extraction (Confidence: 1.0) ===
        dbt_refs = self._extract_dbt_refs(raw_content)
        cte_names = self._get_cte_names(raw_content)
        
        for ref in dbt_refs:
            ref_name = ref["name"]
            
            # Determine source name
            if ref["is_seed"]:
                source_name = f"seeds/{ref_name}.csv"
            elif ref["ref_type"] == "source":
                source_name = ref_name  # Already schema.table format
            else:
                source_name = ref_name
            
            # Add model-to-model edge (not column-level yet)
            edges.append({
                "source": source_name,
                "target": target_table,
                "type": "DBT_REF",
                "subtype": ref["ref_type"],
                "file": str(file_path),
                "confidence": 1.0,  # HIGHEST - explicit dbt syntax
                "is_cte": False,  # Explicitly NOT a CTE
            })
        
        # === LAYER 2: SQLGlot column extraction (Confidence: 0.6-0.8) ===
        if sqlglot:
            # Strip Jinja for sqlglot parsing
            clean_content = self._strip_jinja(raw_content)
            
            try:
                parsed = sqlglot.parse(clean_content, read=self.dialect)
                if parsed:
                    col_edges = self._extract_columns_sqlglot(
                        parsed, target_table, str(file_path), cte_names, dbt_refs
                    )
                    edges.extend(col_edges)
            except Exception as e:
                self.parse_warnings.append(f"SQL parse error {file_path}: {e}")
        
        return edges
    
    def _strip_jinja(self, content: str) -> str:
        """Strip Jinja template syntax for sqlglot parsing."""
        # Replace {{ ref('name') }} with the table name
        content = re.sub(r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", r"\1", content)
        # Replace {{ source('schema', 'table') }} with schema.table
        content = re.sub(r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", r"\1.\2", content)
        # Remove comments
        content = re.sub(r"\{#.*?#\}", "", content, flags=re.DOTALL)
        # Remove {% %} blocks
        content = re.sub(r"\{\%.*?\%\}", "", content, flags=re.DOTALL)
        # Remove remaining {{ }}
        content = re.sub(r"\{\{.*?\}\}", "", content)
        return content
    
    def _extract_columns_sqlglot(
        self, 
        parsed: list, 
        target_table: str, 
        file_path: str,
        cte_names: Set[str],
        dbt_refs: List[dict]
    ) -> List[dict]:
        """
        Extract column edges using sqlglot, with CTE filtering.
        
        Key: Don't treat CTE names as source tables unless they're also dbt refs.
        """
        edges = []
        
        # Build a map of CTE names to their resolved model refs
        cte_to_model = {}
        for ref in dbt_refs:
            # If a CTE name matches a ref name, resolve it
            if ref["name"].lower() in cte_names:
                cte_to_model[ref["name"].lower()] = ref["name"]
        
        for stmt in parsed:
            if not stmt:
                continue
            
            source_tables = []
            
            # Find source tables from FROM/JOIN
            for select in stmt.find_all(exp.Select):
                from_clause = select.args.get("from")
                if from_clause:
                    table_name = from_clause.this.name
                    # Skip if it's a CTE that's not a resolved ref
                    if table_name.lower() not in cte_names or table_name.lower() in cte_to_model:
                        source_tables.append(table_name)
                
                for join in select.args.get("joins", []):
                    table_name = join.this.name
                    if table_name.lower() not in cte_names or table_name.lower() in cte_to_model:
                        source_tables.append(table_name)
                
                # Extract columns
                for col_expr in select.selects:
                    col_name = self._get_column_name(col_expr)
                    if not col_name or col_name == "*":
                        continue
                    
                    for src_table in source_tables:
                        # Resolve CTE to actual model if possible
                        resolved_table = cte_to_model.get(src_table.lower(), src_table)
                        
                        edges.append({
                            "source": f"{resolved_table}.{col_name}",
                            "target": f"{target_table}.{col_name}",
                            "type": "COLUMN_LINEAGE",
                            "file": file_path,
                            "confidence": self._get_confidence(col_expr),
                        })
        
        return edges
    
    def _get_column_name(self, col_expr) -> Optional[str]:
        """Extract column name from a column expression."""
        if isinstance(col_expr, exp.Column):
            return col_expr.name
        alias = col_expr.alias
        if alias:
            return alias
        return str(col_expr)[:50]
    
    def _get_confidence(self, col_expr) -> float:
        """Assign confidence score based on expression complexity."""
        expr_str = str(col_expr)
        if isinstance(col_expr, exp.Column):
            return 0.8
        if any(kw in expr_str.upper() for kw in ["CASE", "COALESCE", "CAST", "CONCAT"]):
            return 0.6
        if any(kw in expr_str.upper() for kw in ["JSON", "LATERAL", "UNNEST"]):
            return 0.4
        return 0.6
