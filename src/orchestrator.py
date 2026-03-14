"""
Orchestrator - Wires Surveyor + Hydrologist in sequence

Serializes outputs to .cartography/ directory.
Includes robust error handling and logging with progress tracking.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent imports
from .agents.surveyor import SurveyorAgent
from .agents.hydrologist import HydrologistAgent

# Agent 3: Semanticist (optional - requires LLM module)
try:
    from .agents.semanticist import SemanticistAgent
    HAS_SEMANTICIST = True
except ImportError:
    SemanticistAgent = None
    HAS_SEMANTICIST = False
    print("⚠️  SemanticistAgent not available (LLM module missing)")

# Agent 4: Archivist (optional)
try:
    from .agents.archivist import ArchivistAgent
    HAS_ARCHIVIST = True
except ImportError:
    ArchivistAgent = None
    HAS_ARCHIVIST = False
    print("⚠️  ArchivistAgent not available")
    
def _log_progress(results: dict, message: str, level: str = "info"):
    """Add progress entry to results for frontend display"""
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
    """
    Safely extract node/edge counts from any graph type.
    Handles both raw NetworkX DiGraph and CartographyGraph wrapper.
    """
    nodes = graph.number_of_nodes() if hasattr(graph, "number_of_nodes") else getattr(graph, "total_nodes", 0)
    edges = graph.number_of_edges() if hasattr(graph, "number_of_edges") else getattr(graph, "total_edges", 0)
    return nodes, edges


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
        Dictionary with analysis results and progress log
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if agents is None:
        agents = ["surveyor", "hydrologist", "semanticist", "archivist"]
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "repo_path": str(repo_path),
        "agents_run": agents,
        "artifacts": [],
        "errors": [],
        "warnings": [],
        "progress_log": []
    }
    
    # ========================
    # Run Surveyor Agent
    # ========================
    if "surveyor" in agents:
        try:
            logger.info("[1/4] Running Surveyor Agent...")
            _log_progress(results, "Agent 1 (Surveyor): Starting module analysis", "info")
            logger.info(f"  Repository: {repo_path}")
            
            surveyor = SurveyorAgent(repo_path=repo_path)
            graph = surveyor.run()
            
            # Save module graph
            output_path = output_dir / "module_graph.json"
            graph.to_file(output_path)
            results["artifacts"].append(str(output_path))
            
            # Extract metrics safely
            s_nodes, s_edges = _get_graph_metrics(graph)
            
            results["surveyor"] = {
                "nodes": s_nodes,
                "edges": s_edges,
                "hubs": getattr(graph, "architectural_hubs", []),
                "warnings": getattr(graph, "parse_warnings", [])
            }
            
            logger.info(f"   Module Graph: {s_nodes} nodes, {s_edges} edges")
            _log_progress(results, f"✓ Surveyor: {s_nodes} nodes, {s_edges} edges", "success")
            logger.info(f"   Saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Surveyor Agent failed: {e}")
            _log_progress(results, f"✗ Surveyor failed: {e}", "error")
            results["errors"].append({"agent": "surveyor", "error": str(e)})
            results["warnings"].append(f"Surveyor analysis incomplete: {e}")
    
    # ========================
    # Run Hydrologist Agent
    # ========================
    if "hydrologist" in agents:
        try:
            logger.info("[2/4] Running Hydrologist Agent...")
            _log_progress(results, "Agent 2 (Hydrologist): Starting lineage extraction", "info")
            
            hydrologist = HydrologistAgent(repo_path=repo_path)
            graph = hydrologist.run()
            
            # Extract metrics safely (Hydrologist returns raw DiGraph)
            h_nodes, h_edges = _get_graph_metrics(graph)
            lineage_edges = getattr(hydrologist, "lineage_edges", [])
            
            # Save lineage graph
            output_path = output_dir / "lineage_graph.json"
            
            import json
            with open(output_path, "w") as f:
                json.dump({
                    "nodes": h_nodes,
                    "edges": len(lineage_edges),
                    "edges_detail": lineage_edges
                }, f, indent=2)
            
            results["artifacts"].append(str(output_path))
            results["hydrologist"] = {
                "nodes": h_nodes,
                "edges": len(lineage_edges),
                "warnings": []
            }
            
            logger.info(f"   Lineage Graph: {h_nodes} nodes, {len(lineage_edges)} edges")
            _log_progress(results, f"✓ Hydrologist: {h_nodes} nodes, {len(lineage_edges)} edges", "success")
            logger.info(f"   Saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Hydrologist Agent failed: {e}")
            _log_progress(results, f"✗ Hydrologist failed: {e}", "error")
            results["errors"].append({"agent": "hydrologist", "error": str(e)})
            results["warnings"].append(f"Hydrologist analysis incomplete: {e}")
    
    # ========================
# Run Semanticist Agent
# ========================
    if "semanticist" in agents:
        # Check if Semanticist is available (LLM module)
        if not HAS_SEMANTICIST:
            logger.warning("SemanticistAgent not available - skipping")
            _log_progress(results, "⚠ Semanticist: Module not available (LLM not configured)", "warning")
            results["warnings"].append("Semanticist skipped: LLM module not available")
        else:
            try:
                logger.info("[3/4] Running Semanticist Agent...")
                _log_progress(results, "Agent 3 (Semanticist): Starting LLM analysis", "info")
                
                semanticist = SemanticistAgent(repo_path=repo_path, budget_limit=2.00)
                sem_results = semanticist.run(
                    results.get("surveyor", {}), 
                    results.get("hydrologist", {})
                )
                
                results["semanticist"] = {
                    "modules_analyzed": len(sem_results.get("purpose_statements", {})),
                    "domains": len(sem_results.get("domain_clusters", {})),
                    "budget": sem_results.get("budget", {}),
                    "purpose_statements": sem_results.get("purpose_statements", {}),
                    "domain_clusters": sem_results.get("domain_clusters", {})
                }
                
                _log_progress(
                    results, 
                    f"✓ Semanticist: {results['semanticist']['modules_analyzed']} modules, {results['semanticist']['domains']} domains", 
                    "success"
                )
                
            except Exception as e:
                logger.error(f"Semanticist failed: {e}")
                _log_progress(results, f"✗ Semanticist failed: {e}", "error")
                results["errors"].append({"agent": "semanticist", "error": str(e)})
                results["warnings"].append(f"Semanticist analysis incomplete: {e}")
    
    # ========================
    # Run Archivist Agent (Agent 4)
    # ========================
    if "archivist" in agents:
        try:
            logger.info("[4/4] Running Archivist Agent...")
            _log_progress(results, "Agent 4 (Archivist): Generating living context artifacts", "info")
            
            from .agents.archivist import ArchivistAgent
            
            archivist = ArchivistAgent(repo_path=repo_path, output_dir=output_dir / ".cartographer")
            archivist_results = archivist.run(
                results.get("surveyor", {}),
                results.get("hydrologist", {}),
                results.get("semanticist", {})
            )
            
            if archivist_results.get("ok"):
                results["archivist"] = {
                    "ok": True,
                    "artifacts": archivist_results.get("artifacts", {}),
                    "output_dir": archivist_results.get("output_dir")
                }
                
                # Add artifact paths to main results
                for artifact_name, artifact_path in archivist_results.get("artifacts", {}).items():
                    if artifact_path:
                        results["artifacts"].append(artifact_path)
                
                _log_progress(
                    results,
                    f"✓ Archivist: {len(archivist_results.get('artifacts', {}))} artifacts generated",
                    "success"
                )
                logger.info(f"   Output directory: {archivist_results.get('output_dir')}")
            else:
                raise RuntimeError("Archivist run returned ok=False")
                
        except ImportError as e:
            # Graceful degradation if Archivist module not available
            logger.warning(f"Archivist Agent not available: {e}")
            _log_progress(results, "⚠ Archivist: Module not available (optional)", "warning")
            results["warnings"].append(f"Archivist skipped: {e}")
            
        except Exception as e:
            logger.error(f"Archivist Agent failed: {e}")
            _log_progress(results, f"✗ Archivist failed: {e}", "error")
            results["errors"].append({"agent": "archivist", "error": str(e)})
            results["warnings"].append(f"Archivist analysis incomplete: {e}")
    
    # ========================
    # Log Summary
    # ========================
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Agents run: {len(agents)}")
    logger.info(f"Artifacts generated: {len(results['artifacts'])}")
    logger.info(f"Errors: {len(results['errors'])}")
    logger.info(f"Warnings: {len(results['warnings'])}")
    
    _log_progress(results, "✓ Analysis pipeline complete", "success")
    
    return results