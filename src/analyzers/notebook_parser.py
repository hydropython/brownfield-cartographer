"""Notebook Parser  Extract data operations from Jupyter notebooks.

Parses .ipynb files to find:
- Data source references (pandas read operations, file paths)
- Output paths (write operations, export paths)
- SQL queries in notebook cells
"""
from pathlib import Path
from typing import Optional, List, Dict
import json
import re


class NotebookParser:
    """Extract data flow operations from Jupyter notebooks."""
    
    def __init__(self):
        self.parse_warnings = []
    
    def parse_notebook(self, file_path: Path) -> dict:
        """Parse a Jupyter notebook file.
        
        Returns:
            dict with keys:
                - sources: list of data sources
                - sinks: list of data sinks
                - sql_queries: list of SQL queries found
                - cell_count: total number of cells
                - file_path: str
        """
        result = {
            "sources": [],
            "sinks": [],
            "sql_queries": [],
            "cell_count": 0,
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
            notebook = json.loads(content)
        except json.JSONDecodeError as e:
            self.parse_warnings.append(f"Invalid JSON {file_path}: {e}")
            return result
        except Exception as e:
            self.parse_warnings.append(f"Read error {file_path}: {e}")
            return result
        
        # Get cells
        cells = notebook.get("cells", [])
        result["cell_count"] = len(cells)
        
        # Patterns for data operations
        pandas_read_patterns = [
            (r"pd\.read_csv\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_csv"),
            (r"pd\.read_sql\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_sql"),
            (r"pd\.read_parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_parquet"),
            (r"pd\.read_excel\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_excel"),
        ]
        
        pandas_write_patterns = [
            (r"\.to_csv\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_csv"),
            (r"\.to_sql\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_sql"),
            (r"\.to_parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_parquet"),
        ]
        
        sql_patterns = [
            r"SELECT\s+.+\s+FROM\s+\w+",
            r"WITH\s+\w+\s+AS\s*\(",
        ]
        
        # Analyze each cell
        for i, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "")
            source_lines = cell.get("source", [])
            
            # Convert source to string
            if isinstance(source_lines, list):
                source = "".join(source_lines)
            else:
                source = source_lines
            
            if cell_type == "code":
                # Find pandas read operations
                for pattern, op_type in pandas_read_patterns:
                    for match in re.finditer(pattern, source):
                        result["sources"].append({
                            "type": op_type,
                            "path": match.group(1),
                            "cell": i + 1,
                            "file": str(file_path),
                        })
                
                # Find pandas write operations
                for pattern, op_type in pandas_write_patterns:
                    for match in re.finditer(pattern, source):
                        result["sinks"].append({
                            "type": op_type,
                            "path": match.group(1),
                            "cell": i + 1,
                            "file": str(file_path),
                        })
                
                # Find SQL queries
                for pattern in sql_patterns:
                    for match in re.finditer(pattern, source, re.IGNORECASE):
                        result["sql_queries"].append({
                            "query": match.group(0)[:100],
                            "cell": i + 1,
                            "file": str(file_path),
                        })
        
        return result
    
    def get_lineage_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed notebook to edge format for graph."""
        edges = []
        result = self.parse_notebook(file_path)
        
        # Get notebook name
        notebook_name = file_path.stem
        
        # Sources -> this notebook (READS edges)
        for source in result["sources"]:
            edges.append({
                "source": source["path"],
                "target": notebook_name,
                "type": "READS",
                "operation": source["type"],
                "cell": source["cell"],
                "file": str(file_path),
            })
        
        # This notebook -> sinks (WRITES edges)
        for sink in result["sinks"]:
            edges.append({
                "source": notebook_name,
                "target": sink["path"],
                "type": "WRITES",
                "operation": sink["type"],
                "cell": sink["cell"],
                "file": str(file_path),
            })
        
        # SQL queries -> notebook (USES edges)
        for sql in result["sql_queries"]:
            edges.append({
                "source": "SQL_QUERY",
                "target": notebook_name,
                "type": "USES",
                "query": sql["query"][:50],
                "cell": sql["cell"],
                "file": str(file_path),
            })
        
        return edges
