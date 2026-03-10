"""Surveyor Agent — Phase 1: Deterministic Structural Extraction.

Implements the Rosetta Stone Architecture for multi-language parsing,
evidence-backed confidence scoring, and graph-theoretic hub detection.

Constitution Rules Enforced:
- Rule 1: No hallucinated code (only parsed AST nodes)
- Rule 3: Evidence-based outputs (confidence_score + evidence_type)
- Rule 4: Graceful degradation (fail-open on parse errors)
"""
import json
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime

import networkx as nx
from tree_sitter_languages import get_language, get_parser
from pydantic import ValidationError

from ..models.nodes import ModuleNode, ConfidenceTier, EvidenceType, SymbolType
from ..models.edges import Edge, EdgeType
from ..models.graph import CartographyGraph
from ..analyzers.git_analyzer import GitVelocityAnalyzer  # ✅ Looks in analyzers/


# === LanguageRouter: Map extensions to Tree-sitter languages ===
LANGUAGE_ROUTER: dict[str, str] = {
    ".py": "python",
    ".sql": "sql",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    # Add more as needed
}

# === Confidence Mapping: Evidence type → Confidence tier (Reaper Protocol) ===
EVIDENCE_TO_CONFIDENCE: dict[EvidenceType, ConfidenceTier] = {
    "static": 1.0,      # Direct AST parse
    "algorithmic": 0.9, # Graph algorithm (PageRank, reachability)
    "inference": 0.6,   # LLM or heuristic inference
    "heuristic": 0.3,   # Pattern match or best guess
}


class SurveyorAgent:
    """Deterministic engine for extracting codebase structural skeleton.
    
    Implements:
    - Multi-language parsing via tree-sitter-languages (pre-compiled wheels)
    - S-expression query library for structural pattern matching
    - Git velocity analysis with --follow for rename tracking
    - NetworkX DiGraph with PageRank hub detection
    - Evidence-backed confidence scoring per Constitution Rule 3
    - Fail-open graceful degradation per Constitution Rule 4
    """
    
    def __init__(
        self,
        repo_path: Path,
        output_dir: Path = Path(".cartography"),
        days_lookback: int = 30,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir)
        self.git_analyzer = GitVelocityAnalyzer(self.repo_path, days_lookback)
        
        # Graph state
        self.graph = CartographyGraph(
            repo_name=self.repo_path.name,
            repo_path=str(self.repo_path),
            base_commit_sha=self._get_current_commit(),
        )
        
        # Query library paths
        self.query_lib = Path(__file__).parent.parent / "analyzers" / "query_library"
    
    def _get_current_commit(self) -> str:
        """Get current git commit SHA for reproducibility."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True, timeout=10
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"
    
    def _get_language(self, file_path: Path) -> Optional[str]:
        """LanguageRouter: Map file extension to Tree-sitter language name."""
        return LANGUAGE_ROUTER.get(file_path.suffix.lower())
    
    def _load_query(self, language: str, query_name: str) -> str:
        """Load S-expression query from query library."""
        query_path = self.query_lib / language / f"{query_name}.scm"
        if query_path.exists():
            return query_path.read_text(encoding="utf-8")
        return ""
    
    def _resolve_import_path(
        self,
        import_path: str,
        current_file: Path,
        repo_root: Path
    ) -> Optional[str]:
        """Resolve relative imports to absolute module paths.
        
        Handles:
        - Absolute imports: "utils.helpers" → "src/utils/helpers.py"
        - Relative imports: ".helpers" → same-dir helpers.py
        - Package imports: "utils" → "src/utils/__init__.py" or "src/utils.py"
        
        Returns:
            Resolved module ID (e.g., "utils.helpers") or None if unresolvable
        """
        # Skip external/3rd-party imports (will become GhostNodes)
        if import_path.startswith(("pandas", "numpy", "sqlglot", "networkx")):
            return None
        
        current_dir = current_file.parent
        parts = import_path.split(".")
        
        # Handle relative imports (start with .)
        if import_path.startswith("."):
            dots = len(import_path) - len(import_path.lstrip("."))
            for _ in range(dots):
                current_dir = current_dir.parent
            parts = import_path.lstrip(".").split(".")
            if not parts or parts == [""]:
                parts = []
        
        # Try to resolve path
        for i in range(len(parts), 0, -1):
            candidate_parts = parts[:i]
            candidate_path = repo_root / Path(*candidate_parts)
            
            # Check for module file
            if (candidate_path.with_suffix(".py")).exists():
                return ".".join(candidate_parts)
            # Check for package __init__.py
            if (candidate_path / "__init__.py").exists():
                return ".".join(candidate_parts)
        
        # Fallback: return as-is (may be external)
        return import_path if import_path else None
    
    def analyze_module(self, file_path: Path) -> Optional[ModuleNode]:
        """Core function: Extract structural metadata from a single module.
        
        Uses S-expression queries to perform AST pattern matching.
        Implements fail-open: returns None on parse error, logs warning.
        
        Returns:
            ModuleNode with evidence-backed confidence, or None on failure
        """
        language_name = self._get_language(file_path)
        if not language_name:
            return None  # Unknown language, skip gracefully
        
        try:
            # Initialize parser with pre-compiled grammar
            language = get_language(language_name)
            parser = get_parser(language_name)
            
            # Parse file content
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = parser.parse(bytes(content, "utf-8"))
            root_node = tree.root_node
            
            # Extract imports via S-expression query
            imports = []
            import_query = self._load_query(language_name, "imports")
            if import_query:
                query = language.query(import_query)
                for capture in query.captures(root_node):
                    node, name = capture
                    if name == "import_path":
                        import_text = content[node.start_byte:node.end_byte]
                        resolved = self._resolve_import_path(import_text, file_path, self.repo_path)
                        if resolved:
                            imports.append(resolved)
            
            # Extract public API via S-expression query
            exports = []
            api_query = self._load_query(language_name, "public_api")
            if api_query:
                query = language.query(api_query)
                for capture in query.captures(root_node):
                    node, name = capture
                    if name == "name":
                        symbol_name = content[node.start_byte:node.end_byte]
                        exports.append(symbol_name)
            
            # Compute structural metrics
            rel_path = file_path.relative_to(self.repo_path)
            change_velocity = self.git_analyzer.get_change_velocity(str(rel_path))
            last_modified = self.git_analyzer.get_file_last_modified(str(rel_path))
            
            # Cyclomatic complexity: count decision nodes (simplified)
            decision_keywords = {"if", "for", "while", "elif", "except", "case"}
            complexity = sum(1 for line in content.split("\n") 
                           if any(kw in line for kw in decision_keywords))
            
            # Comment-to-code ratio
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            comment_lines = sum(1 for l in lines if l.startswith(("#", "--", "//")))
            comment_ratio = round(comment_lines / len(lines), 3) if lines else 0.0
            
            # === CONSTITUTION RULE 3: Evidence-based confidence ===
            # Static parse = highest confidence
            confidence = EVIDENCE_TO_CONFIDENCE["static"]
            evidence = "static"
            
            return ModuleNode(
                id=str(rel_path.with_suffix("")).replace("/", ".").replace("\\", "."),
                symbol_type="Module",
                file_path=str(rel_path),
                language=language_name,
                imports=imports,
                exports=exports,
                cyclomatic_complexity=complexity,
                comment_to_code_ratio=comment_ratio,
                lines_of_code=len(lines),
                git_sha=self._get_current_commit(),
                last_analyzed_commit=self._get_current_commit(),
                change_velocity_30d=change_velocity,
                last_modified=last_modified,
                confidence_score=confidence,
                evidence_type=evidence,
                scope="module",
                query_files=[f"{language_name}/imports.scm", f"{language_name}/public_api.scm"]
            )
            
        except Exception as e:
            # === CONSTITUTION RULE 4: Graceful degradation ===
            # Log warning, skip file, continue analysis
            rel_path = file_path.relative_to(self.repo_path) if file_path.is_relative_to(self.repo_path) else file_path
            self.graph.parse_warnings.append(
                f"Failed to parse {rel_path}: {type(e).__name__}: {str(e)[:100]}"
            )
            self.graph.files_skipped.append(str(rel_path))
            return None
    
    def _add_ghost_nodes(self, imports: list[str], module_id: str) -> None:
        """Add GhostNodes for 3rd-party/external dependencies."""
        external_prefixes = ["pandas", "numpy", "sqlglot", "networkx", "torch", "tensorflow"]
        
        for imp in imports:
            prefix = imp.split(".")[0]
            if prefix in external_prefixes:
                ghost_id = f"external.{imp}"
                # Add ghost node if not exists
                if not any(n.id == ghost_id for n in self.graph.modules):
                    ghost = ModuleNode(
                        id=ghost_id,
                        symbol_type="GhostNode",
                        is_ghost_node=True,
                        external_package=prefix,
                        confidence_score=1.0,
                        evidence_type="static",
                        scope="module"
                    )
                    self.graph.add_node(ghost)
                
                # Add IMPORTS edge to ghost
                edge = Edge(
                    source=module_id,
                    target=ghost_id,
                    edge_type="IMPORTS",
                    confidence_score=1.0,
                    evidence_type="static"
                )
                self.graph.add_edge(edge)
    
    def _build_graph(self) -> None:
        """Build NetworkX DiGraph from extracted modules + compute PageRank."""
        # Create NetworkX graph
        nx_graph = nx.DiGraph()
        
        # Add nodes
        for module in self.graph.modules:
            nx_graph.add_node(module.id, **module.model_dump())
        
        # Add edges (IMPORTS relationships)
        for module in self.graph.modules:
            for imp in module.imports:
                # Check if target exists as internal module
                target_exists = any(m.id == imp for m in self.graph.modules)
                target_id = imp if target_exists else f"external.{imp}"
                
                # Add edge
                nx_graph.add_edge(module.id, target_id, edge_type="IMPORTS")
                
                # Also add to Pydantic graph
                edge = Edge(
                    source=module.id,
                    target=target_id,
                    edge_type="IMPORTS",
                    confidence_score=1.0,
                    evidence_type="static"
                )
                self.graph.add_edge(edge)
            
            # Add ghost nodes for external imports
            self._add_ghost_nodes(module.imports, module.id)
        
        # === Hub Detection: PageRank ===
        if nx_graph.number_of_nodes() > 0:
            pagerank = nx.pagerank(nx_graph, alpha=0.85)  # Standard damping factor
            # Top 5 hubs
            hubs = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
            self.graph.architectural_hubs = [hub_id for hub_id, _ in hubs]
        
        # === Cycle Detection: Circular dependencies ===
        cycles = list(nx.simple_cycles(nx_graph))
        if cycles:
            cycle_summary = [f"{' -> '.join(c)}" for c in cycles[:3]]  # Show first 3
            self.graph.parse_warnings.append(
                f"Detected {len(cycles)} circular dependencies: {cycle_summary}"
            )
        
        # === Dead Code Detection: Reachability from entry points ===
        # Find entry points (files with if __name__ == "__main__", route handlers, etc.)
        entry_points = [
            m.id for m in self.graph.modules 
            if m.entry_point_type is not None and m.entry_point_type != "none"
        ]
        
        if entry_points:
            # Compute reachable nodes
            reachable = set()
            for ep in entry_points:
                reachable.update(nx.descendants(nx_graph, ep) | {ep})
            
            # Flag unreachable exported modules as dead code candidates
            for module in self.graph.modules:
                if module.exports and module.id not in reachable:
                    module.reachability_status = "unreachable"
                    if module.in_degree == 0:  # No incoming imports
                        module.is_dead_code_candidate = True
                        self.graph.dead_code_candidates.append(module.id)
    
    def run(self, include_tests: bool = False) -> CartographyGraph:
        """Execute full Surveyor analysis pipeline.
        
        Args:
            include_tests: Whether to analyze test files (default: False)
        
        Returns:
            CartographyGraph with modules, edges, and metadata
        """
        # Discover files to analyze
        files_to_analyze = []
        for ext in LANGUAGE_ROUTER.keys():
            pattern = f"**/*{ext}"
            for file_path in self.repo_path.glob(pattern):
                # Skip virtual envs, build dirs, tests (unless requested)
                if any(skip in str(file_path) for skip in [".venv", "venv", "node_modules", "__pycache__"]):
                    continue
                if not include_tests and "test" in file_path.name.lower():
                    continue
                files_to_analyze.append(file_path)
        
        # Analyze each module
        for file_path in files_to_analyze:
            node = self.analyze_module(file_path)
            if node:
                self.graph.add_node(node)
        
        # Build graph + compute metrics
        self._build_graph()
        
        # Update summary stats
        self.graph._update_stats()
        
        return self.graph
    
    def save_artifacts(self) -> Path:
        """Persist analysis results to .cartography/module_graph.json."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "module_graph.json"
        self.graph.to_file(output_path)
        return output_path