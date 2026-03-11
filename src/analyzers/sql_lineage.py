"""SQL Lineage Analyzer  sqlglot-based table dependency extraction.

Extracts:
- Source tables (FROM, JOIN clauses)
- Target tables (INSERT, CREATE, MERGE)
- CTEs (Common Table Expressions)
- dbt ref() and source() function calls
"""
from pathlib import Path
from typing import Optional
import sqlglot
from sqlglot import exp
import re


class SqlLineageAnalyzer:
    """Extract table dependencies from SQL files using sqlglot."""
    
    def __init__(self, dialect: str = "postgres"):
        self.dialect = dialect
    
    def parse_sql_file(self, file_path: Path) -> dict:
        """Parse a SQL file and extract lineage information."""
        result = {
            "source_tables": [],
            "target_tables": [],
            "cte_tables": [],
            "dbt_refs": [],
            "dbt_sources": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return result
        
        # Extract dbt ref() calls: {{ ref('table_name') }}
        ref_pattern = r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        for match in re.finditer(ref_pattern, content):
            result["dbt_refs"].append(match.group(1))
        
        # Extract dbt source() calls: {{ source('schema', 'table') }}
        source_pattern = r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        for match in re.finditer(source_pattern, content):
            result["dbt_sources"].append({
                "schema": match.group(1),
                "table": match.group(2),
            })
        
        # Parse SQL with sqlglot
        try:
            statements = sqlglot.parse(content, dialect=self.dialect)
            
            for stmt in statements:
                if stmt is None:
                    continue
                
                # Extract target tables (INSERT, CREATE, MERGE)
                if isinstance(stmt, exp.Insert):
                    target = stmt.find(exp.Table)
                    if target and target.name:
                        result["target_tables"].append(target.name)
                
                elif isinstance(stmt, exp.Create):
                    target = stmt.find(exp.Table)
                    if target and target.name:
                        result["target_tables"].append(target.name)
                    select = stmt.find(exp.Select)
                    if select:
                        self._extract_source_tables(select, result)
                
                elif isinstance(stmt, exp.Select):
                    self._extract_source_tables(stmt, result)
                
                elif isinstance(stmt, exp.Merge):
                    target = stmt.find(exp.Table)
                    if target and target.name:
                        result["target_tables"].append(target.name)
                    self._extract_source_tables(stmt, result)
        
        except Exception:
            pass  # Graceful degradation
        
        # Deduplicate
        result["source_tables"] = list(set(result["source_tables"]))
        result["target_tables"] = list(set(result["target_tables"]))
        result["cte_tables"] = list(set(result["cte_tables"]))
        
        return result
    
    def _extract_source_tables(self, statement, result: dict) -> None:
        """Extract all source tables from a SELECT statement."""
        for table in statement.find_all(exp.Table):
            if table.name and table.name not in result["cte_tables"]:
                result["source_tables"].append(table.name)
        
        with_clause = statement.find(exp.With)
        if with_clause:
            for cte in with_clause.find_all(exp.CTE):
                if cte.alias:
                    result["cte_tables"].append(cte.alias)
        
        for join in statement.find_all(exp.Join):
            table = join.find(exp.Table)
            if table and table.name and table.name not in result["cte_tables"]:
                result["source_tables"].append(table.name)
    
    def get_lineage_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed lineage to edge format for graph."""
        edges = []
        parsed = self.parse_sql_file(file_path)
        model_name = file_path.stem
        
        # Source tables -> this model (READS edges)
        for table in parsed["source_tables"]:
            edges.append({
                "source": table,
                "target": model_name,
                "type": "READS",
                "file": str(file_path),
            })
        
        # This model -> target tables (WRITES edges)
        for table in parsed["target_tables"]:
            edges.append({
                "source": model_name,
                "target": table,
                "type": "WRITES",
                "file": str(file_path),
            })
        
        # dbt refs -> this model (DEPENDS_ON edges)
        for ref in parsed["dbt_refs"]:
            edges.append({
                "source": ref,
                "target": model_name,
                "type": "DEPENDS_ON",
                "file": str(file_path),
            })
        
        # dbt sources -> this model (SOURCES edges)
        for src in parsed["dbt_sources"]:
            source_name = f"{src['schema']}.{src['table']}"
            edges.append({
                "source": source_name,
                "target": model_name,
                "type": "SOURCES",
                "file": str(file_path),
            })
        
        return edges
