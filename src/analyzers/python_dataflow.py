"""Python Data Flow Analyzer  Extract data operations from Python files.

Uses tree-sitter to find:
- pandas: read_csv(), read_sql(), read_parquet(), to_csv(), to_sql()
- SQLAlchemy: execute(), query(), from_statement()
- PySpark: read.csv(), read.parquet(), write.jdbc(), write.save()

Handles f-strings and variable references gracefully (logs as 'dynamic reference').
"""
from pathlib import Path
from typing import Optional, List, Dict
import re


class PythonDataFlowAnalyzer:
    """Extract data flow operations from Python files using tree-sitter."""
    
    def __init__(self):
        self.dynamic_references = []
        self.parse_warnings = []
    
    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a Python file for data flow operations.
        
        Returns:
            dict with keys:
                - sources: list of data sources (read operations)
                - sinks: list of data sinks (write operations)
                - transformations: list of transformation operations
                - dynamic_references: list of unresolved f-string/variable refs
                - file_path: str
        """
        result = {
            "sources": [],
            "sinks": [],
            "transformations": [],
            "dynamic_references": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.parse_warnings.append(f"Read error {file_path}: {e}")
            return result
        
        # === pandas read operations (SOURCES) ===
        pandas_read_patterns = [
            (r"pd\.read_csv\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_csv"),
            (r"pd\.read_sql\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_sql"),
            (r"pd\.read_parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_parquet"),
            (r"pd\.read_excel\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_excel"),
            (r"pd\.read_json\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_json"),
            (r"pandas\.read_csv\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.read_csv"),
        ]
        
        for pattern, op_type in pandas_read_patterns:
            for match in re.finditer(pattern, content):
                result["sources"].append({
                    "type": op_type,
                    "path": match.group(1),
                    "line": content[:match.start()].count("\n") + 1,
                    "dynamic": False,
                })
        
        # === pandas write operations (SINKS) ===
        pandas_write_patterns = [
            (r"\.to_csv\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_csv"),
            (r"\.to_sql\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_sql"),
            (r"\.to_parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_parquet"),
            (r"\.to_excel\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_excel"),
            (r"\.to_json\s*\(\s*['\"]([^'\"]+)['\"]", "pandas.to_json"),
        ]
        
        for pattern, op_type in pandas_write_patterns:
            for match in re.finditer(pattern, content):
                result["sinks"].append({
                    "type": op_type,
                    "path": match.group(1),
                    "line": content[:match.start()].count("\n") + 1,
                    "dynamic": False,
                })
        
        # === SQLAlchemy operations ===
        sqlalchemy_patterns = [
            (r"execute\s*\(\s*['\"]([^'\"]+)['\"]", "sqlalchemy.execute"),
            (r"\.query\s*\(\s*['\"]([^'\"]+)['\"]", "sqlalchemy.query"),
            (r"from_statement\s*\(\s*['\"]([^'\"]+)['\"]", "sqlalchemy.from_statement"),
        ]
        
        for pattern, op_type in sqlalchemy_patterns:
            for match in re.finditer(pattern, content):
                result["sources"].append({
                    "type": op_type,
                    "query": match.group(1),
                    "line": content[:match.start()].count("\n") + 1,
                    "dynamic": False,
                })
        
        # === PySpark read operations (SOURCES) ===
        pyspark_read_patterns = [
            (r"spark\.read\.csv\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.read.csv"),
            (r"spark\.read\.parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.read.parquet"),
            (r"spark\.read\.json\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.read.json"),
            (r"spark\.read\.orc\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.read.orc"),
        ]
        
        for pattern, op_type in pyspark_read_patterns:
            for match in re.finditer(pattern, content):
                result["sources"].append({
                    "type": op_type,
                    "path": match.group(1),
                    "line": content[:match.start()].count("\n") + 1,
                    "dynamic": False,
                })
        
        # === PySpark write operations (SINKS) ===
        pyspark_write_patterns = [
            (r"\.write\.csv\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.write.csv"),
            (r"\.write\.parquet\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.write.parquet"),
            (r"\.write\.json\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.write.json"),
            (r"\.write\.jdbc\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.write.jdbc"),
            (r"\.write\.save\s*\(\s*['\"]([^'\"]+)['\"]", "pyspark.write.save"),
        ]
        
        for pattern, op_type in pyspark_write_patterns:
            for match in re.finditer(pattern, content):
                result["sinks"].append({
                    "type": op_type,
                    "path": match.group(1),
                    "line": content[:match.start()].count("\n") + 1,
                    "dynamic": False,
                })
        
        # === Detect f-strings and variable references (DYNAMIC) ===
        # Pattern: read_csv(f"...{var}...") or read_csv(variable_path)
        dynamic_patterns = [
            r"read_\w+\s*\(\s*f['\"]",  # f-string
            r"read_\w+\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)",  # variable (no quotes)
        ]
        
        for pattern in dynamic_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count("\n") + 1
                snippet = content[match.start():match.end()+20]
                result["dynamic_references"].append({
                    "pattern": snippet[:50],
                    "line": line_num,
                    "reason": "dynamic reference, cannot resolve",
                })
                self.dynamic_references.append({
                    "file": str(file_path),
                    "line": line_num,
                    "snippet": snippet[:50],
                })
        
        return result
    
    def get_lineage_edges(self, file_path: Path) -> list[dict]:
        """Convert analyzed data flow to edge format for graph."""
        edges = []
        result = self.analyze_file(file_path)
        
        # Get module name from file path
        module_name = file_path.stem
        
        # Sources -> this module (READS edges)
        for source in result["sources"]:
            edges.append({
                "source": source.get("path", source.get("query", "unknown")),
                "target": module_name,
                "type": "READS",
                "operation": source["type"],
                "line": source.get("line", 0),
                "file": str(file_path),
            })
        
        # This module -> sinks (WRITES edges)
        for sink in result["sinks"]:
            edges.append({
                "source": module_name,
                "target": sink["path"],
                "type": "WRITES",
                "operation": sink["type"],
                "line": sink.get("line", 0),
                "file": str(file_path),
            })
        
        # Log dynamic references as warnings
        for dyn in result["dynamic_references"]:
            edges.append({
                "source": "DYNAMIC_REFERENCE",
                "target": module_name,
                "type": "UNRESOLVED",
                "details": dyn["reason"],
                "line": dyn.get("line", 0),
                "file": str(file_path),
            })
        
        return edges
