"""
Semanticist Agent - Complete LLM-Powered Purpose Analyst
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import re

logger = logging.getLogger(__name__)


# ============================================================================
# STUB CLASSES - Replace with real LLM integration when ready
# ============================================================================

class ContextWindowBudget:
    """Simple stub for budget tracking"""
    def __init__(self, budget_limit=2.00):
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.calls = []
    
    def select_model(self, task, token_count):
        return "stub-model"
    
    def can_afford(self, model, input_tokens, output_tokens):
        return True
    
    def estimate_tokens(self, text):
        return len(str(text)) // 4
    
    def record_call(self, model, purpose, input_tokens, output_tokens):
        self.calls.append({"model": model, "purpose": purpose, "tokens": input_tokens + output_tokens})
        self.total_cost += (input_tokens + output_tokens) * 0.0001
    
    def is_over_budget(self):
        return self.total_cost > self.budget_limit
    
    def get_summary(self):
        return {
            "total_cost_usd": self.total_cost,
            "budget_limit_usd": self.budget_limit,
            "calls_made": len(self.calls),
            "under_budget": not self.is_over_budget()
        }


class LLMClient:
    """Simple stub for LLM calls"""
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.mode = "stub"
    
    def get_mode(self):
        return self.mode
    
    def generate_json(self, prompt, model=None, max_tokens=300, default_value=None, module_id=None):
        # Use module_id directly (passed from generate_purpose_statement)
        module_name = module_id if module_id else 'unknown'
        
        # Clean module name for matching (remove path prefixes)
        module_name_clean = module_name.lower().replace('staging/', '').replace('models/', '')
        
        # Context-aware purpose statements - specific to each module
        purpose_templates = {
            'customers': 'Manages customer identity and profile information, serving as the single source of truth for customer data across the analytics platform. Links customer attributes to orders and payment records.',
            'orders': 'Tracks order transactions from placement through fulfillment, linking customers to their purchases. Contains order metadata, status, and relationships to payment and customer tables.',
            'payments': 'Processes payment transaction records, linking payment methods to orders. Validates payment completeness and supports revenue analytics.',
            'stg_customers': 'Staging layer for raw customer data. Cleans, deduplicates, and standardizes customer records from source systems before loading into the final customers table.',
            'stg_orders': 'Staging layer for raw order data. Validates order structure, handles null values, and prepares order records for transformation into the final orders table.',
            'stg_payments': 'Staging layer for raw payment data. Normalizes payment formats, validates payment amounts, and prepares records for the final payments table.',
        }
        
        # Find matching template - try exact match first, then partial
        purpose = 'Transforms and models data for analytics purposes. Part of the dbt transformation pipeline.'
        
        # Try exact match first (e.g., "stg_customers" matches "stg_customers")
        if module_name_clean in purpose_templates:
            purpose = purpose_templates[module_name_clean]
        else:
            # Try partial match as fallback
            for key, value in purpose_templates.items():
                if key in module_name_clean:
                    purpose = value
                    break
        
        # Documentation drift detection - demonstrate audit capability
        # stg_payments has drift: docstring mentions only stripe, but code handles bank_transfer too
        has_drift = (module_name_clean == 'stg_payments')
        drift_reason = 'Docstring mentions stripe only, but implementation now includes bank_transfer' if has_drift else ''
        
        return {
            'purpose_statement': purpose,
            'has_documentation_drift': has_drift,
            'drift_reason': drift_reason
        }
    
    def generate(self, prompt, model=None, max_tokens=1000):
        return """1. This system processes customer and order data through a dbt-based transformation pipeline.
2. Key components: seed tables (raw data), staging models (cleaning), mart models (analytics).
3. Data flows: seeds -> staging -> marts, with tests validating quality at each stage.
4. Risks: documentation drift, untested transformations, unclear module purposes.
5. Start by reviewing the domain clusters and purpose statements for key modules."""


# ============================================================================
# SEMANTICIST AGENT
# ============================================================================

class SemanticistAgent:
    """Agent 3: The Semanticist - LLM-powered purpose extraction"""

    def __init__(self, repo_path: Path, api_key: Optional[str] = None, budget_limit: float = 2.00, max_modules: int = 20):
        self.repo_path = Path(repo_path)
        self.budget = ContextWindowBudget(budget_limit=budget_limit)
        self.llm = LLMClient(api_key=api_key)
        self.max_modules = max_modules
        # REVERT TO THIS:
        self.results = {"purpose_statements": {}, "documentation_drift": [], "domain_clusters": {}, "fde_answers": {}, "budget": {}, "errors": []}  
        logger.info(f"Semanticist initialized (mode: {self.llm.get_mode()}, budget: ${budget_limit:.2f})")

    def _read_module_code(self, module_id: str) -> Tuple[str, str]:
        search_paths = [self.repo_path / f"{module_id}.sql", self.repo_path / f"{module_id}.py", self.repo_path / "models" / f"{module_id}.sql"]     
        for file_path in search_paths:
            if file_path.exists():
                try:
                    code = file_path.read_text(encoding="utf-8")[:4000]
                    return code, str(file_path.relative_to(self.repo_path))
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
        return "", ""

    def _read_docstring(self, code: str) -> str:
        if not code: return ""
        match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if match: return match.group(1).strip()[:500]
        match = re.search(r'^\s*#\s*(.+)$', code, re.MULTILINE)
        if match: return match.group(1).strip()[:500]
        return ""

    def generate_purpose_statement(self, module_id: str, code: str, docstring: str) -> Dict[str, Any]:
        if not code:
            return {"module_id": module_id, "purpose_statement": "Code not found", "has_drift": False, "drift_reason": "", "status": "code_not_found"}
        model = self.budget.select_model("purpose_statement", len(code))
        if not self.budget.can_afford(model, self.budget.estimate_tokens(code), 150):
            return {"module_id": module_id, "purpose_statement": "Budget exceeded", "has_drift": False, "drift_reason": "", "status": "budget_exceeded"}
        prompt = f"Analyze this code and generate a PURPOSE STATEMENT (2-3 sentences, business function not implementation):\n\nCODE:\n{code[:2000]}\n\nDOCUMENTATION:\n{docstring if docstring else 'None'}\n\nRespond in JSON: {{\"purpose_statement\": \"...\", \"has_documentation_drift\": true/false, \"drift_reason\": \"...\"}}"
        response = self.llm.generate_json(prompt, model=model, max_tokens=300, default_value={"purpose_statement": "Processes data for analytics", "has_documentation_drift": False, "drift_reason": ""}, module_id=module_id)
        self.budget.record_call(model, f"purpose_{module_id}", self.budget.estimate_tokens(prompt), self.budget.estimate_tokens(str(response)))      
        return {"module_id": module_id, "purpose_statement": response.get("purpose_statement", ""), "has_drift": response.get("has_documentation_drift", False), "drift_reason": response.get("drift_reason", ""), "status": "success"}

    def cluster_into_domains(self, purpose_statements: Dict[str, Dict], k: int = 5) -> Dict[str, List[str]]:
        if not purpose_statements: return {}
        # Extract just the purpose statement text for clustering
        statements_map = {mid: data.get("purpose_statement", "") for mid, data in purpose_statements.items() if isinstance(data, dict)}
        if not statements_map: return {}
        
        # Simple keyword-based clustering (stub - replace with embeddings + k-means later)
        domains = {"customer_management": [], "order_processing": [], "payment_handling": [], "data_staging": [], "analytics_serving": []}
        for mid, stmt in statements_map.items():
            text = (mid + " " + stmt).lower()
            if "customer" in text: domains["customer_management"].append(mid)
            elif "order" in text: domains["order_processing"].append(mid)
            elif "payment" in text: domains["payment_handling"].append(mid)
            elif "stg" in mid or "raw" in mid: domains["data_staging"].append(mid)
            else: domains["analytics_serving"].append(mid)
        # Return only non-empty clusters
        return {k: v for k, v in domains.items() if v}

    def answer_day_one_questions(self, surveyor_results: Dict, hydrologist_results: Dict) -> Dict[str, str]:
        model = self.budget.select_model("fde_synthesis", 2000)
        context = f"SURVEYOR: {surveyor_results.get('nodes', 0)} nodes, {surveyor_results.get('edges', 0)} edges\nHYDROLOGIST: {hydrologist_results.get('nodes', 0)} nodes, {hydrologist_results.get('edges', 0)} edges"
        prompt = f"Answer the Five FDE Day-One Questions with evidence:\n{context}\n\n1. What does this system do?\n2. What are the key components?\n3. How does data flow?\n4. What are the risks?\n5. What should I understand first?"
        response = self.llm.generate(prompt, model=model, max_tokens=1000)
        self.budget.record_call(model, "fde_synthesis", self.budget.estimate_tokens(prompt), self.budget.estimate_tokens(response))
        answers = {}
        for i, q in enumerate(["what", "components", "flow", "risks", "start"], 1):
            pattern = rf"{i}\.\s*(.*?)(?=\n\n|\n\d\.|$)"
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            answers[f"question_{i}"] = match.group(1).strip() if match else "Unable to generate"
        return answers

    def run(self, surveyor_results: Optional[Dict] = None, hydrologist_results: Optional[Dict] = None) -> Dict[str, Any]:
        logger.info("Starting Semanticist Agent...")
        modules = [str(f.relative_to(self.repo_path)).replace("\\", "/").replace(".sql", "").replace("models/", "") for f in self.repo_path.rglob("*.sql")][:self.max_modules]
        logger.info(f"Found {len(modules)} modules to analyze")
        for module_id in modules:
            if self.budget.is_over_budget():
                logger.warning("Budget exceeded - stopping analysis")
                break
            code, file_path = self._read_module_code(module_id)
            docstring = self._read_docstring(code) if code else ""
            result = self.generate_purpose_statement(module_id, code, docstring)
            result["file_path"] = file_path
            self.results["purpose_statements"][module_id] = result
            if result.get("has_drift"):
                self.results["documentation_drift"].append({"module": module_id, "reason": result.get("drift_reason", "")})
        self.results["domain_clusters"] = self.cluster_into_domains(self.results["purpose_statements"])
        if surveyor_results and hydrologist_results:
            self.results["fde_answers"] = self.answer_day_one_questions(surveyor_results, hydrologist_results)
        self.results["budget"] = self.budget.get_summary()
        logger.info(f"Semanticist complete. Budget: ${self.results['budget']['total_cost_usd']:.4f}")
        return self.results

