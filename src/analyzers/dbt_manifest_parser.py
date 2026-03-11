"""dbt Manifest Parser  Extract explicit model dependencies from dbt manifest.json.

This is the "DNA" of dbt projects  pre-computed by dbt itself.

Confidence: 1.0 (explicit dbt metadata)
"""
from pathlib import Path
from typing import List, Dict, Optional
import json


class DbtManifestParser:
    """Extract lineage from dbt manifest.json."""
    
    def __init__(self):
        self.parse_warnings = []
    
    def get_manifest_edges(self, manifest_path: Path) -> List[dict]:
        """Extract lineage edges from dbt manifest.json."""
        edges = []
        
        if not manifest_path.exists():
            self.parse_warnings.append(f"manifest.json not found: {manifest_path}")
            return edges
        
        try:
            content = manifest_path.read_text(encoding="utf-8")
            manifest = json.loads(content)
        except Exception as e:
            self.parse_warnings.append(f"JSON parse error {manifest_path}: {e}")
            return edges
        
        # Extract model dependencies
        nodes = manifest.get("nodes", {})
        for node_id, node_data in nodes.items():
            if node_data.get("resource_type") != "model":
                continue
            
            model_name = node_data.get("name", "")
            model_file = node_data.get("original_file_path", "")
            
            # Extract dependencies (refs)
            for dep in node_data.get("depends_on", {}).get("nodes", []):
                dep_type = "model"
                if dep.startswith("source."):
                    dep_type = "source"
                elif dep.startswith("seed."):
                    dep_type = "seed"
                
                # Clean up dependency name
                dep_name = dep.split(".")[-1]
                
                edges.append({
                    "source": dep_name,
                    "target": model_name,
                    "type": "MANIFEST_REF",
                    "subtype": dep_type,
                    "file": str(manifest_path),
                    "confidence": 1.0,  # Highest confidence - from dbt itself
                })
        
        # Extract source-to-model mappings
        sources = manifest.get("sources", {})
        for source_id, source_data in sources.items():
            source_name = source_data.get("name", "")
            source_table = source_data.get("identifier", source_name)
            
            edges.append({
                "source": f"{source_name}.{source_table}",
                "target": source_table,
                "type": "SOURCE_DEFINITION",
                "file": str(manifest_path),
                "confidence": 1.0,
            })
        
        # Extract seed-to-model mappings
        seeds = manifest.get("nodes", {})
        for seed_id, seed_data in seeds.items():
            if seed_data.get("resource_type") != "seed":
                continue
            seed_name = seed_data.get("name", "")
            
            edges.append({
                "source": f"seeds/{seed_name}.csv",
                "target": seed_name,
                "type": "SEED_DEFINITION",
                "file": str(manifest_path),
                "confidence": 1.0,
            })
        
        return edges
