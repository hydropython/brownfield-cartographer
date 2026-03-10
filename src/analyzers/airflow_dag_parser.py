"""Airflow DAG Parser  Extract pipeline topology from Airflow DAG files.

Parses:
- DAG definitions (name, schedule, owner)
- Task definitions (operators, sensors)
- Task dependencies (set_upstream, set_downstream, >>, <<)
"""
from pathlib import Path
from typing import Optional, List, Dict
import re


class AirflowDagParser:
    """Extract pipeline topology from Airflow DAG files."""
    
    def __init__(self):
        self.parse_warnings = []
    
    def parse_dag_file(self, file_path: Path) -> dict:
        """Parse an Airflow DAG Python file."""
        result = {
            "dags": [],
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
        
        # Find DAG definitions
        dag_pattern = r"DAG\s*\(\s*['\"]([^'\"]+)['\"]"
        for match in re.finditer(dag_pattern, content):
            result["dags"].append({
                "name": match.group(1),
                "file": str(file_path),
            })
        
        # Find task definitions (common operators)
        task_patterns = [
            r"(\w+)\s*=\s*PythonOperator\s*\(",
            r"(\w+)\s*=\s*BashOperator\s*\(",
            r"(\w+)\s*=\s*SqlOperator\s*\(",
            r"(\w+)\s*=\s*DummyOperator\s*\(",
            r"(\w+)\s*=\s*Sensor\s*\(",
        ]
        
        for pattern in task_patterns:
            for match in re.finditer(pattern, content):
                result["tasks"].append({
                    "name": match.group(1),
                    "file": str(file_path),
                })
        
        # Find task dependencies (>> and <<)
        dep_pattern = r"(\w+)\s*>>\s*(\w+)"
        for match in re.finditer(dep_pattern, content):
            result["dependencies"].append({
                "upstream": match.group(1),
                "downstream": match.group(2),
                "file": str(file_path),
            })
        
        dep_pattern2 = r"(\w+)\s*<<\s*(\w+)"
        for match in re.finditer(dep_pattern2, content):
            result["dependencies"].append({
                "upstream": match.group(2),
                "downstream": match.group(1),
                "file": str(file_path),
            })
        
        return result
    
    def get_lineage_edges(self, file_path: Path) -> list[dict]:
        """Convert parsed DAG to edge format for graph."""
        edges = []
        result = self.parse_dag_file(file_path)
        
        # DAG -> tasks (CONTAINS edges)
        for dag in result["dags"]:
            for task in result["tasks"]:
                edges.append({
                    "source": dag["name"],
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
                "file": str(file_path),
            })
        
        return edges
