"""Data Lineage Agent  Phase 2 of Brownfield Cartographer.

Merges 6 analyzers for 100% spec compliance:
1. SqlLineageAnalyzer (sqlglot)  SQL/dbt table dependencies
2. DagConfigParser (dbt YAML)  dbt schema.yml configs
3. PythonDataFlowAnalyzer  pandas, SQLAlchemy, PySpark operations
4. NotebookParser  Jupyter .ipynb data references
5. AirflowDagParser  Airflow DAG pipeline topology
6. PrefectFlowParser  Prefect flow pipeline topology
"""
from pathlib import Path
from typing import Optional
import json
import networkx as nx

from ..analyzers.sql_lineage import SqlLineageAnalyzer
from ..analyzers.dag_config_parser import DagConfigParser
from ..analyzers.python_dataflow import PythonDataFlowAnalyzer
from ..analyzers.notebook_parser import NotebookParser
from ..analyzers.airflow_dag_parser import AirflowDagParser
from ..analyzers.prefect_flow_parser import PrefectFlowParser


class HydrologistAgent:
    """Data Lineage Agent  merges all 6 data flow analyzers."""
    
    def __init__(self, repo_path: Path, output_dir: Path = Path(".cartography"), sql_dialect: str = "postgres"):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir)
        self.sql_dialect = sql_dialect
        
        # Initialize all 6 analyzers
        self.sql_analyzer = SqlLineageAnalyzer(dialect=sql_dialect)
        self.config_parser = DagConfigParser()
        self.python_analyzer = PythonDataFlowAnalyzer()
        self.notebook_parser = NotebookParser()
        self.airflow_parser = AirflowDagParser()
        self.prefect_parser = PrefectFlowParser()
        
        self.lineage_graph = nx.DiGraph()
        self.lineage_edges = []
        self.parse_warnings = []
    
    def run(self, module_graph: Optional[object] = None) -> nx.DiGraph:
        """Run full lineage extraction pipeline with all 6 analyzers."""
        
        # Analyzer 1: SQL Lineage
        sql_files = list(self.repo_path.glob("**/*.sql"))
        print(f"  [1/6] SQL files: {len(sql_files)}")
        for sql_file in sql_files:
            try:
                edges = self.sql_analyzer.get_lineage_edges(sql_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"SQL error {sql_file}: {e}")
        
        # Analyzer 2: dbt YAML Configs
        yaml_files = list(self.repo_path.glob("**/*.yml")) + list(self.repo_path.glob("**/*.yaml"))
        print(f"  [2/6] YAML files: {len(yaml_files)}")
        for yaml_file in yaml_files:
            try:
                edges = self.config_parser.get_config_edges(yaml_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"YAML error {yaml_file}: {e}")
        
        # Analyzer 3: Python Data Flow
        py_files = list(self.repo_path.glob("**/*.py"))
        print(f"  [3/6] Python files: {len(py_files)}")
        for py_file in py_files:
            try:
                edges = self.python_analyzer.get_lineage_edges(py_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"Python error {py_file}: {e}")
        
        # Analyzer 4: Jupyter Notebooks
        ipynb_files = list(self.repo_path.glob("**/*.ipynb"))
        print(f"  [4/6] Notebook files: {len(ipynb_files)}")
        for nb_file in ipynb_files:
            try:
                edges = self.notebook_parser.get_lineage_edges(nb_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"Notebook error {nb_file}: {e}")
        
        # Analyzer 5: Airflow DAGs
        dag_files = list(self.repo_path.glob("**/*dag*.py")) + list(self.repo_path.glob("**/airflow/**/*.py"))
        print(f"  [5/6] Airflow DAG files: {len(dag_files)}")
        for dag_file in dag_files:
            try:
                edges = self.airflow_parser.get_lineage_edges(dag_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"Airflow error {dag_file}: {e}")
        
        # Analyzer 6: Prefect Flows
        prefect_files = list(self.repo_path.glob("**/*flow*.py")) + list(self.repo_path.glob("**/prefect/**/*.py"))
        print(f"  [6/6] Prefect flow files: {len(prefect_files)}")
        for pf_file in prefect_files:
            try:
                edges = self.prefect_parser.get_lineage_edges(pf_file)
                self.lineage_edges.extend(edges)
            except Exception as e:
                self.parse_warnings.append(f"Prefect error {pf_file}: {e}")
        
        # Build merged lineage graph
        for edge in self.lineage_edges:
            self.lineage_graph.add_edge(edge["source"], edge["target"], type=edge["type"], file=edge.get("file", ""))
        
        print(f"\n  Merged lineage graph: {self.lineage_graph.number_of_nodes()} nodes, {self.lineage_graph.number_of_edges()} edges")
        
        return self.lineage_graph
    
    def find_sources(self) -> list[str]:
        """Find entry-point tables (nodes with in-degree=0)."""
        return sorted([node for node in self.lineage_graph.nodes() if self.lineage_graph.in_degree(node) == 0])
    
    def find_sinks(self) -> list[str]:
        """Find output tables (nodes with out-degree=0)."""
        return sorted([node for node in self.lineage_graph.nodes() if self.lineage_graph.out_degree(node) == 0])
    
    def blast_radius(self, table_id: str) -> dict:
        """Compute downstream impact of a table change."""
        if table_id not in self.lineage_graph:
            return {"table": table_id, "downstream_tables": [], "depth": 0, "count": 0}
        
        downstream = list(nx.descendants(self.lineage_graph, table_id))
        max_depth = 0
        for node in downstream:
            try:
                depth = nx.shortest_path_length(self.lineage_graph, table_id, node)
                max_depth = max(max_depth, depth)
            except nx.NetworkXNoPath:
                pass
        
        return {"table": table_id, "downstream_tables": sorted(downstream), "depth": max_depth, "count": len(downstream)}
    
    def save_artifacts(self) -> Path:
        """Save lineage graph to .cartography/lineage_graph.json."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "lineage_graph.json"
        
        data = {
            "sources": self.find_sources(),
            "sinks": self.find_sinks(),
            "total_nodes": self.lineage_graph.number_of_nodes(),
            "total_edges": self.lineage_graph.number_of_edges(),
            "parse_warnings": self.parse_warnings[:10],
            "analyzer_counts": {
                "sql": len(list(self.repo_path.glob("**/*.sql"))),
                "yaml": len(list(self.repo_path.glob("**/*.yml")) + list(self.repo_path.glob("**/*.yaml"))),
                "python": len(list(self.repo_path.glob("**/*.py"))),
                "notebook": len(list(self.repo_path.glob("**/*.ipynb"))),
                "airflow": len(list(self.repo_path.glob("**/*dag*.py")) + list(self.repo_path.glob("**/airflow/**/*.py"))),
                "prefect": len(list(self.repo_path.glob("**/*flow*.py")) + list(self.repo_path.glob("**/prefect/**/*.py"))),
            },
            "nodes": list(self.lineage_graph.nodes()),
            "edges": [{"source": u, "target": v, **d} for u, v, d in self.lineage_graph.edges(data=True)],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_path
