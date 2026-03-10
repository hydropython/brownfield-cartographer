"""DAG Config Parser  dbt YAML config parsing for pipeline topology.

Extracts:
- Model definitions from schema.yml
- Source definitions from sources.yml
- Test configurations
- Column-level lineage
"""
from pathlib import Path
from typing import Optional
import yaml


class DagConfigParser:
    """Parse dbt/Airflow YAML configs for pipeline topology."""
    
    def __init__(self):
        pass
    
    def parse_dbt_schema(self, file_path: Path) -> dict:
        """Parse a dbt schema.yml file."""
        result = {
            "models": [],
            "sources": [],
            "tests": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception:
            return result
        
        if not data:
            return result
        
        # Extract models
        for model in data.get("models", []):
            if isinstance(model, dict):
                model_info = {
                    "name": model.get("name", ""),
                    "description": model.get("description", ""),
                    "columns": [col.get("name") for col in model.get("columns", []) if isinstance(col, dict)],
                    "tests": [],
                }
                
                # Extract tests from columns
                for col in model.get("columns", []):
                    if isinstance(col, dict):
                        tests = col.get("tests", [])
                        if tests:
                            model_info["tests"].extend(tests)
                
                result["models"].append(model_info)
        
        # Extract sources
        for source in data.get("sources", []):
            if isinstance(source, dict):
                source_info = {
                    "name": source.get("name", ""),
                    "schema": source.get("schema", ""),
                    "tables": [tbl.get("name") for tbl in source.get("tables", []) if isinstance(tbl, dict)],
                }
                result["sources"].append(source_info)
        
        return result
    
    def get_config_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed config to edge format for graph."""
        edges = []
        parsed = self.parse_dbt_schema(file_path)
        
        # Model -> columns (HAS_COLUMN edges)
        for model in parsed["models"]:
            for col in model["columns"]:
                edges.append({
                    "source": model["name"],
                    "target": f"{model['name']}.{col}",
                    "type": "HAS_COLUMN",
                    "file": str(file_path),
                })
            
            # Model -> tests (HAS_TEST edges)
            for test in model["tests"]:
                edges.append({
                    "source": model["name"],
                    "target": f"{model['name']}_test_{test}",
                    "type": "HAS_TEST",
                    "file": str(file_path),
                })
        
        # Source -> tables (CONTAINS edges)
        for source in parsed["sources"]:
            for table in source["tables"]:
                edges.append({
                    "source": source["name"],
                    "target": f"{source['name']}.{table}",
                    "type": "CONTAINS",
                    "file": str(file_path),
                })
        
        return edges
