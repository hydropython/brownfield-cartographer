"""
Python Data Flow Analyzer (Tree-Sitter Edition)
Goal: Build the data lineage layer for mixed Python/SQL/YAML codebases.
Target: Pandas, SQLAlchemy, and PySpark.
"""
import tree_sitter_python as tspy
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Dict, Any

class PythonDataFlowAnalyzer:
    """Extract data operations using AST traversal to ensure deterministic lineage."""

    def __init__(self):
        # Initialize Tree-Sitter for Python
        self.PY_LANGUAGE = Language(tspy.language())
        self.parser = Parser(self.PY_LANGUAGE)
        
        # S-Expression Query: Finds method calls like obj.method(args)
        # Specifically looks for the object, the method name, and the argument list
        self.lineage_query = self.PY_LANGUAGE.query("""
            (call
              function: (attribute
                object: (identifier) @obj_name
                attribute: (identifier) @method_name)
              arguments: (argument_list) @args)
        """)

    def _resolve_path(self, node) -> str:
        """
        Agent 2 Goal #1: Handle f-strings and variable references gracefully.
        Logs as 'dynamic reference, cannot resolve' for non-literal strings.
        """
        # Tree-sitter argument_list contains parentheses and comma-separated nodes
        # We look for the first significant argument (usually the path or query)
        for child in node.children:
            if child.type == 'string':
                # Extract literal string content, removing quotes
                return child.text.decode('utf-8').strip("'\"")
            
            if child.type in ['f_string', 'identifier', 'attribute', 'binary_operator']:
                return "dynamic reference, cannot resolve"
        
        return "unresolved_argument"

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses the Python file and extracts sources (reads) and sinks (writes).
        """
        result = {
            "file_path": str(file_path),
            "sources": [],
            "sinks": [],
            "dynamic_references": []
        }

        if not file_path.exists():
            return result

        try:
            content = file_path.read_bytes()
            tree = self.parser.parse(content)
            captures = self.lineage_query.captures(tree.root_node)
            
            # Map of methods to their functional roles in the lineage
            source_methods = {'read_csv', 'read_sql', 'read_parquet', 'execute', 'read', 'read_json'}
            sink_methods = {'to_csv', 'to_sql', 'to_parquet', 'write', 'save', 'to_json'}

            for node, tag in captures:
                # We process at the 'args' capture to ensure we have the full call context
                if tag == "args":
                    call_node = node.parent
                    func_node = call_node.child_by_field_name('function')
                    
                    obj_name = func_node.child_by_field_name('object').text.decode('utf-8')
                    method_name = func_node.child_by_field_name('attribute').text.decode('utf-8')
                    
                    # Resolve the data path or query string
                    data_identity = self._resolve_path(node)
                    line_number = node.start_point[0] + 1

                    operation = {
                        "library_object": obj_name,
                        "method": method_name,
                        "identity": data_identity,
                        "line": line_number,
                        "is_dynamic": data_identity == "dynamic reference, cannot resolve"
                    }

                    # Categorize into Lineage Graph Nodes
                    if method_name in source_methods:
                        result["sources"].append(operation)
                    elif method_name in sink_methods:
                        result["sinks"].append(operation)

                    if operation["is_dynamic"]:
                        result["dynamic_references"].append(operation)

        except Exception as e:
            # Fallback for parsing errors to keep the pipeline alive
            print(f"Error analyzing {file_path}: {e}")

        return result

    def export_refined_audit(self, file_path: Path, output_dir: Path):
        """
        Saves the analysis to the 'refined_audit' folder as per saved preferences.
        """
        import json
        analysis = self.analyze_file(file_path)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"audit_{file_path.stem}.json"
        
        with open(report_path, 'w') as f:
            json.dump(analysis, f, indent=4)
        
        return report_path