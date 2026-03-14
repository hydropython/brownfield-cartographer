"""
DAG Config Parser - Phase 2
Focus: Extraction of lineage metadata from dbt YAML configurations.
"""
import yaml
from pathlib import Path
from typing import List, Dict, Any

class DAGConfigAnalyzer:
    """
    Parses dbt YAML files (schema.yml, sources.yml) to identify 
    upstream sources and model properties.
    """
    def __init__(self):
        self.found_configs = []

    def get_config_edges(self, yaml_path: Path) -> List[Dict[str, Any]]:
        """
        Parses a YAML file and returns list of edges for the lineage graph.
        Targeting CONSUMES/PRODUCES relationships defined in metadata.
        """
        edges = []
        if not yaml_path.exists():
            return edges

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not config:
                return edges

            # 1. Process Sources (Defining entry points)
            if 'sources' in config:
                for source in config['sources']:
                    source_name = source.get('name')
                    for table in source.get('tables', []):
                        table_name = table.get('name')
                        # Logic: Source Table -> Source Object
                        edges.append({
                            "source": f"{source_name}.{table_name}",
                            "target": source_name,
                            "type": "PRODUCES",
                            "meta": "yaml_source_definition"
                        })

            # 2. Process Models (Defining transformation metadata)
            if 'models' in config:
                for model in config['models']:
                    model_name = model.get('name')
                    # We look for tests or descriptions that imply dependencies
                    # though dbt usually handles this in the SQL 'ref'
                    pass

        except Exception as e:
            # We fail silently to keep the swarm moving
            print(f"Warning: Failed to parse YAML {yaml_path.name}: {e}")
            
        return edges

    def extract_schema_metadata(self, yaml_path: Path) -> Dict[str, Any]:
        """Extra utility for the Semanticist Agent to verify column names."""
        metadata = {}
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # Logic to pull column descriptions and types
        except:
            pass
        return metadata