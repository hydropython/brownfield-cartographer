"""Prefect Flow Parser  Extract pipeline topology from Prefect flow files."""
from pathlib import Path
from typing import Optional, List, Dict
import re


class PrefectFlowParser:
    """Extract pipeline topology from Prefect flow files."""
    
    def __init__(self):
        self.parse_warnings = []
    
    def parse_flow_file(self, file_path: Path) -> dict:
        """Parse a Prefect flow Python file."""
        result = {
            "flows": [],
            "tasks": [],
            "dependencies": [],
            "file_path": str(file_path),
        }
        
        if not file_path.exists():
            return result
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.parse_warnings.append(f"Read error {file_path}: {e}")
            return result
        
        # Find Flow definitions - @flow decorator
        flow_pattern = r"@flow\s*\([^)]*name\s*=\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(flow_pattern, content):
            result["flows"].append({
                "name": match.group(1),
                "type": "decorator",
                "file": str(file_path),
            })
        
        # Flow class instantiation
        flow_class_pattern = r"Flow\s*\(\s*name\s*=\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(flow_class_pattern, content):
            result["flows"].append({
                "name": match.group(1),
                "type": "class",
                "file": str(file_path),
            })
        
        # Find Task definitions - @task decorator
        task_pattern = r"@task\s*\([^)]*name\s*=\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(task_pattern, content):
            result["tasks"].append({
                "name": match.group(1),
                "type": "decorator",
                "file": str(file_path),
            })
        
        # Task class
        task_class_pattern = r"class\s+(\w+)\s*\(\s*Task\s*\)"
        for match in re.finditer(task_class_pattern, content):
            result["tasks"].append({
                "name": match.group(1),
                "type": "class",
                "file": str(file_path),
            })
        
        # Find task dependencies - set_upstream calls
        upstream_pattern = r"(\w+)\.set_upstream\s*\(\s*(\w+)\s*\)"
        for match in re.finditer(upstream_pattern, content):
            result["dependencies"].append({
                "upstream": match.group(2),
                "downstream": match.group(1),
                "type": "set_upstream",
                "file": str(file_path),
            })
        
        # Task chaining with >> operator
        chain_pattern = r"(\w+)\s*>>\s*(\w+)"
        for match in re.finditer(chain_pattern, content):
            result["dependencies"].append({
                "upstream": match.group(1),
                "downstream": match.group(2),
                "type": "chain",
                "file": str(file_path),
            })
        
        # .submit() calls
        submit_pattern = r"(\w+)\.submit\s*\("
        for match in re.finditer(submit_pattern, content):
            result["dependencies"].append({
                "upstream": match.group(1),
                "downstream": "flow_context",
                "type": "submit",
                "file": str(file_path),
            })
        
        return result
    
    def get_lineage_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed Prefect flow to edge format for graph."""
        edges = []
        result = self.parse_flow_file(file_path)
        
        # Flow -> tasks (CONTAINS edges)
        for flow in result["flows"]:
            for task in result["tasks"]:
                edges.append({
                    "source": flow["name"],
                    "target": task["name"],
                    "type": "CONTAINS",
                    "file": str(file_path),
                })
        
        # Task dependencies (DEPENDS_ON edges)
        for dep in result["dependencies"]:
            edges.append({
                "source": dep["upstream"],
                "target": dep["downstream"],
                "type": "DEPENDS_ON",
                "subtype": dep["type"],
                "file": str(file_path),
            })
        
        return edges
