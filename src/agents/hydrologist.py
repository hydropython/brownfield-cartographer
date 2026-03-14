import re             # Fixes the red line in your screenshot
import json as j_lib  # Prevents the "UnboundLocalError"
import logging
import networkx as nx
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class HydrologistAgent:
    def __init__(self, repo_path: Path, dag=None):
        self.repo_path = Path(repo_path).resolve()
        # Use existing DAG if passed (from Surveyor), otherwise create new
        self.dag = dag if dag is not None else nx.DiGraph()
        self.COLOR_MAP = {"Dataset": "#2ecc71", "Logic": "#e67e22", "File": "#3498db"}

    def _add_lineage(self, source, target, t_type, file, lines="0"):
        """Standardized edge creation with full metadata."""
        if not source or not target:
            return
            
        # Ensure nodes exist with correct metadata before adding the edge
        if source not in self.dag:
            self.dag.add_node(source, type="DatasetNode", color=self.COLOR_MAP["Dataset"])
        if target not in self.dag:
            self.dag.add_node(target, type="DatasetNode", color=self.COLOR_MAP["Dataset"])
            
        self.dag.add_edge(
            source, target,
            transformation_type=t_type,
            source_file=str(file.relative_to(self.repo_path)) if hasattr(file, 'relative_to') else str(file),
            line_range=str(lines)
        )

    def _parse_notebook(self, file_path: Path):
        """Pattern: Jupyter .ipynb files parsed for data sources and sinks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # This uses the top-level json import, fixing your previous error
                nb = j_lib.load(f) 
                for i, cell in enumerate(nb.get('cells', [])):
                    if cell['cell_type'] == 'code':
                        code_content = "".join(cell['source'])
                        # Detect read/load
                        for match in re.findall(r"(?:read_|load)\(['\"](.*?)['\"]", code_content):
                            self._add_lineage(match, file_path.name, "NB_READ", file_path, i)
                        # Detect to/save
                        for match in re.findall(r"(?:to_|save)\(['\"](.*?)['\"]", code_content):
                            self._add_lineage(file_path.name, match, "NB_WRITE", file_path, i)
        except Exception as e:
            logger.debug(f"Notebook parse skipped for {file_path.name}: {e}")

    def _parse_orchestration(self, file_path: Path):
        """Pattern: Airflow/Prefect DAGs and dbt schema.yml."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Airflow task dependencies (>> or <<)
            for match in re.findall(r"(\w+)\s*>>\s*(\w+)", content):
                self._add_lineage(match[0], match[1], "AIRFLOW_DAG", file_path)
            
            # dbt source/ref patterns
            for match in re.findall(r"ref\(['\"](\w+)['\"]\)", content):
                self._add_lineage(match, file_path.stem.upper(), "DBT_REF", file_path)
        except Exception as e:
            logger.debug(f"Orchestration parse failed for {file_path.name}: {e}")

    def run(self) -> dict:
        """Full Spectrum Analysis: 100% Node Retention Policy."""
        import re
        try:
            logger.info("Hydrologist: Analyzing lineage and data flow...")
            
            # Reset local graph state (using self.dag as per your previous logic)
            self.dag = nx.DiGraph()

            # 1. INITIALIZE ALL NODES (Capture the 33 files)
            found_files = list(self.repo_path.glob("**/*"))
            for f in found_files:
                if f.is_file() and f.suffix in ['.sql', '.py', '.ipynb', '.yml']:
                    # Normalize node_id to UPPER for case-insensitive matching in lineage
                    node_id = f.stem.upper()
                    self.dag.add_node(
                        node_id, 
                        type="FileNode", 
                        color="#2ecc71" if f.suffix == '.sql' else "#95a5a6",
                        source_file=str(f.relative_to(self.repo_path)),
                        label=f.stem
                    )

            # 2. LAYER TRANSFORMATIONS (SQL/dbt Lineage Logic)
            # This fills the "0 edges" gap by scanning for table relationships
            sql_files = list(self.repo_path.glob("**/*.sql"))
            for sql_file in sql_files:
                target_node = sql_file.stem.upper()
                
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Pattern A: dbt ref() calls - e.g., {{ ref('stg_orders') }}
                dbt_refs = re.findall(r"ref\(['\"]([^'\"]+)['\"]\)", content)
                
                # Pattern B: Standard SQL JOINs/FROMs (Simple fallback)
                # Looks for "FROM table" or "JOIN table"
                sql_refs = re.findall(r"(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)", content, re.IGNORECASE)
                
                # Combine and deduplicate potential sources
                potential_sources = set([r.upper() for r in dbt_refs + sql_refs])
                
                for source_node in potential_sources:
                    # Only add an edge if the source exists in our captured nodes
                    if source_node in self.dag.nodes and source_node != target_node:
                        self.dag.add_edge(
                            source_node, 
                            target_node, 
                            transformation_type="LINEAGE",
                            color="#3498db",
                            weight=1.0
                        )
                        logger.debug(f"Edge Created: {source_node} -> {target_node}")

            # 3. CONSTRUCT UI-READY DICTIONARY
            return {
                "status": "success",
                "nodes": [{"id": n, **d} for n, d in self.dag.nodes(data=True)],
                "edges": [{"source": u, "target": v, **d} for u, v, d in self.dag.edges(data=True)],
                "edge_count": self.dag.number_of_edges(),
                "node_count": self.dag.number_of_nodes()
            }

        except Exception as e:
            logger.error(f"✗ Hydrologist failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed", 
                "error": str(e), 
                "nodes": [], 
                "edges": [], 
                "edge_count": 0
            }

    def _add_lineage(self, source, target, t_type, file, lines="0"):
        """Ensures that adding an edge also updates node status to 'Active'."""
        # Update node colors to show they have active lineage
        for node in [source, target]:
            if node not in self.dag:
                self.dag.add_node(node, type="DatasetNode", color="#2ecc71")
            else:
                # If it was a gray file node, promote it to a green dataset node
                self.dag.nodes[node]['color'] = "#2ecc71"
                self.dag.nodes[node]['type'] = "DatasetNode"

        self.dag.add_edge(
            source, target,
            transformation_type=t_type,
            source_file=str(file.relative_to(self.repo_path)),
            line_range=str(lines)
        )

    # --- FORENSIC QUERY METHODS ---
    def get_upstream(self, table):
        """'Show me all upstream dependencies of table X'"""
        return list(nx.ancestors(self.dag, table)) if table in self.dag else []

    def get_impact(self, table):
        """'What would break if I change the schema of table Y?'"""
        return list(nx.descendants(self.dag, table)) if table in self.dag else []

    def save_artifacts(self) -> Path:
        """Saves lineage data to refined_ folders using aliased library."""
        # Ensure we are using j_lib, and NO local variable is named 'json'
        
        # 1. Capture the graph state
        # Rename 'n' and 'd' to be more descriptive to avoid any single-letter conflicts
        graph_nodes = [
            {"data": {"id": node_id, "label": node_id, **node_data}} 
            for node_id, node_data in self.dag.nodes(data=True)
        ]
        graph_edges = [
            {"data": {"source": u_node, "target": v_node, **edge_data}} 
            for u_node, v_node, edge_data in self.dag.edges(data=True)
        ]

        payload = {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "metadata": {
                "legend": getattr(self, 'COLOR_MAP', {}), 
                "timestamp": datetime.now().isoformat()
            }
        }

        target_folders = ["refined_audit", "refined_"]
        last_saved_path = None

        for folder_name in target_folders:
            try:
                save_path = Path(folder_name)
                save_path.mkdir(exist_ok=True)
                
                output_file = save_path / "lineage_graph.json"
                with open(output_file, "w", encoding="utf-8") as f_out:
                    # STRICTLY use j_lib here
                    j_lib.dump(payload, f_out, indent=2, default=str)
                
                last_saved_path = output_file
                logger.info(f"✅ Hydrologist: Saved artifacts to {output_file}")
            except Exception as e:
                logger.error(f"❌ Failed to save to {folder_name}: {e}")

        return last_saved_path