"""
Orchestrator - Wires Surveyor + Hydrologist in sequence
Serializes outputs to .cartography/ directory.
Ensures zero variable shadowing and guaranteed result returns.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .agents.surveyor import SurveyorAgent
from .agents.hydrologist import HydrologistAgent

# Agent 3 & 4: Imports with availability checks
try:
    from .agents.semanticist import SemanticistAgent
    HAS_SEMANTICIST = True
except ImportError:
    HAS_SEMANTICIST = False
    logger.warning("⚠️ SemanticistAgent not available")

try:
    from .agents.archivist import ArchivistAgent
    HAS_ARCHIVIST = True
except ImportError:
    HAS_ARCHIVIST = False
    logger.warning("⚠️ ArchivistAgent not available")


def _log_progress(results: dict, message: str, level: str = "info"):
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": message,
        "level": level
    }
    results["progress_log"].append(entry)
    if level == "error": 
        logger.error(message)
    else: 
        logger.info(message)


def _get_graph_metrics(graph):
    """Safely extracts metrics from various graph object types."""
    nodes = graph.number_of_nodes() if hasattr(graph, "number_of_nodes") else getattr(graph, "total_nodes", 0)
    edges = graph.number_of_edges() if hasattr(graph, "number_of_edges") else getattr(graph, "total_edges", 0)
    return nodes, edges


def run_analysis(repo_path: Path, output_dir: Path, agents: List[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Main execution loop. 
    Guaranteed to return a Dict to prevent 'NoneType' API errors.
    """
    if verbose: 
        logging.getLogger().setLevel(logging.DEBUG)
    
    if agents is None: 
        agents = ["surveyor", "hydrologist", "semanticist", "archivist"]
    
    # 1. SETUP ENVIRONMENT
    output_dir.mkdir(parents=True, exist_ok=True)
    carto_dir = repo_path / ".cartography"
    carto_dir.mkdir(exist_ok=True)
    
    # Initialize results with empty structures to prevent KeyErrors downstream
    results = {
        "repo_path": str(repo_path),
        "agents_run": agents,
        "artifacts": [],
        "errors": [],
        "warnings": [],
        "progress_log": [],
        "surveyor": {"nodes": [], "node_count": 0, "edges": 0},
        "hydrologist": {"nodes": [], "edges": [], "edge_count": 0},
        "semanticist": {"data": {}, "modules_analyzed": 0},
        "archivist": {}
    }

    # ========================
    # PHASE 1: SURVEYOR
    # ========================
    if "surveyor" in agents:
        try:
            _log_progress(results, "[1/4] Running Surveyor Agent...", "info")
            surveyor = SurveyorAgent(repo_path=repo_path)
            graph = surveyor.run()
            
            output_path = carto_dir / "module_graph.json"
            graph.to_file(output_path)
            
            # Extract nodes for the UI and Semanticist
            node_map = getattr(graph, "nodes", {})
            node_list = [v if isinstance(v, dict) else {"id": k} for k, v in node_map.items()]
            
            s_nodes, s_edges = _get_graph_metrics(graph)
            results["surveyor"] = {
                "nodes": node_list, 
                "node_count": s_nodes,
                "edges": s_edges,
                "hubs": getattr(graph, "architectural_hubs", [])
            }
            results["artifacts"].append(str(output_path))
            _log_progress(results, f"✓ Surveyor: {s_nodes} nodes captured", "success")
        except Exception as e:
            _log_progress(results, f"✗ Surveyor failed: {e}", "error")
            results["errors"].append({"agent": "surveyor", "error": str(e)})

    # ========================
    # PHASE 2: HYDROLOGIST
    # ========================
    if "hydrologist" in agents:
        try:
            _log_progress(results, "[2/4] Running Hydrologist Agent...", "info")
            hydrologist = HydrologistAgent(repo_path=repo_path)
            
            # EXECUTION: Returns the dict we cleaned up in hydrologist.py
            h_data = hydrologist.run() 
            results["hydrologist"] = h_data
            
            # PERSISTENCE: Save to .cartography
            output_path = carto_dir / "lineage_graph.json"
            with open(output_path, "w", encoding="utf-8") as f_out:
                json.dump(h_data, f_out, indent=2, default=str)
            
            results["artifacts"].append(str(output_path))
            _log_progress(results, f"✓ Hydrologist: {h_data.get('edge_count', 0)} edges detected", "success")
        except Exception as e:
            _log_progress(results, f"✗ Hydrologist failed: {e}", "error")
            results["errors"].append({"agent": "hydrologist", "error": str(e)})

    # ========================
    # PHASE 3: SEMANTICIST
    # ========================
    if "semanticist" in agents and HAS_SEMANTICIST:
        try:
            _log_progress(results, "[3/4] Running Semanticist Agent...", "info")
            semanticist = SemanticistAgent(repo_path=repo_path)
            
            # HANDSHAKE: Pass the dictionaries we just built
            sem_results = semanticist.run(results["surveyor"], results["hydrologist"])
            
            # Clean data extraction
            inner_data = sem_results.get("data", sem_results) if isinstance(sem_results, dict) else {}

            results["semanticist"] = {
                "data": inner_data,
                "modules_analyzed": len(inner_data.get("purpose_statements", {}))
            }
            _log_progress(results, f"✓ Semanticist analysis complete", "success")
        except Exception as e:
            _log_progress(results, f"✗ Semanticist failed: {e}", "error")

    # ========================
    # PHASE 4: ARCHIVIST
    # ========================
    if "archivist" in agents and HAS_ARCHIVIST:
        try:
            _log_progress(results, "[4/4] Running Archivist Agent...", "info")
            archivist = ArchivistAgent(repo_path=Path(repo_path))
            
            # FINAL HANDSHAKE: Pass all captured data
            archivist_results = archivist.run(
                surveyor_data=results["surveyor"],
                hydrologist_data=results["hydrologist"],
                semantic_data=results["semanticist"].get("data", {})
            )
            results["archivist"] = archivist_results
            _log_progress(results, "✓ Archivist: Generated living documentation", "success")
        except Exception as e:
            _log_progress(results, f"✗ Archivist failed: {e}", "error")

    # =================================================================
    # THE GUARANTEE: Always return the results object
    # =================================================================
    return results