"""Tree-Sitter Multi-Language AST Analyzer.

Uses LanguageRouter to select correct grammar per file extension.
Supports Python, SQL, YAML, JavaScript/TypeScript.
"""
from pathlib import Path
from typing import Optional

from tree_sitter import Language, Parser, Query, QueryCursor

# Import individual grammar packages (production-grade, maintained)
import tree_sitter_python
import tree_sitter_sql
import tree_sitter_yaml
# import tree_sitter_javascript  # Optional: add as needed
# import tree_sitter_typescript  # Optional: add as needed


class LanguageRouter:
    """Maps file extensions to tree-sitter grammar configurations."""
    
    ROUTER: dict[str, dict] = {
        ".py": {"grammar": tree_sitter_python, "name": "python"},
        ".sql": {"grammar": tree_sitter_sql, "name": "sql"},
        ".yml": {"grammar": tree_sitter_yaml, "name": "yaml"},
        ".yaml": {"grammar": tree_sitter_yaml, "name": "yaml"},
        # ".js": {"grammar": tree_sitter_javascript, "name": "javascript"},
        # ".ts": {"grammar": tree_sitter_typescript, "name": "typescript"},
    }
    
    @classmethod
    def get_language(cls, file_path: Path) -> Optional[str]:
        """Return language name for file extension, or None if unsupported."""
        config = cls.ROUTER.get(file_path.suffix.lower())
        return config["name"] if config else None
    
    @classmethod
    def get_grammar(cls, file_path: Path):
        """Return tree-sitter grammar module for file extension."""
        config = cls.ROUTER.get(file_path.suffix.lower())
        return config["grammar"] if config else None
    
    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Return list of supported file extensions."""
        return list(cls.ROUTER.keys())


class TreeSitterAnalyzer:
    """Multi-language AST parser with QueryCursor API (tree-sitter 0.22+)."""
    
    def __init__(self):
        self._languages = {}
        self._parsers = {}
        
        # Pre-load languages and parsers for performance
        for ext, config in LanguageRouter.ROUTER.items():
            try:
                grammar = config["grammar"]
                lang_name = config["name"]
                self._languages[ext] = Language(grammar.language())
                self._parsers[ext] = Parser(self._languages[ext])
            except Exception as e:
                # Graceful degradation: skip unsupported grammars
                pass
    
    def parse_file(self, file_path: Path, content: Optional[str] = None) -> Optional[dict]:
        """Parse a file and return AST root node + metadata."""
        ext = file_path.suffix.lower()
        if ext not in self._parsers:
            return None
        
        if content is None:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        
        parser = self._parsers[ext]
        tree = parser.parse(bytes(content, "utf-8"))
        
        return {
            "root_node": tree.root_node,
            "content": content,
            "language": LanguageRouter.get_language(file_path),
            "file_path": str(file_path),
        }
    
    def query_captures(self, file_path: Path, query_text: str, target_capture: str) -> list[str]:
        """Execute a tree-sitter query and return captured text values.
        
        Uses cursor.captures() API (tree-sitter 0.22+).
        """
        ext = file_path.suffix.lower()
        if ext not in self._languages or not query_text:
            return []
        
        result = self.parse_file(file_path)
        if not result:
            return []
        
        try:
            lang = self._languages[ext]
            query = Query(lang, query_text)
            cursor = QueryCursor(query)
            captures_dict = cursor.captures(result["root_node"])
            
            if target_capture not in captures_dict:
                return []
            
            return [
                result["content"][node.start_byte:node.end_byte]
                for node in captures_dict[target_capture]
            ]
        except Exception:
            # Graceful degradation: return empty on query errors
            return []
