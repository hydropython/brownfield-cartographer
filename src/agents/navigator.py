import json
from pathlib import Path
import openai

class NavigatorAgent:
    def __init__(self, audit_dir: str = "refined_audit"):
        self.audit_dir = Path(audit_dir)
        self.codebase_path = self.audit_dir / "CODEBASE.md"
        self.lineage_path = self.audit_dir / "ui_lineage_graph.json"
        self.semantic_path = self.audit_dir / "ui_semantic_state.json"

    def find_implementation(self, concept: str):
        """Tool 1: Semantic Search"""
        if not self.codebase_path.exists():
            return "Error: CODEBASE.md not found. Run Agent 4 first."
        content = self.codebase_path.read_text()
        relevant = [line for line in content.split('\n') if concept.lower() in line.lower()]
        return "\n".join(relevant) if relevant else f"No mention of '{concept}' in codebase."

    def trace_lineage(self, dataset: str, direction: str = "upstream"):
        """Tool 2: Graph Lineage"""
        if not self.lineage_path.exists():
            return "Error: Lineage graph missing."
        with open(self.lineage_path) as f:
            data = json.load(f)
        target_id = dataset.upper()
        # Look inside the Cytoscape elements structure we built earlier
        edges = [e["data"] for e in data.get("elements", []) if "source" in e["data"]]
        
        if direction == "upstream":
            return [e["source"] for e in edges if e["target"] == target_id]
        return [e["target"] for e in edges if e["source"] == target_id]

    def explain_module(self, path: str):
        """Tool 3: Generative Explanation"""
        if not self.semantic_path.exists():
            return "Error: Run Semanticist Agent first."
        with open(self.semantic_path, 'r') as f:
            data = json.load(f)
        for mod in data:
            if path.lower() in mod.get('file_path', '').lower() or path.upper() in mod.get('id', ''):
                return {
                    "purpose": mod.get("purpose_statement"),
                    "details": mod.get("interesting_details")
                }
        return f"Unknown module: {path}"
    
    def query_with_context(self, user_query: str):
        # 1. Grab the "Perfect Codebase" [cite: 2026-03-03]
        if not self.codebase_path.exists():
            return "Error: No context available. Run analysis first."
        
        context = self.codebase_path.read_text()
        
        # 2. Add the Lineage Graph for structural awareness
        with open(self.lineage_path) as f:
            graph_context = f.read()

        # 3. Call GPT-mini with the "Safety Sandwich" logic
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Use this context to answer: {context}\n\nGraph: {graph_context}"},
                {"role": "user", "content": user_query}
            ]
        )
        
        return response.choices[0].message.content