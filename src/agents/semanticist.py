"""Semanticist Agent  Phase 3 of Brownfield Cartographer.

LLM-powered semantic understanding that static analysis cannot provide.

Core tasks:
1. ContextWindowBudget  tiered model selection (gemini-flash bulk, claude/gpt-4 synthesis)
2. generate_purpose_statement()  code-based purpose + docstring drift detection
3. cluster_into_domains()  k-means clustering  Domain Architecture Map
4. answer_day_one_questions()  Five FDE Questions with evidence citations

Cost discipline: cheap model for bulk, expensive for synthesis.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import re
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .context_budget import ContextWindowBudget


class SemanticistAgent:
    """LLM-powered semantic enrichment agent."""

    def __init__(
        self,
        repo_path: Path,
        output_dir: Path = Path(".cartography"),
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        max_budget_usd: float = 10.00,
        max_tokens: int = 500000,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir)
        self.budget = ContextWindowBudget(max_budget_usd=max_budget_usd, max_tokens=max_tokens)
        self._llm = None
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.purpose_statements: Dict[str, str] = {}
        self.doc_drift_flags: Dict[str, dict] = {}
        self.domain_clusters: List[dict] = []
        self.day_one_answers: Dict[str, str] = {}
        self.parse_warnings: List[str] = []

    def _get_llm(self):
        """Lazy-load LLM client."""
        if self._llm is None:
            try:
                from .llm_client import LLMClient
                self._llm = LLMClient(provider=self.llm_provider, api_key=self.llm_api_key, budget=self.budget)
            except ImportError:
                self._llm = _MockLLMClient(budget=self.budget)
        return self._llm

    def generate_purpose_statement(self, module_id: str, code_content: str, existing_docstring: Optional[str] = None) -> dict:
        """Generate purpose statement from CODE (not docstring) + detect drift."""
        llm = self._get_llm()
        model = self.budget.select_model("bulk")

        prompt = f"Analyze this code and write a 2-3 sentence purpose statement. Module: {module_id}. Focus on BUSINESS FUNCTION, not implementation. Code: {code_content[:4000]}"

        input_tokens = self.budget.estimate_tokens(prompt)
        output_tokens = 200

        if not self.budget.can_spend(input_tokens, output_tokens, model):
            return {"module_id": module_id, "purpose_statement": "[BUDGET_EXHAUSTED]", "drift_detected": None, "evidence": "Token budget exceeded"}

        try:
            purpose = llm.complete(prompt=prompt, system="You are a senior engineer. Be concise and business-focused.", max_tokens=output_tokens, temperature=0.3)
            self.budget.spend(input_tokens, output_tokens, model, task_type="bulk")

            result = {"module_id": module_id, "purpose_statement": purpose.strip(), "drift_detected": False, "drift_analysis": None, "evidence": f"Generated from code ({len(code_content)} chars)"}

            if existing_docstring:
                drift = self._check_doc_drift(module_id, code_content, existing_docstring, purpose)
                result["drift_detected"] = drift["drift_detected"]
                result["drift_analysis"] = drift["analysis"]

            self.purpose_statements[module_id] = result
            return result
        except Exception as e:
            self.parse_warnings.append(f"Purpose error for {module_id}: {e}")
            return {"module_id": module_id, "purpose_statement": f"[ERROR] {e}", "drift_detected": None, "evidence": str(e)}

    def _check_doc_drift(self, module_id: str, code_content: str, existing_docstring: str, generated_purpose: str) -> dict:
        """Check if existing docstring contradicts implementation."""
        llm = self._get_llm()
        model = self.budget.select_model("bulk")
        prompt = f"Compare docstring vs code for {module_id}. Docstring: {existing_docstring[:1000]}. Generated purpose: {generated_purpose}. Does docstring accurately reflect code? Answer MATCH or DRIFT with brief explanation."

        input_tokens = self.budget.estimate_tokens(prompt)
        output_tokens = 150

        try:
            analysis = llm.complete(prompt=prompt, system="You are a technical writer.", max_tokens=output_tokens, temperature=0.3)
            self.budget.spend(input_tokens, output_tokens, model, task_type="bulk")
            return {"drift_detected": "DRIFT" in analysis.upper()[:20], "analysis": analysis.strip()}
        except Exception as e:
            return {"drift_detected": None, "analysis": f"Error: {e}"}

    def cluster_into_domains(self, purpose_statements: Dict[str, str], n_clusters: int = 6) -> List[dict]:
        """Cluster modules by semantic domain using TF-IDF + k-means."""
        if not purpose_statements:
            return []

        module_ids = list(purpose_statements.keys())
        statements = [purpose_statements[m]["purpose_statement"] for m in module_ids]

        valid_pairs = [(mid, stmt) for mid, stmt in zip(module_ids, statements) if stmt and not str(stmt).startswith("[")]
        if len(valid_pairs) < n_clusters:
            return [{"domain": "uncategorized", "modules": [mid for mid, _ in valid_pairs]}]

        valid_ids, valid_stmts = zip(*valid_pairs)

        vectorizer = TfidfVectorizer(max_features=100, stop_words="english", ngram_range=(1, 2))
        X = vectorizer.fit_transform(valid_stmts)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)

        clusters: Dict[int, List[str]] = {}
        for mid, label in zip(valid_ids, cluster_labels):
            clusters.setdefault(label, []).append(mid)

        domain_clusters = []
        for cluster_id, members in clusters.items():
            path_prefixes = [m.split(".")[0] for m in members if "." in m]
            domain_name = max(set(path_prefixes), key=path_prefixes.count) if path_prefixes else f"domain_{cluster_id}"
            domain_clusters.append({"domain": domain_name, "cluster_id": int(cluster_id), "module_count": len(members), "modules": members})

        self.domain_clusters = domain_clusters
        return domain_clusters

    def answer_day_one_questions(self, surveyor_output: dict, hydrologist_output: dict, questions: Optional[List[str]] = None) -> Dict[str, str]:
        """Answer the Five FDE Day-One Questions with evidence citations."""
        if questions is None:
            questions = [
                "What does this codebase do at a high level?",
                "Where should I start if I need to make a small change?",
                "What are the most critical modules I must not break?",
                "How do I test my changes in this codebase?",
                "Who owns what, and how do I get help when stuck?",
            ]

        llm = self._get_llm()
        model = self.budget.select_model("synthesis")
        context = self._build_synthesis_context(surveyor_output, hydrologist_output)
        answers = {}

        for i, question in enumerate(questions, 1):
            prompt = f"Answer this FDE Day-One question with SPECIFIC EVIDENCE. Question: {question}. Context: {json.dumps(context)[:6000]}. Cite file paths and module names. Be concise but actionable."
            input_tokens = self.budget.estimate_tokens(prompt)
            output_tokens = 500

            if not self.budget.can_spend(input_tokens, output_tokens, model):
                answers[question] = "[BUDGET_EXHAUSTED]"
                continue

            try:
                answer = llm.complete(prompt=prompt, system="You are a senior engineer onboarding a new team member.", max_tokens=output_tokens, temperature=0.3)
                self.budget.spend(input_tokens, output_tokens, model, task_type="synthesis")
                answers[question] = answer.strip()
            except Exception as e:
                self.parse_warnings.append(f"Q&A error: {e}")
                answers[question] = f"[ERROR] {e}"

        self.day_one_answers = answers
        return answers

    def _build_synthesis_context(self, surveyor: dict, hydrologist: dict) -> dict:
        """Build condensed context for LLM synthesis."""
        return {
            "structure": {"total_modules": surveyor.get("total_nodes", 0), "total_dependencies": surveyor.get("total_edges", 0), "hubs": surveyor.get("architectural_hubs", [])[:5]},
            "lineage": {"sources": hydrologist.get("sources", [])[:5], "sinks": hydrologist.get("sinks", [])[:5]},
            "semantics": {"purposes": {k: v["purpose_statement"] for k, v in list(self.purpose_statements.items())[:10]}},
        }

    def save_artifacts(self) -> Path:
        """Save semantic enrichment to .cartography/semantic_enrichment.json."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "semantic_enrichment.json"
        data = {"purpose_statements": self.purpose_statements, "doc_drift_flags": self.doc_drift_flags, "domain_clusters": self.domain_clusters, "day_one_answers": self.day_one_answers, "budget_stats": self.budget.get_stats(), "parse_warnings": self.parse_warnings}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return output_path


class _MockLLMClient:
    """Mock LLM client for testing without API keys."""
    def __init__(self, budget: ContextWindowBudget):
        self.budget = budget
    def complete(self, prompt: str, **kwargs) -> str:
        self.budget.record_cache_miss()
        if "purpose" in prompt.lower():
            return "This module handles data transformation for the customer analytics pipeline."
        elif "drift" in prompt.lower():
            return "MATCH - docstring accurately reflects implementation"
        elif "question" in prompt.lower():
            return "Start with src/agents/ for core logic. Key modules: surveyor.py, hydrologist.py. Test via pytest in tests/."
        return "[Mock LLM response]"
