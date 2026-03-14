"""
Semanticist Agent - Upgraded Forensic Purpose Analyst
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

class SemanticistAgent:
    def __init__(self, repo_path: Path, api_key: Optional[str] = None, budget_limit: float = 5.00, max_modules: int = 50):
        self.repo_path = Path(repo_path)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.max_modules = max_modules
        self.results = {
            "purpose_statements": {},
            "fde_answers": {},
            "domain_clusters": {},
            "budget": {"limit": budget_limit, "spent": 0.0}
        }

    def _read_module_code(self, module_id: str) -> tuple[str, str]:
        path_parts = module_id.split('.')
        potential_path = self.repo_path / "/".join(path_parts)
        for ext in ['.sql', '.yml', '.py']:
            full_path = potential_path.with_suffix(ext)
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read(), str(full_path)
        return "# Code not found", "unknown"

    def _read_docstring(self, code: str) -> str:
        lines = code.splitlines()
        doc = []
        for line in lines:
            if line.strip().startswith(('--', '#', '/*')):
                doc.append(line.strip().lstrip('-#/* '))
            elif not line.strip(): continue
            else: break
        return " ".join(doc) if doc else "No documentation found."

    def generate_purpose_statement(self, module_id: str, code: str, docstring: str) -> str:
        if "stg_" in module_id:
            return f"Staging model for {module_id.split('_')[-1]}. Cleanses raw source data."
        if "marts" in module_id:
            return f"Business logic for {module_id.split('.')[-1]}. Provides analytics-ready data."
        return f"Core logic for {module_id}. Analyzes system dependencies."

    def cluster_into_domains(self, nodes_data: list) -> Dict[str, list]:
        clusters = {"Staging": [], "Marts": [], "Macros": [], "Core/Other": []}
        for node in nodes_data:
            m_id = node.get("id") if isinstance(node, dict) else str(node)
            if "staging" in m_id.lower(): clusters["Staging"].append(m_id)
            elif "marts" in m_id.lower(): clusters["Marts"].append(m_id)
            elif "macros" in m_id.lower(): clusters["Macros"].append(m_id)
            else: clusters["Core/Other"].append(m_id)
        return clusters

    def answer_day_one_questions(self, nodes_data: list, hydrologist_results: Dict) -> Dict[str, str]:
        nodes_list = nodes_data if isinstance(nodes_data, list) else []
        stg_nodes = [n for n in nodes_list if "stg_" in str(n)]
        mart_nodes = [n for n in nodes_list if "marts" in str(n)]
        
        return {
            "q1_ingestion_path": f"Via {len(stg_nodes)} staging models",
            "q2_critical_outputs": ", ".join([str(n).split('.')[-1] for n in mart_nodes[:3]]) or "None detected",
            "q3_blast_radius": f"High impact on {len(mart_nodes)} downstream models",
            "q4_logic_distribution": "Concentrated in 'marts/' directory" if mart_nodes else "Distributed",
            "q5_git_velocity": "Analysis pending"
        }

    def run(self, surveyor_results: Dict, hydrologist_results: Dict) -> Dict[str, Any]:
        logger.info("Semanticist Swarm Initiated...")
        
        # 1. Defensive Data Loading
        nodes_data = []
        if isinstance(surveyor_results, dict):
            # Try to get the list of nodes
            nodes_data = surveyor_results.get("nodes", [])
            
        # 2. If nodes_data is still empty or an integer, load from the saved file
        if not isinstance(nodes_data, list) or not nodes_data:
            graph_path = self.repo_path / ".cartography" / "module_graph.json"
            if graph_path.exists():
                with open(graph_path, 'r', encoding='utf-8') as f:
                    full_graph = json.load(f)
                    nodes_data = full_graph.get("nodes", [])
        
        # 3. Proceed with analysis only if we have a list
        self.results["purpose_statements"] = {}
        if isinstance(nodes_data, list):
            for node in nodes_data:
                # Handle cases where node is a dict or just a string
                m_id = node.get("id") if isinstance(node, dict) else str(node)
                code, path = self._read_module_code(m_id)
                self.results["purpose_statements"][m_id] = self.generate_purpose_statement(
                    m_id, code, self._read_docstring(code)
                )

        # 4. Standard features
        self.results["domain_clusters"] = self.cluster_into_domains(nodes_data)
        self.results["fde_answers"] = self.answer_day_one_questions(nodes_data, hydrologist_results)

        self._persist_to_refined_state()
        return {"ok": True, "data": self.results}

    def _persist_to_refined_state(self):
        target_dir = Path(r"D:\10 ACADAMY KIFIYA\TRP_Training\week 4\refined_audit")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        ui_payload = {
            "ok": True,
            "results": self.results
        }
        
        state_file = target_dir / "ui_semantic_state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(ui_payload, f, indent=2)
        print(f"✅ DATA CAPTURED: {len(self.results['purpose_statements'])} modules saved to {state_file}")