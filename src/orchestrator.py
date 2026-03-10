"""Orchestrator  Wires agents in sequence, serializes outputs.

Pipeline: Surveyor -> Hydrologist -> Semanticist -> Archivist
"""
from pathlib import Path
from typing import Optional

from agents.surveyor import SurveyorAgent
from agents.hydrologist import HydrologistAgent
# from agents.semanticist import SemanticistAgent  # TASK-009
# from agents.archivist import ArchivistAgent      # TASK-010


def run_pipeline(
    repo_path: Path,
    output_dir: Path = Path(".cartography"),
    incremental: bool = False,
    days_lookback: int = 30,
) -> dict[str, Path]:
    """Run full analysis pipeline and return artifact paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    
    # === Phase 1: Surveyor (Static Structure) ===
    print("[1/4] Running Surveyor Agent...")
    surveyor = SurveyorAgent(repo_path=repo_path, output_dir=output_dir, days_lookback=days_lookback)
    module_graph = surveyor.run(include_tests=False)
    artifacts["module_graph"] = surveyor.save_artifacts()
    print(f"   Module graph: {artifacts['module_graph']} ({module_graph.total_nodes} nodes, {module_graph.total_edges} edges)")
    
    # === Phase 2: Hydrologist (Data Lineage) ===
    print("[2/4] Running Hydrologist Agent...")
    hydrologist = HydrologistAgent(repo_path=repo_path, output_dir=output_dir)
    lineage_graph = hydrologist.run(module_graph=module_graph)
    artifacts["lineage_graph"] = hydrologist.save_artifacts()
    print(f"   Lineage graph: {artifacts['lineage_graph']}")
    
    # === Phase 3: Semanticist (LLM Enrichment)  TASK-009 ===
    # print("[3/4] Running Semanticist Agent...")
    # semanticist = SemanticistAgent(repo_path=repo_path, output_dir=output_dir)
    # semanticist.enrich(module_graph, lineage_graph)
    # artifacts["semantic_enrichment"] = semanticist.save_artifacts()
    
    # === Phase 4: Archivist (Documentation)  TASK-010 ===
    # print("[4/4] Running Archivist Agent...")
    # archivist = ArchivistAgent(repo_path=repo_path, output_dir=output_dir)
    # artifacts["codebase_md"] = archivist.generate_codebase_md(module_graph, lineage_graph)
    # artifacts["onboarding_brief"] = archivist.generate_onboarding_brief()
    
    print(f"\n Pipeline complete. Artifacts in {output_dir}")
    return artifacts


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <repo_path> [--output <dir>]")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(".cartography")
    
    run_pipeline(repo_path, output_dir)
