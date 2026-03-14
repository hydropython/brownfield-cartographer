"""Surveyor Agent  Phase 1: Deterministic Structural Extraction."""
import json
import re
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime

import networkx as nx
from tree_sitter import Language, Parser, Query, QueryCursor
from pydantic import ValidationError

import tree_sitter_python
import tree_sitter_sql
import tree_sitter_yaml

from ..models.nodes import ModuleNode, ConfidenceTier, EvidenceType, SymbolType
from ..models.edges import Edge, EdgeType
from ..models.graph import CartographyGraph
from ..analyzers.git_analyzer import GitVelocityAnalyzer

LANGUAGE_ROUTER: dict[str, dict] = {
    ".py": {"grammar": tree_sitter_python, "name": "python"},
    ".sql": {"grammar": tree_sitter_sql, "name": "sql"},
    ".yml": {"grammar": tree_sitter_yaml, "name": "yaml"},
    ".yaml": {"grammar": tree_sitter_yaml, "name": "yaml"},
}

EVIDENCE_TO_CONFIDENCE: dict[EvidenceType, ConfidenceTier] = {
    "static": 1.0, "algorithmic": 0.9, "inference": 0.6, "heuristic": 0.3,
}

class SurveyorAgent:
    def __init__(self, repo_path: Path, output_dir: Path = Path(".cartography"), days_lookback: int = 30):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir)
        self.git_analyzer = GitVelocityAnalyzer(self.repo_path, days_lookback)
        self.graph = CartographyGraph(repo_name=self.repo_path.name, repo_path=str(self.repo_path), base_commit_sha=self._get_current_commit())
        self.query_lib = Path(__file__).parent.parent / "analyzers" / "query_library"
        self._languages = {}
        self._parsers = {}
        for ext, config in LANGUAGE_ROUTER.items():
            try:
                self._languages[ext] = Language(config["grammar"].language())
                self._parsers[ext] = Parser(self._languages[ext])
            except Exception as e:
                self.graph.parse_warnings.append(f"Failed to load {config['name']} grammar: {e}")
    
    def _get_current_commit(self) -> str:
        import subprocess
        try:
            result = subprocess.run(["git", "-C", str(self.repo_path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=10)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _get_language(self, file_path: Path) -> Optional[str]:
        config = LANGUAGE_ROUTER.get(file_path.suffix.lower())
        return config["name"] if config else None
    
    def _get_parser_for_file(self, file_path: Path) -> Optional[Parser]:
        return self._parsers.get(file_path.suffix.lower())
    
    def _load_query(self, language: str, query_name: str) -> str:
        query_path = self.query_lib / language / f"{query_name}.scm"
        return query_path.read_text(encoding="utf-8") if query_path.exists() else ""
    
    def _resolve_import_path(self, import_path: str, current_file: Path, repo_root: Path) -> Optional[str]:
        if import_path.startswith(("pandas", "numpy", "sqlglot", "networkx", "torch", "tensorflow")):
            return None
        current_dir = current_file.parent
        parts = import_path.split(".")
        if import_path.startswith("."):
            dots = len(import_path) - len(import_path.lstrip("."))
            for _ in range(dots):
                current_dir = current_dir.parent
            parts = import_path.lstrip(".").split(".")
            if not parts or parts == [""]:
                parts = []
        for i in range(len(parts), 0, -1):
            candidate_parts = parts[:i]
            candidate_path = repo_root / Path(*candidate_parts)
            if (candidate_path.with_suffix(".py")).exists():
                return ".".join(candidate_parts)
            if (candidate_path / "__init__.py").exists():
                return ".".join(candidate_parts)
        return import_path if import_path else None
    
    def _extract_captures(self, query_text: str, lang, root_node, content: str, target_capture: str) -> list:
        results = []
        if not query_text or root_node.child_count == 0:
            return results
        try:
            query = Query(lang, query_text)
            cursor = QueryCursor(query)
            captures_dict = cursor.captures(root_node)
            if target_capture in captures_dict:
                for node in captures_dict[target_capture]:
                    results.append(content[node.start_byte:node.end_byte])
        except Exception:
            pass
        return results
    
    def analyze_module(self, file_path: Path) -> Optional[ModuleNode]:
        """
        Analyzes a single file using Tree-Sitter with regex fallbacks for Jinja/SQL.
        """
        language_name = self._get_language(file_path)
        if not language_name:
            return None
            
        parser = self._get_parser_for_file(file_path)
        if not parser:
            return None
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = parser.parse(bytes(content, "utf-8"))
            root_node = tree.root_node
            lang = self._languages[file_path.suffix.lower()]
            
            # 1. Extraction: Imports
            import_query_text = self._load_query(language_name, "imports")
            imports = self._extract_captures(import_query_text, lang, root_node, content, "import_path")
            
            # 2. Extraction: Public API/Symbols
            api_query_text = self._load_query(language_name, "public_api")
            exports = self._extract_captures(api_query_text, lang, root_node, content, "name")
            
            # 3. DBT-SPECIFIC FALLBACK: If SQL parser failed or returned empty
            # Tree-sitter-sql often fails on Jinja {{ ref() }}
            if language_name == "sql" or root_node.child_count == 0:
                # Extract dbt refs
                for match in re.finditer(r'\{\{\s*ref\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\}\}', content):
                    ref_name = match.group(1)
                    if ref_name not in imports:
                        imports.append(ref_name)
                
                # Extract dbt sources
                for match in re.finditer(r'\{\{\s*source\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\}\}', content):
                    source_name = f"{match.group(1)}.{match.group(2)}"
                    if source_name not in imports:
                        imports.append(source_name)

            # 4. Resolve paths for internal imports
            resolved_imports = []
            for imp in imports:
                resolved = self._resolve_import_path(imp, file_path, self.repo_path)
                if resolved:
                    resolved_imports.append(resolved)
            
            # 5. Metadata and Metrics
            rel_path = file_path.relative_to(self.repo_path)
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            comment_lines = sum(1 for l in lines if l.startswith(("#", "--", "//")))
            
            # Complexity calculation
            decision_keywords = {"if", "for", "while", "elif", "except", "case", "match"}
            complexity = sum(1 for line in content.split("\n") if any(kw in line for kw in decision_keywords))

            return ModuleNode(
                id=str(rel_path.with_suffix("")).replace("/", ".").replace("\\", "."),
                symbol_type="Module",
                file_path=str(rel_path),
                language=language_name,
                imports=resolved_imports,
                exports=exports,
                cyclomatic_complexity=complexity,
                comment_to_code_ratio=round(comment_lines / len(lines), 3) if lines else 0.0,
                lines_of_code=len(lines),
                git_sha=self._get_current_commit(),
                last_analyzed_commit=self._get_current_commit(),
                change_velocity_30d=self.git_analyzer.get_change_velocity(str(rel_path)),
                last_modified=self.git_analyzer.get_file_last_modified(str(rel_path)),
                confidence_score=EVIDENCE_TO_CONFIDENCE["static"],
                evidence_type="static",
                scope="module"
            )

        except Exception as e:
            rel_path = file_path.relative_to(self.repo_path) if file_path.is_relative_to(self.repo_path) else file_path
            self.graph.parse_warnings.append(f"Failed to parse {rel_path}: {str(e)}")
            self.graph.files_skipped.append(str(rel_path))
            return None
    
    def _add_ghost_nodes(self, imports: list[str], module_id: str) -> None:
        external_prefixes = ["pandas", "numpy", "sqlglot", "networkx", "torch", "tensorflow", "requests", "flask", "django"]
        for imp in imports:
            prefix = imp.split(".")[0]
            if prefix in external_prefixes:
                ghost_id = f"external.{imp}"
                if not any(n.id == ghost_id for n in self.graph.modules):
                    ghost = ModuleNode(id=ghost_id, symbol_type="GhostNode", is_ghost_node=True, external_package=prefix, confidence_score=1.0, evidence_type="static", scope="module")
                    self.graph.add_node(ghost)
                edge = Edge(source=module_id, target=ghost_id, edge_type="IMPORTS", confidence_score=1.0, evidence_type="static")
                self.graph.add_edge(edge)
    
    def _build_graph(self) -> None:
        nx_graph = nx.DiGraph()
        for module in self.graph.modules:
            nx_graph.add_node(module.id, **module.model_dump())
        for module in self.graph.modules:
            for imp in module.imports:
                target_exists = any(m.id == imp for m in self.graph.modules)
                target_id = imp if target_exists else f"external.{imp}"
                nx_graph.add_edge(module.id, target_id, edge_type="IMPORTS")
                edge = Edge(source=module.id, target=target_id, edge_type="IMPORTS", confidence_score=1.0, evidence_type="static")
                self.graph.add_edge(edge)
            self._add_ghost_nodes(module.imports, module.id)
        if nx_graph.number_of_nodes() > 0:
            try:
                pagerank = nx.pagerank(nx_graph, alpha=0.85, max_iter=100)
                hubs = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
                self.graph.architectural_hubs = [hub_id for hub_id, score in hubs if score > 0.001]
            except Exception as e:
                self.graph.parse_warnings.append(f"PageRank failed, using in-degree: {e}")
                in_degrees = {node: nx_graph.in_degree(node) for node in nx_graph.nodes()}
                hubs = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
                self.graph.architectural_hubs = [hub_id for hub_id, degree in hubs if degree > 0]
        sccs = list(nx.strongly_connected_components(nx_graph))
        circular_deps = [scc for scc in sccs if len(scc) > 1]
        if circular_deps:
            self.graph.parse_warnings.append(f"Detected {len(circular_deps)} circular dependency clusters: {[list(c) for c in circular_deps[:3]]}")
        entry_points = [m.id for m in self.graph.modules if m.entry_point_type is not None and m.entry_point_type != "none"]
        if entry_points:
            reachable = set()
            for ep in entry_points:
                reachable.update(nx.descendants(nx_graph, ep) | {ep})
            for module in self.graph.modules:
                if module.exports and module.id not in reachable:
                    module.reachability_status = "unreachable"
                    if module.in_degree == 0:
                        module.is_dead_code_candidate = True
                        self.graph.dead_code_candidates.append(module.id)
    
    def run(self, include_tests: bool = False) -> CartographyGraph:
        files_to_analyze = []
        # DEBUG: Check if the path even exists
        if not self.repo_path.exists():
            print(f"CRITICAL: Repo path does not exist: {self.repo_path}")
            return self.graph

        for ext in LANGUAGE_ROUTER.keys():
            # rglob is more robust for recursive discovery
            for file_path in self.repo_path.rglob(f"*{ext}"):
                if any(skip in str(file_path) for skip in [".venv", "venv", "node_modules", "__pycache__", ".git"]):
                    continue
                if not include_tests and "test" in file_path.name.lower():
                    continue
                files_to_analyze.append(file_path)
        
        # DEBUG: See how many files were actually found
        print(f"DEBUG: Surveyor found {len(files_to_analyze)} potential files in {self.repo_path}")
        
        if files_to_analyze:
            file_paths = [str(f.relative_to(self.repo_path)) for f in files_to_analyze]
            pareto_core = self.git_analyzer.get_pareto_core(file_paths, threshold=0.2)
            if pareto_core:
                self.graph.parse_warnings.append(f"High-velocity core (20/80): {len(pareto_core)} files  {pareto_core[:3]}")
        for file_path in files_to_analyze:
            node = self.analyze_module(file_path)
            if node:
                self.graph.add_node(node)
        self._build_graph()
        self.graph._update_stats()
        return self.graph
    
    def save_artifacts(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "module_graph.json"
        self.graph.to_file(output_path)
        return output_path
