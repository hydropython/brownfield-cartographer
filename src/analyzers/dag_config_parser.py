"""DAG Config Parser  Extract dbt YAML configurations as graph edges.

Confidence Scoring:
- 1.0: Explicit YAML relationships (schema.yml foreign keys)
- 1.0: Source definitions (schema.yml sources)
- 1.0: Test definitions (schema.yml tests)
"""
from pathlib import Path
from typing import Optional, List, Dict

try:
    import yaml
except ImportError:
    yaml = None


class DagConfigParser:
    """Extract pipeline topology from dbt YAML config files."""
    
    def __init__(self):
        self.parse_warnings = []
    
    def parse_yaml_file(self, file_path: Path) -> dict:
        """Parse a dbt YAML config file."""
        result = {
            "models": [],
            "sources": [],
            "tests": [],
            "relationships": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        if yaml is None:
            self.parse_warnings.append(f"PyYAML not installed, skipping {file_path}")
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as e:
            self.parse_warnings.append(f"YAML parse error {file_path}: {e}")
            return result
        
        if not data:
            return result
        
        # schema.yml has: models as LIST of dicts with 'name' key
        models = data.get("models", [])
        if isinstance(models, list) and len(models) > 0:
            if isinstance(models[0], dict) and "name" in models[0]:
                self._parse_schema_yml(data, result, file_path)
        
        return result
    
    def _parse_schema_yml(self, data: dict, result: dict, file_path: Path) -> None:
        """Parse schema.yml file (model definitions with columns/tests)."""
        # Extract models
        for model in data.get("models", []):
            if not isinstance(model, dict):
                continue
            model_name = model.get("name", "")
            if not model_name:
                continue
            
            result["models"].append({
                "name": model_name,
                "file": str(file_path),
                "columns": [],
                "tests": [],
            })
            
            for col in model.get("columns", []):
                if not isinstance(col, dict):
                    continue
                col_name = col.get("name", "")
                if col_name:
                    result["models"][-1]["columns"].append(col_name)
                
                for test in col.get("tests", []):
                    if isinstance(test, str):
                        result["models"][-1]["tests"].append({"type": test, "column": col_name})
                    elif isinstance(test, dict):
                        test_name = list(test.keys())[0]
                        result["models"][-1]["tests"].append({
                            "type": test_name,
                            "column": col_name,
                            "config": test[test_name]
                        })
                        
                        if test_name == "relationships":
                            rel_config = test["relationships"]
                            to_ref = str(rel_config.get("to", ""))
                            to_model = to_ref.replace("ref('", "").replace('ref("', "").replace("')", "").replace('")', "")
                            result["relationships"].append({
                                "from_model": model_name,
                                "from_column": col_name,
                                "to_model": to_model,
                                "to_column": str(rel_config.get("field", "")),
                                "file": str(file_path),
                            })
        
        # Extract sources
        for source in data.get("sources", []):
            if not isinstance(source, dict):
                continue
            source_name = source.get("name", "")
            for table in source.get("tables", []):
                if isinstance(table, dict):
                    table_name = table.get("name", "")
                    if table_name:
                        result["sources"].append({
                            "source_name": source_name,
                            "table_name": table_name,
                            "file": str(file_path),
                            "columns": [c.get("name") for c in table.get("columns", []) if isinstance(c, dict)],
                        })
    
    def get_config_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed YAML config to edge format."""
        edges = []
        result = self.parse_yaml_file(file_path)
        
        # Relationship edges (foreign keys) - HIGH CONFIDENCE (1.0)
        for rel in result["relationships"]:
            edges.append({
                "source": rel["to_model"],
                "target": rel["from_model"],
                "type": "RELATIONSHIP",
                "subtype": "foreign_key",
                "from_column": rel["from_column"],
                "to_column": rel["to_column"],
                "file": rel["file"],
                "confidence": 1.0,
            })
        
        # Source edges - HIGH CONFIDENCE (1.0)
        for src in result["sources"]:
            edges.append({
                "source": f"{src['source_name']}.{src['table_name']}",
                "target": src["table_name"],
                "type": "SOURCES",
                "file": src["file"],
                "confidence": 1.0,
            })
        
        # Test edges - HIGH CONFIDENCE (1.0)
        for model in result["models"]:
            for test in model.get("tests", []):
                edges.append({
                    "source": model["name"],
                    "target": f"{model['name']}_test_{test['type']}_{test['column']}",
                    "type": "TESTS",
                    "subtype": test["type"],
                    "column": test["column"],
                    "file": model["file"],
                    "confidence": 1.0,
                })
        
        return edges
