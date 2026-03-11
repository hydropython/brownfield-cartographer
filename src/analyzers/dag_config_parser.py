"""
DAG Config Parser - YAML AST-based config extraction

Parses YAML configuration files using proper AST parsing.
Extracts models, tests, sources, exposures from dbt/YAML configs.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DAGConfigParser:
    """
    Parse YAML configuration files using AST.
    
    Extracts:
    - Model definitions and configurations
    - Test definitions
    - Source definitions
    - Exposure definitions
    """
    
    def __init__(self):
        self.yaml_available = self._init_yaml()
    
    def _init_yaml(self) -> bool:
        """Initialize YAML parser if available."""
        try:
            import yaml
            logger.info("   PyYAML loaded for AST parsing")
            return True
        except ImportError:
            logger.warning("   PyYAML not installed")
            return False
    
    def parse_dbt_schema(self, yaml_file: Path) -> Dict[str, Any]:
        """
        Parse dbt schema.yml file using YAML AST.
        
        Args:
            yaml_file: Path to schema.yml file
        
        Returns:
            Dictionary with models, tests, sources extracted
        """
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
            
            elements = {
                "models": [],
                "tests": [],
                "sources": [],
                "exposures": []
            }
            
            if content:
                # Extract models with columns and tests (AST-based)
                for model in content.get("models", []):
                    if isinstance(model, dict):
                        model_name = list(model.keys())[0] if model else None
                        if model_name:
                            model_config = model.get(model_name, {})
                            columns = model_config.get("columns", [])
                            
                            # Extract tests from columns
                            model_tests = []
                            for col in columns:
                                if isinstance(col, dict):
                                    col_tests = col.get("tests", [])
                                    model_tests.extend([
                                        {"column": col.get("name"), "test": t}
                                        for t in (col_tests if isinstance(col_tests, list) else [])
                                    ])
                            
                            elements["models"].append({
                                "name": model_name,
                                "description": model_config.get("description", ""),
                                "columns": [c.get("name") if isinstance(c, dict) else str(c) for c in columns],
                                "tests": model_tests
                            })
                
                # Extract sources (AST-based)
                for source in content.get("sources", []):
                    if isinstance(source, dict):
                        elements["sources"].append({
                            "name": source.get("name"),
                            "tables": [t.get("name") for t in source.get("tables", [])]
                        })
                
                # Extract exposures (AST-based)
                for exposure in content.get("exposures", []):
                    if isinstance(exposure, dict):
                        elements["exposures"].append({
                            "name": exposure.get("name"),
                            "type": exposure.get("type"),
                            "owner": exposure.get("owner", {}).get("email", "")
                        })
            
            logger.info(f"  Parsed {yaml_file.name}: {len(elements['models'])} models, {len(elements['sources'])} sources via YAML AST")
            
            return {
                "file": str(yaml_file),
                "type": "dbt_schema",
                "elements": elements,
                "parse_method": "yaml-ast"
            }
        
        except Exception as e:
            logger.warning(f"Failed to parse {yaml_file}: {e}")
            return {
                "file": str(yaml_file),
                "type": "dbt_schema",
                "error": str(e),
                "elements": {},
                "recoverable": True
            }
    
    def parse_dbt_project(self, yaml_file: Path) -> Dict[str, Any]:
        """Parse dbt_project.yml file using YAML AST."""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
            
            return {
                "file": str(yaml_file),
                "type": "dbt_project",
                "name": content.get("name", "unknown") if content else "unknown",
                "version": content.get("version", "1.0.0") if content else "1.0.0",
                "profile": content.get("profile", "") if content else "",
                "parse_method": "yaml-ast"
            }
        except Exception as e:
            logger.warning(f"Failed to parse {yaml_file}: {e}")
            return {
                "file": str(yaml_file),
                "type": "dbt_project",
                "error": str(e),
                "parse_method": "failed"
            }
    
    def analyze_directory(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Analyze all YAML files in directory with progress reporting."""
        from tqdm import tqdm
        
        yaml_files = list(repo_path.rglob("*.yml")) + list(repo_path.rglob("*.yaml"))
        results = []
        
        logger.info(f"Analyzing {len(yaml_files)} YAML files...")
        
        for yaml_file in tqdm(yaml_files, desc="YAML files"):
            if "node_modules" not in str(yaml_file) and ".git" not in str(yaml_file):
                filename = yaml_file.name.lower()
                
                if filename == "dbt_project.yml":
                    result = self.parse_dbt_project(yaml_file)
                elif "schema" in filename:
                    result = self.parse_dbt_schema(yaml_file)
                else:
                    result = {"file": str(yaml_file), "type": "unknown", "parse_method": "skipped"}
                
                results.append(result)
        
        return results
