"""
SQL Lineage Analyzer - Agent 2 (The Hydrologist)
Extracts table dependency graphs using sqlglot for cross-dialect support.
"""
import re
from pathlib import Path
from typing import List, Dict, Set, Any
import sqlglot
from sqlglot import exp

class SqlLineageAnalyzer:
    """Extract table dependencies from SQL/dbt files using sqlglot."""
    
    def __init__(self, dialect: str = "postgres"):
        self.dialect = dialect
        # Dialects requiring special handling for identifiers
        self.supported_dialects = ["postgres", "bigquery", "snowflake", "duckdb"]

    def parse_sql_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a SQL file and extract lineage information with dialect awareness."""
        result = {
            "source_tables": [],
            "target_tables": [],
            "cte_names": [],
            "dbt_refs": [],
            "dbt_sources": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return result

        # 1. Extract dbt macros (Jinja remains opaque to sqlglot)
        result["dbt_refs"] = re.findall(r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", content)
        
        sources = re.findall(r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", content)
        result["dbt_sources"] = [f"{s[0]}.{s[1]}" for s in sources]

        # 2. Prepare SQL for sqlglot (Remove Jinja to prevent parsing errors)
        clean_sql = re.sub(r"\{\{.*?\}\}", "DBT_PLACEHOLDER_TABLE", content)

        try:
            # Parse into a list of expressions
            expressions = sqlglot.parse(clean_sql, dialect=self.dialect)
            
            for stmt in expressions:
                if not stmt: continue

                # Extract CTEs first to ensure we don't count them as source tables
                for cte in stmt.find_all(exp.CTE):
                    result["cte_names"].append(cte.alias_or_name.lower())

                # Target Table Detection (INSERT, CREATE, MERGE, UPDATE)
                if isinstance(stmt, (exp.Create, exp.Insert, exp.Merge, exp.Update)):
                    target = stmt.find(exp.Table)
                    if target:
                        name = self._format_table_name(target)
                        if name != "dbt_placeholder_table":
                            result["target_tables"].append(name)

                # Source Table Detection (FROM, JOIN)
                for table in stmt.find_all(exp.Table):
                    name = self._format_table_name(table)
                    # Filter out CTEs and placeholders
                    if name.lower() not in result["cte_names"] and name.lower() != "dbt_placeholder_table":
                        result["source_tables"].append(name)

        except Exception as e:
            print(f"Sqlglot error in {file_path.name}: {e}")

        # Deduplicate results
        result["source_tables"] = sorted(list(set(result["source_tables"])))
        result["target_tables"] = sorted(list(set(result["target_tables"])))
        
        return result

    def _format_table_name(self, table_exp: exp.Table) -> str:
        """Helper to extract full names like 'project.dataset.table'."""
        # Use sqlglot's own SQL generator to maintain dialect-specific quoting if needed
        return table_exp.sql(dialect=self.dialect).replace('"', '').replace('`', '')

    def get_lineage_edges(self, file_path: Path) -> List[Dict[str, Any]]:
        """Convert parsed lineage to edge format for the DataLineageGraph."""
        edges = []
        parsed = self.parse_sql_file(file_path)
        model_name = file_path.stem
        
        # Mapping rules for the graph
        mappings = [
            ("source_tables", "READS"),
            ("target_tables", "WRITES"),
            ("dbt_refs", "DEPENDS_ON"),
            ("dbt_sources", "SOURCES_FROM")
        ]

        for key, edge_type in mappings:
            for item in parsed[key]:
                edges.append({
                    "source": item if edge_type != "WRITES" else model_name,
                    "target": model_name if edge_type != "WRITES" else item,
                    "type": edge_type,
                    "file": str(file_path),
                    "dialect": self.dialect
                })
        
        return edges