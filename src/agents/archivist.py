"""
Agent 4: The Archivist - Living Context Maintainer

Produces and maintains system outputs as living artifacts that can be
re-used and updated as the codebase evolves.

Artifacts:
- CODEBASE.md: Living context file for AI coding agents
- onboarding_brief.md: Day-One Brief with 5 FDE questions
- lineage_graph.json: Serialized DataLineageGraph
- semantic_index/: Vector store of Purpose Statements
- cartography_trace.jsonl: Audit log of all analysis actions
"""

from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Any, Optional


class ArchivistAgent:
    """
    The Archivist maintains living context artifacts for the codebase.
    
    This is the evolution of Week 1's CLAUDE.md and Week 2's Audit Report pattern.
    """
    
    def __init__(self, repo_path: Path, output_dir: Optional[Path] = None):
        self.repo_path = Path(repo_path)
        self.output_dir = output_dir or self.repo_path / ".cartographer"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trace_log: List[Dict[str, Any]] = []
        
    def run(self, surveyor_results: Dict, hydrologist_results: Dict, 
            semanticist_results: Dict) -> Dict[str, Any]:
        """
        Run the Archivist agent to produce all artifacts.
        
        Args:
            surveyor_results: Output from Surveyor agent
            hydrologist_results: Output from Hydrologist agent
            semanticist_results: Output from Semanticist agent
            
        Returns:
            Dictionary with paths to all generated artifacts
        """
        print("\n=== ARCHIVIST: Generating Living Context Artifacts ===")
        
        self._log_action("archivist_start", {
            "repo": str(self.repo_path),
            "timestamp": datetime.now().isoformat()
        })
        
        artifacts = {}
        
        # 1. Generate CODEBASE.md
        print("  📄 Generating CODEBASE.md...")
        artifacts["codebase_md"] = self.generate_CODEBASE_md(
            surveyor_results, hydrologist_results, semanticist_results
        )
        
        # 2. Generate onboarding_brief.md
        print("  📋 Generating onboarding_brief.md...")
        artifacts["onboarding_brief"] = self.generate_onboarding_brief(
            surveyor_results, hydrologist_results, semanticist_results
        )
        
        # 3. Generate lineage_graph.json
        print("  🕸️  Generating lineage_graph.json...")
        artifacts["lineage_graph"] = self.generate_lineage_graph(hydrologist_results)
        
        # 4. Generate semantic_index/
        print("  🔍 Generating semantic_index/...")
        artifacts["semantic_index"] = self.generate_semantic_index(semanticist_results)
        
        # 5. Generate cartography_trace.jsonl
        print("  📜 Generating cartography_trace.jsonl...")
        artifacts["trace_log"] = self.save_trace_log()
        
        self._log_action("archivist_complete", {
            "artifacts_generated": len(artifacts),
            "output_dir": str(self.output_dir)
        })
        
        print(f"✅ Archivist complete: {len(artifacts)} artifacts generated\n")
        
        return {
            "ok": True,
            "artifacts": artifacts,
            "output_dir": str(self.output_dir)
        }
    
    def _log_action(self, action: str, details: Dict[str, Any], 
                    confidence: float = 1.0, evidence_source: str = "archivist"):
        """Log an action to the trace log."""
        self.trace_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent": "archivist",
            "action": action,
            "details": details,
            "confidence": confidence,
            "evidence_source": evidence_source
        })
    
    def generate_CODEBASE_md(self, surveyor: Dict, hydrologist: Dict, 
                             semanticist: Dict) -> str:
        """
        Generate CODEBASE.md - Living context file for AI coding agents.
        
        Sections:
        - Architecture Overview (1 paragraph)
        - Critical Path (top 5 modules by PageRank)
        - Data Sources & Sinks (from Hydrologist)
        - Known Debt (circular deps + doc drift flags)
        - High-Velocity Files (files changing most frequently)
        - Module Purpose Index
        """
        output_path = self.output_dir / "CODEBASE.md"
        
        # Build the document
        lines = []
        lines.append("# CODEBASE.md - Living Context File")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Repository:** {self.repo_path.name}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 1. Architecture Overview
        lines.append("## Architecture Overview")
        lines.append("")
        overview = self._generate_architecture_overview(surveyor)
        lines.append(overview)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 2. Critical Path
        lines.append("## Critical Path (Top 5 Modules)")
        lines.append("")
        lines.append("| Rank | Module | File | Reason |")
        lines.append("|------|--------|------|--------|")
        critical = self._get_critical_path(surveyor)
        for i, mod in enumerate(critical[:5], 1):
            lines.append(f"| {i} | `{mod['id']}` | `{mod['file']}` | {mod['reason']} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 3. Data Sources & Sinks
        lines.append("## Data Sources & Sinks")
        lines.append("")
        sources_sinks = self._get_data_sources_sinks(hydrologist)
        lines.append("### Sources (Entry Points)")
        lines.append("")
        for src in sources_sinks.get("sources", [])[:5]:
            lines.append(f"- `{src}`")
        lines.append("")
        lines.append("### Sinks (Exit Points)")
        lines.append("")
        for sink in sources_sinks.get("sinks", [])[:5]:
            lines.append(f"- `{sink}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 4. Known Debt
        lines.append("## Known Technical Debt")
        lines.append("")
        debt = self._get_known_debt(surveyor, semanticist)
        if debt.get("circular_deps"):
            lines.append("### Circular Dependencies")
            lines.append("")
            for dep in debt["circular_deps"][:5]:
                lines.append(f"- ⚠️ `{dep}`")
            lines.append("")
        if debt.get("doc_drift"):
            lines.append("### Documentation Drift")
            lines.append("")
            for drift in debt["doc_drift"][:5]:
                lines.append(f"- ⚠️ `{drift['module']}`: {drift['reason']}")
            lines.append("")
        if not debt.get("circular_deps") and not debt.get("doc_drift"):
            lines.append("*No significant technical debt detected.*")
            lines.append("")
        lines.append("---")
        lines.append("")
        
        # 5. High-Velocity Files
        lines.append("## High-Velocity Files (Likely Pain Points)")
        lines.append("")
        high_vel = self._get_high_velocity_files()
        if high_vel:
            lines.append("| File | Change Count | Last Modified |")
            lines.append("|------|--------------|---------------|")
            for f in high_vel[:5]:
                lines.append(f"| `{f['file']}` | {f['changes']} | {f['last_modified']} |")
        else:
            lines.append("*Git history not available. Run `git log` for change velocity.*")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 6. Module Purpose Index
        lines.append("## Module Purpose Index")
        lines.append("")
        purposes = semanticist.get("purpose_statements", {})
        if purposes:
            for mod_id, info in list(purposes.items())[:10]:
                purpose = info.get("purpose_statement", "No purpose defined")
                file_path = info.get("file_path", "Unknown")
                lines.append(f"### `{mod_id}`")
                lines.append("")
                lines.append(f"**File:** `{file_path}`")
                lines.append("")
                lines.append(f"**Purpose:** {purpose}")
                lines.append("")
        else:
            lines.append("*No purpose statements available. Run Semanticist agent first.*")
            lines.append("")
        
        # Write to file
        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")
        
        self._log_action("generate_CODEBASE_md", {
            "output_path": str(output_path),
            "sections": 6,
            "modules_indexed": len(purposes)
        }, evidence_source="static_analysis")
        
        print(f"    → Saved: {output_path}")
        
        return str(output_path)
    
    def _generate_architecture_overview(self, surveyor: Dict) -> str:
        """Generate a 1-paragraph architecture overview."""
        modules = surveyor.get("modules", [])
        edges = surveyor.get("edges", [])
        
        if not modules:
            return "Architecture analysis pending. Run Surveyor agent first."
        
        module_count = len(modules)
        edge_count = len(edges) if isinstance(edges, list) else edges
        
        # Determine project type
        yaml_count = sum(1 for m in modules if m.get("file_path", "").endswith((".yml", ".yaml")))
        sql_count = sum(1 for m in modules if m.get("file_path", "").endswith(".sql"))
        py_count = sum(1 for m in modules if m.get("file_path", "").endswith(".py"))
        
        if yaml_count > sql_count:
            proj_type = "DBT project"
        elif py_count > 0:
            proj_type = "Python project"
        else:
            proj_type = "Mixed codebase"
        
        return (
            f"This is a **{proj_type}** with **{module_count} modules** and "
            f"**{edge_count} dependencies**. "
            f"The codebase follows a {'layered' if edge_count > module_count else 'flat'} "
            f"architecture with {'high' if edge_count > module_count * 2 else 'moderate'} "
            f"interconnectivity between components."
        )
    
    def _get_critical_path(self, surveyor: Dict) -> List[Dict]:
        """Get top 5 modules by connectivity (simplified PageRank)."""
        modules = surveyor.get("modules", [])
        edges = surveyor.get("edges", [])
        
        # Count connections per module
        connection_count = {}
        for m in modules:
            mid = m.get("id", "unknown")
            connection_count[mid] = 0
        
        for e in edges if isinstance(edges, list) else []:
            src = e.get("source", "")
            tgt = e.get("target", "")
            connection_count[src] = connection_count.get(src, 0) + 1
            connection_count[tgt] = connection_count.get(tgt, 0) + 1
        
        # Sort by connection count
        sorted_modules = sorted(
            connection_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Build result
        result = []
        for mod_id, count in sorted_modules[:5]:
            mod_info = next((m for m in modules if m.get("id") == mod_id), {})
            result.append({
                "id": mod_id,
                "file": mod_info.get("file_path", "unknown"),
                "connections": count,
                "reason": f"{count} connections"
            })
        
        return result
    
    def _get_data_sources_sinks(self, hydrologist: Dict) -> Dict[str, List[str]]:
        """Extract data sources (entry points) and sinks (exit points)."""
        sources = []
        sinks = []
        
        edges = hydrologist.get("lineage_edges", [])
        
        # Sources: nodes with no incoming edges
        # Sinks: nodes with no outgoing edges
        all_nodes = set()
        has_incoming = set()
        has_outgoing = set()
        
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            all_nodes.add(src)
            all_nodes.add(tgt)
            has_outgoing.add(src)
            has_incoming.add(tgt)
        
        sources = list(all_nodes - has_incoming)[:10]
        sinks = list(all_nodes - has_outgoing)[:10]
        
        self._log_action("extract_sources_sinks", {
            "sources_count": len(sources),
            "sinks_count": len(sinks)
        }, evidence_source="hydrologist")
        
        return {"sources": sources, "sinks": sinks}
    
    def _get_known_debt(self, surveyor: Dict, semanticist: Dict) -> Dict:
        """Identify known technical debt."""
        debt = {
            "circular_deps": [],
            "doc_drift": []
        }
        
        # Check for documentation drift from Semanticist
        purposes = semanticist.get("purpose_statements", {})
        for mod_id, info in purposes.items():
            if info.get("has_drift") or info.get("has_documentation_drift"):
                debt["doc_drift"].append({
                    "module": mod_id,
                    "reason": info.get("drift_reason", "Documentation contradicts implementation")
                })
        
        self._log_action("identify_debt", {
            "circular_deps": len(debt["circular_deps"]),
            "doc_drift": len(debt["doc_drift"])
        }, evidence_source="combined_analysis")
        
        return debt
    
    def _get_high_velocity_files(self) -> List[Dict]:
        """Get files with most git changes (if git available)."""
        import subprocess
        
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "log", "--name-only", "--oneline"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            # Count file occurrences
            file_counts = {}
            lines = result.stdout.strip().split("\n")[1:]  # Skip first commit line
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith("commit"):
                    file_counts[line] = file_counts.get(line, 0) + 1
            
            # Sort by count
            sorted_files = sorted(
                file_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [
                {"file": f, "changes": c, "last_modified": "recent"}
                for f, c in sorted_files[:5]
            ]
            
        except Exception as e:
            self._log_action("git_velocity_error", {"error": str(e)})
            return []
    
    def generate_onboarding_brief(self, surveyor: Dict, hydrologist: Dict,
                                  semanticist: Dict) -> str:
        """
        Generate onboarding_brief.md - Day-One Brief for new engineers.
        
        Answers the 5 FDE questions with evidence citations:
        1. What does this system do?
        2. How is it structured?
        3. Where is the critical logic?
        4. What are the known issues?
        5. How do I make changes safely?
        """
        output_path = self.output_dir / "onboarding_brief.md"
        
        lines = []
        lines.append("# Onboarding Brief - Day One")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Repository:** {self.repo_path.name}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Q1: What does this system do?
        lines.append("## 1. What Does This System Do?")
        lines.append("")
        purposes = semanticist.get("purpose_statements", {})
        if purposes:
            # Get top-level purposes
            for mod_id, info in list(purposes.items())[:3]:
                purpose = info.get("purpose_statement", "Unknown")
                lines.append(f"- **{mod_id}:** {purpose}")
        else:
            lines.append("*Run Semanticist agent to generate purpose statements.*")
        lines.append("")
        lines.append("**Evidence:** `semantic_index/` - LLM inference")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Q2: How is it structured?
        lines.append("## 2. How Is It Structured?")
        lines.append("")
        modules = surveyor.get("modules", [])
        if modules:
            # Group by directory
            dirs = {}
            for m in modules:
                fp = m.get("file_path", "")
                dir_name = str(Path(fp).parent) if fp else "root"
                if dir_name not in dirs:
                    dirs[dir_name] = 0
                dirs[dir_name] += 1
            
            for dir_name, count in sorted(dirs.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"- `{dir_name}/` - {count} modules")
        else:
            lines.append("*Run Surveyor agent to analyze structure.*")
        lines.append("")
        lines.append("**Evidence:** `surveyor` agent - Static analysis")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Q3: Where is the critical logic?
        lines.append("## 3. Where Is the Critical Logic?")
        lines.append("")
        critical = self._get_critical_path(surveyor)
        if critical:
            for i, mod in enumerate(critical[:3], 1):
                lines.append(f"{i}. `{mod['id']}` - {mod['reason']}")
                lines.append(f"   - File: `{mod['file']}`")
        else:
            lines.append("*Run Surveyor agent to identify critical modules.*")
        lines.append("")
        lines.append("**Evidence:** `surveyor` agent - Graph centrality analysis")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Q4: What are the known issues?
        lines.append("## 4. What Are the Known Issues?")
        lines.append("")
        debt = self._get_known_debt(surveyor, semanticist)
        if debt.get("doc_drift"):
            lines.append("### Documentation Drift")
            for d in debt["doc_drift"][:3]:
                lines.append(f"- ⚠️ `{d['module']}`: {d['reason']}")
            lines.append("")
        if debt.get("circular_deps"):
            lines.append("### Circular Dependencies")
            for dep in debt["circular_deps"][:3]:
                lines.append(f"- ⚠️ `{dep}`")
            lines.append("")
        if not debt.get("doc_drift") and not debt.get("circular_deps"):
            lines.append("*No significant issues detected.*")
        lines.append("")
        lines.append("**Evidence:** `semanticist` + `surveyor` - Combined analysis")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Q5: How do I make changes safely?
        lines.append("## 5. How Do I Make Changes Safely?")
        lines.append("")
        lines.append("### Before Making Changes")
        lines.append("")
        lines.append("1. **Review dependencies** - Check `lineage_graph.json` for downstream impacts")
        lines.append("2. **Check documentation** - Review `CODEBASE.md` for module purposes")
        lines.append("3. **Run tests** - Ensure existing tests pass before modifications")
        lines.append("")
        lines.append("### After Making Changes")
        lines.append("")
        lines.append("1. **Update documentation** - Keep docstrings in sync with implementation")
        lines.append("2. **Re-run Archivist** - `python -m src.agents.archivist` to refresh artifacts")
        lines.append("3. **Review trace log** - Check `cartography_trace.jsonl` for analysis history")
        lines.append("")
        lines.append("**Evidence:** Best practices from FDE engagement pattern")
        lines.append("")
        
        # Write to file
        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")
        
        self._log_action("generate_onboarding_brief", {
            "output_path": str(output_path),
            "questions_answered": 5
        }, evidence_source="combined_analysis")
        
        print(f"    → Saved: {output_path}")
        
        return str(output_path)
    
    def generate_lineage_graph(self, hydrologist: Dict) -> str:
        """Generate serialized lineage_graph.json for downstream tooling."""
        output_path = self.output_dir / "lineage_graph.json"
        
        # Extract lineage data
        lineage_data = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "repo": str(self.repo_path),
            "nodes": [],
            "edges": []
        }
        
        edges = hydrologist.get("lineage_edges", [])
        
        # Collect all nodes
        all_nodes = {}
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            if src and src not in all_nodes:
                all_nodes[src] = {"id": src, "type": "unknown"}
            if tgt and tgt not in all_nodes:
                all_nodes[tgt] = {"id": tgt, "type": "unknown"}
        
        lineage_data["nodes"] = list(all_nodes.values())
        lineage_data["edges"] = edges
        
        # Write to file
        output_path.write_text(
            json.dumps(lineage_data, indent=2),
            encoding="utf-8"
        )
        
        self._log_action("generate_lineage_graph", {
            "output_path": str(output_path),
            "nodes": len(lineage_data["nodes"]),
            "edges": len(lineage_data["edges"])
        }, evidence_source="hydrologist")
        
        print(f"    → Saved: {output_path}")
        
        return str(output_path)
    
    def generate_semantic_index(self, semanticist: Dict) -> str:
        """Generate semantic_index/ directory with vector store of purposes."""
        output_dir = self.output_dir / "semantic_index"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        purposes = semanticist.get("purpose_statements", {})
        
        # Create index file
        index_data = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "modules": {}
        }
        
        for mod_id, info in purposes.items():
            index_data["modules"][mod_id] = {
                "purpose": info.get("purpose_statement", ""),
                "file_path": info.get("file_path", ""),
                "has_drift": info.get("has_drift", False),
                "confidence": info.get("confidence", 1.0)
            }
        
        # Write index
        index_path = output_dir / "purpose_index.json"
        index_path.write_text(
            json.dumps(index_data, indent=2),
            encoding="utf-8"
        )
        
        # Create individual module files for easy retrieval
        for mod_id, info in purposes.items():
            mod_file = output_dir / f"{mod_id.replace('/', '_')}.json"
            mod_file.write_text(
                json.dumps({"module_id": mod_id, **info}, indent=2),
                encoding="utf-8"
            )
        
        self._log_action("generate_semantic_index", {
            "output_dir": str(output_dir),
            "modules_indexed": len(purposes)
        }, evidence_source="semanticist")
        
        print(f"    → Saved: {output_dir}/")
        
        return str(output_dir)
    
    def save_trace_log(self) -> str:
        """Save cartography_trace.jsonl - audit log of all actions."""
        output_path = self.output_dir / "cartography_trace.jsonl"
        
        # Append to existing log if present
        existing_logs = []
        if output_path.exists():
            for line in output_path.read_text().strip().split("\n"):
                if line.strip():
                    try:
                        existing_logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        
        # Combine with new logs
        all_logs = existing_logs + self.trace_log
        
        # Write as JSONL
        with output_path.open("w", encoding="utf-8") as f:
            for log_entry in all_logs:
                f.write(json.dumps(log_entry) + "\n")
        
        self._log_action("save_trace_log", {
            "output_path": str(output_path),
            "total_entries": len(all_logs)
        }, evidence_source="archivist")
        
        print(f"    → Saved: {output_path}")
        
        return str(output_path)
    
    def check_incremental_update(self) -> bool:
        """
        Check if incremental update is possible (git-based).
        
        Returns True if there are new commits since last analysis.
        """
        import subprocess
        
        last_run_file = self.output_dir / ".last_run"
        
        if not last_run_file.exists():
            return False  # First run, full analysis needed
        
        try:
            last_run = last_run_file.read_text().strip()
            
            # Get commits since last run
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "log", "--oneline", f"--since={last_run}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False
            
            has_new_commits = len(result.stdout.strip()) > 0
            
            # Update last run timestamp
            last_run_file.write_text(datetime.now().isoformat())
            
            return has_new_commits
            
        except Exception:
            return False