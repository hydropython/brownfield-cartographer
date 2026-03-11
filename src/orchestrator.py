"""
Orchestrator - Wires Surveyor + Hydrologist in sequence

Serializes outputs to .cartography/ directory.
Includes robust error handling and logging.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .agents.surveyor import SurveyorAgent
from .agents.hydrologist import HydrologistAgent


def run_analysis(
    repo_path: Path,
    output_dir: Path,
    agents: List[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run analysis pipeline on repository with error isolation.
    
    Args:
        repo_path: Path to repository
        output_dir: Output directory for artifacts
        agents: List of agents to run
        verbose: Enable verbose output
    
    Returns:
        Dictionary with analysis results
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if agents is None:
        agents = ["surveyor", "hydrologist"]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "repo_path": str(repo_path),
        "agents_run": agents,
        "artifacts": [],
        "errors": [],
        "warnings": []
    }
    
    # Run Surveyor Agent with error isolation
    if "surveyor" in agents:
        try:
            logger.info("[1/2] Running Surveyor Agent...")
            logger.info(f"  Repository: {repo_path}")
            
            surveyor = SurveyorAgent(repo_path=repo_path)
            graph = surveyor.run()
            
            # Save module graph
            output_path = output_dir / "module_graph.json"
            graph.to_file(output_path)
            results["artifacts"].append(str(output_path))
            results["surveyor"] = {
                "nodes": graph.total_nodes,
                "edges": graph.total_edges,
                "hubs": graph.architectural_hubs,
                "warnings": getattr(graph, "parse_warnings", [])
            }
            
            logger.info(f"   Module Graph: {graph.total_nodes} nodes, {graph.total_edges} edges")
            logger.info(f"   Saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Surveyor Agent failed: {e}")
            results["errors"].append({"agent": "surveyor", "error": str(e)})
            results["warnings"].append(f"Surveyor analysis incomplete: {e}")
    
    # Run Hydrologist Agent with error isolation
    if "hydrologist" in agents:
        try:
            logger.info("[2/2] Running Hydrologist Agent...")
            
            hydrologist = HydrologistAgent(repo_path=repo_path)
            graph = hydrologist.run()
            
            # Save lineage graph
            output_path = output_dir / "lineage_graph.json"
            
            import json
            with open(output_path, "w") as f:
                json.dump({
                    "nodes": graph.total_nodes,
                    "edges": len(getattr(hydrologist, "lineage_edges", [])),
                    "edges_detail": getattr(hydrologist, "lineage_edges", [])
                }, f, indent=2)
            
            results["artifacts"].append(str(output_path))
            results["hydrologist"] = {
                "nodes": graph.total_nodes,
                "edges": len(getattr(hydrologist, "lineage_edges", [])),
                "warnings": []
            }
            
            logger.info(f"   Lineage Graph: {graph.total_nodes} nodes, {len(getattr(hydrologist, 'lineage_edges', []))} edges")
            logger.info(f"   Saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Hydrologist Agent failed: {e}")
            results["errors"].append({"agent": "hydrologist", "error": str(e)})
            results["warnings"].append(f"Hydrologist analysis incomplete: {e}")
    
    # Log summary
    logger.info()
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Agents run: {len(agents)}")
    logger.info(f"Artifacts generated: {len(results['artifacts'])}")
    logger.info(f"Errors: {len(results['errors'])}")
    logger.info(f"Warnings: {len(results['warnings'])}")
    
    return results
