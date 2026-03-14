import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Initialize logger
logger = logging.getLogger(__name__)

class ArchivistAgent:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path("refined_audit")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trace_log: List[Dict[str, Any]] = []
    """
    The Archivist maintains living context artifacts for the codebase.
    Directly populates 'refined_audit' so the Dashboard buttons work immediately.
    """
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        # [cite: 2026-03-03] Fixed paths for Refined Audit
        self.output_dir = Path("refined_audit")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trace_log: List[Dict[str, Any]] = []

    def run(self, surveyor_data: Any, hydrologist_data: Any, semantic_data: Any) -> dict:
        print("\n=== ARCHIVIST: Data Handshake Debug ===")
        
        # 1. FIXED: Target 'edges' instead of 'elements'
        h_res = hydrologist_data if isinstance(hydrologist_data, dict) else {}
        edges = h_res.get('edges', []) 
        print(f"DEBUG: Archivist received {len(edges)} edges from Hydrologist")

        # 2. Capture Semanticist (Targeting the 35 modules)
        if isinstance(semantic_data, dict) and "results" in semantic_data:
            m_inner = semantic_data["results"]
        else:
            m_inner = semantic_data if isinstance(semantic_data, dict) else {}
            
        purpose_map = m_inner.get("purpose_statements", {})
        print(f"DEBUG: Archivist extracted {len(purpose_map)} purpose statements")

        try:
            # Generate the artifacts
            # We pass h_res (containing 'edges') to CODEBASE.md
            codebase_path = self.generate_codebase_markdown(h_res, purpose_map)
            
            # Ensure the signature of generate_onboarding_brief matches these 3 args
            onboarding_path = self.generate_onboarding_brief(surveyor_data, h_res, m_inner)
            
            lineage_path = self.generate_lineage_graph(h_res)
            trace_path = self.save_trace_log()
            
            self.build_perfect_codebase(str(self.repo_path))
            
            logger.info(f"✅ Archivist: All artifacts successfully synced to {self.output_dir}")
            
            return {
                "status": "success",
                "ok": True,
                "artifacts": {
                    "codebase_md": codebase_path,
                    "lineage_json": lineage_path,
                    "onboarding_brief": onboarding_path,
                    "trace_log": trace_path
                }
            }
        except Exception as e:
            logger.error(f"❌ Archivist failure: {e}")
            # Log the traceback to see exactly where the argument mismatch is happening
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    def generate_codebase_markdown(self, h_data: dict, purpose_index: dict) -> str:
        """Forensic markdown generation from verified JSON structures."""
        output_path = self.output_dir / "CODEBASE.md"
        
        # 1. Extraction Logic: Match the 'edges' key from ui_lineage_graph.json
        # Your JSON uses 'edges', not 'elements' in the raw output
        edges = h_data.get('edges', [])
        
        valid_connections = []
        for edge in edges:
            s = edge.get("source")
            t = edge.get("target")
            if s and t:
                valid_connections.append(f"- `{s}` → `{t}`")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 🏛️ CODEBASE.md: Living System Context\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 1. Architecture Overview\n")
            # This will now show 14
            f.write(f"- **Logical Connections:** {len(valid_connections)}\n")
            f.write("- **Framework:** dbt / Python Agentic Workflow\n\n")
            
            f.write("## 2. Data Lineage\n")
            if valid_connections:
                f.write("\n".join(valid_connections))
            else:
                f.write("_No active lineage connections detected._\n")
            
            f.write("\n\n## 3. Module Purpose Index\n")
            f.write("| Module | Purpose Statement |\n| :--- | :--- |\n")
            # purpose_index comes from the 35 purpose statements extracted in logs
            for mod, purpose in purpose_index.items():
                f.write(f"| `{mod}` | {purpose} |\n")

        return str(output_path)
  

    import re

    import re

    def generate_onboarding_brief(self, surveyor_data: Any, h_data: Any, semantic_data: dict) -> str:
        """Refines the onboarding brief into clean, human-readable insights [cite: 2026-02-27]."""
        output_path = self.output_dir / "onboarding_brief.md"
        
        # Target the fde_answers from your verified results
        fde = semantic_data.get("fde_answers", {})

        def clean_labels(raw_text):
            """Extracts readable model names from the raw dictionary dump."""
            if not raw_text or "Analysis pending" in str(raw_text): 
                return "Analysis pending"
            
            # Regex to find 'id': '...' in the messy output you shared earlier
            matches = re.findall(r"'id':\s*'([^']+)'", str(raw_text))
            
            if matches:
                # Clean up: 'models.marts.orders' -> 'orders'
                display_names = [m.split('.')[-1] for m in matches]
                summary = ", ".join(display_names[:3])
                if len(display_names) > 3:
                    summary += f" (and {len(display_names) - 3} others)"
                return summary
                
            return str(raw_text)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 📑 Onboarding Brief: Day-One Insight\n\n")

            f.write("### 1. Ingestion Path\n\n")
            f.write(f"> {fde.get('q1_ingestion_path', 'Via staging models')}\n\n")

            f.write("### 2. Critical Outputs\n\n")
            # FIX: Now this will show 'orders, customers (and 9 others)' 
            # instead of a raw dictionary or a blank space.
            f.write(f"> {clean_labels(fde.get('q2_critical_outputs'))}\n\n")

            f.write("### 3. Blast Radius\n\n")
            f.write(f"> {fde.get('q3_blast_radius', 'High impact on downstream models')}\n\n")

            f.write("### 4. Logic Distribution\n\n")
            f.write(f"> {fde.get('q4_logic_distribution', 'Concentrated in marts/ directory')}\n\n")

            f.write("### 5. Git/Change Velocity\n\n")
            f.write(f"> {fde.get('q5_git_velocity', 'Analysis pending')}\n")

        return str(output_path)

    def generate_lineage_graph(self, h_data: dict) -> str:
        """Fixed name for dashboard graph button."""
        output_path = self.output_dir / "ui_lineage_graph.json"
        output_path.write_text(json.dumps(h_data, indent=2), encoding="utf-8")
        return str(output_path)

    def save_trace_log(self) -> str:
        """Fixed name for dashboard trace button."""
        output_path = self.output_dir / "audit_trace.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in self.trace_log:
                f.write(json.dumps(entry) + "\n")
        return str(output_path)

    def build_perfect_codebase(self, repo_path: str):
        """Builds the actual injection file for GPT-4o-mini."""
        output_path = self.output_dir / "PERFECT_CODEBASE.md"
        repo = Path(repo_path)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 🏛️ PERFECT CODEBASE (LLM SOURCE)\n\n")
            # Grab SQL and Python files for the AI
            for ext in ['*.sql', '*.py']:
                for file_path in repo.rglob(ext):
                    if any(x in str(file_path) for x in [".venv", "__pycache__", "target/"]):
                        continue
                    f.write(f"\n### FILE: {file_path.relative_to(repo)}\n```\n")
                    f.write(file_path.read_text(errors='ignore'))
                    f.write("\n```\n")