"""
Tree-sitter Analyzer - Multi-language AST parsing

Uses tree-sitter to parse source files and extract structural elements
(imports, functions, classes) from the AST.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class LanguageRouter:
    """Selects correct grammar based on file extension."""
    
    EXTENSION_MAP = {
        ".py": "python",
        ".sql": "sql",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json"
    }
    
    @classmethod
    def get_language(cls, file_path: Path) -> Optional[str]:
        """Get language from file extension."""
        return cls.EXTENSION_MAP.get(file_path.suffix.lower())
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """Check if file type is supported."""
        return cls.get_language(file_path) is not None


class TreeSitterAnalyzer:
    """
    Multi-language AST parsing with tree-sitter.
    
    Extracts structural elements (imports, functions, classes) from AST.
    Falls back to regex-based extraction if tree-sitter unavailable.
    """
    
    def __init__(self):
        self.parsers = {}
        self.tree_sitter_available = self._init_tree_sitter()
    
    def _init_tree_sitter(self) -> bool:
        """Initialize tree-sitter parsers if available."""
        try:
            from tree_sitter import Parser, Language
            
            # Try to load Python grammar
            try:
                import tree_sitter_python
                self.python_parser = Parser()
                self.python_parser.set_language(tree_sitter_python.language())
                self.parsers["python"] = self.python_parser
                print("   tree-sitter-python loaded")
            except:
                print("   tree-sitter-python not available (using fallback)")
            
            # Try to load SQL grammar
            try:
                import tree_sitter_sql
                self.sql_parser = Parser()
                self.sql_parser.set_language(tree_sitter_sql.language())
                self.parsers["sql"] = self.sql_parser
                print("   tree-sitter-sql loaded")
            except:
                print("   tree-sitter-sql not available (using fallback)")
            
            return len(self.parsers) > 0
        except ImportError:
            print("   tree-sitter not installed (using fallback)")
            return False
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single file.
        
        Uses tree-sitter AST parsing if available, falls back to regex.
        """
        language = LanguageRouter.get_language(file_path)
        
        if not language:
            return {
                "file": str(file_path),
                "language": "unknown",
                "error": f"Unsupported language: {file_path.suffix}"
            }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Use tree-sitter if available for this language
            if self.tree_sitter_available and language in self.parsers:
                return self._parse_with_tree_sitter(file_path, content, language)
            else:
                # Fallback to regex-based extraction
                return self._parse_with_regex(file_path, content, language)
        
        except Exception as e:
            return {
                "file": str(file_path),
                "language": language,
                "error": str(e)
            }
    
    def _parse_with_tree_sitter(self, file_path: Path, content: str, language: str) -> Dict[str, Any]:
        """Parse file using tree-sitter AST."""
        parser = self.parsers.get(language)
        
        if not parser:
            return self._parse_with_regex(file_path, content, language)
        
        try:
            # Parse content
            tree = parser.parse(bytes(content, "utf8"))
            root = tree.root_node
            
            # Extract structural elements based on language
            if language == "python":
                imports = self._extract_python_imports_ast(root, content)
                functions = self._extract_python_functions_ast(root, content)
                classes = self._extract_python_classes_ast(root, content)
            elif language == "sql":
                imports = []  # SQL doesn't have imports
                functions = self._extract_sql_functions_ast(root, content)
                classes = []  # SQL doesn't have classes
            else:
                imports, functions, classes = [], [], []
            
            return {
                "file": str(file_path),
                "language": language,
                "lines": len(content.split("\n")),
                "imports": imports,
                "functions": functions,
                "classes": classes,
                "parse_method": "tree-sitter"
            }
        except Exception as e:
            # Fallback to regex on error
            return self._parse_with_regex(file_path, content, language)
    
    def _parse_with_regex(self, file_path: Path, content: str, language: str) -> Dict[str, Any]:
        """Fallback regex-based parsing."""
        imports = []
        functions = []
        classes = []
        
        if language == "python":
            imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)\s+import', content, re.MULTILINE)
            imports = [i[0] or i[1] for i in imports]
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        elif language == "sql":
            # Extract table references from FROM/JOIN clauses
            tables = re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', content, re.IGNORECASE)
            imports = [t[0] or t[1] for t in tables]
        
        return {
            "file": str(file_path),
            "language": language,
            "lines": len(content.split("\n")),
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "parse_method": "regex-fallback"
        }
    
    def _extract_python_imports_ast(self, root, content: str) -> List[str]:
        """Extract Python imports from AST."""
        imports = []
        
        def walk(node):
            if node.type == "import_statement":
                # import module
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(content[child.start_byte:child.end_byte])
            elif node.type == "import_from_statement":
                # from module import ...
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(content[child.start_byte:child.end_byte])
                        break
            else:
                for child in node.children:
                    walk(child)
        
        walk(root)
        return list(set(imports))
    
    def _extract_python_functions_ast(self, root, content: str) -> List[str]:
        """Extract Python function definitions from AST."""
        functions = []
        
        def walk(node):
            if node.type == "function_definition":
                for child in node.children:
                    if child.type == "identifier":
                        functions.append(content[child.start_byte:child.end_byte])
                        break
            else:
                for child in node.children:
                    walk(child)
        
        walk(root)
        return functions
    
    def _extract_python_classes_ast(self, root, content: str) -> List[str]:
        """Extract Python class definitions from AST."""
        classes = []
        
        def walk(node):
            if node.type == "class_definition":
                for child in node.children:
                    if child.type == "identifier":
                        classes.append(content[child.start_byte:child.end_byte])
                        break
            else:
                for child in node.children:
                    walk(child)
        
        walk(root)
        return classes
    
    def _extract_sql_functions_ast(self, root, content: str) -> List[str]:
        """Extract SQL function/procedure names from AST."""
        functions = []
        # SQL AST structure varies by dialect - basic extraction
        return functions
    
    def analyze_directory(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Analyze all supported files in directory."""
        results = []
        
        for ext in LanguageRouter.EXTENSION_MAP.keys():
            for file_path in repo_path.rglob(f"*{ext}"):
                if "node_modules" not in str(file_path) and ".git" not in str(file_path):
                    result = self.analyze_file(file_path)
                    results.append(result)
        
        return results
