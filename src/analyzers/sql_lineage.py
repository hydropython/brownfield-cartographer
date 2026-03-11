"""
SQL Lineage Analyzer - sqlglot AST-based extraction

Extracts table-level dependencies from SQL using proper AST parsing.
Supports SELECT, FROM, JOIN, WITH (CTE) clauses.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)

class SQLLineageAnalyzer:
    """
    SQL dependency extraction using sqlglot AST.
    
    Parses SQL and extracts:
    - Table references (FROM, JOIN)
    - CTE definitions (WITH clauses)
    - Column-level lineage
    - dbt ref() and source() calls
    """
    
    def __init__(self, dialect: str = "postgres"):
        self.dialect = dialect
        self.sqlglot_available = self._init_sqlglot()
    
    def _init_sqlglot(self) -> bool:
        """Initialize sqlglot if available."""
        try:
            import sqlglot
            from sqlglot import exp
            logger.info("   sqlglot loaded for AST parsing")
            return True
        except ImportError:
            logger.warning("   sqlglot not installed (using regex fallback)")
            return False
    
    def extract_dependencies(self, sql_file: Path) -> Dict[str, Any]:
        """
        Extract dependencies from SQL file using AST.
        
        Args:
            sql_file: Path to SQL file
        
        Returns:
            Dictionary with tables, CTEs, columns, and dependencies
        """
        try:
            with open(sql_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract dbt macros first
            dbt_refs = self._extract_dbt_refs(content)
            dbt_sources = self._extract_dbt_sources(content)
            
            # Use sqlglot AST parsing
            if self.sqlglot_available:
                return self._parse_with_sqlglot_ast(sql_file, content, dbt_refs, dbt_sources)
            else:
                return self._parse_with_regex(sql_file, content, dbt_refs, dbt_sources)
        
        except Exception as e:
            logger.warning(f"Failed to parse {sql_file}: {e}")
            return {
                "file": str(sql_file),
                "error": str(e),
                "tables": [],
                "ctes": [],
                "dependencies": [],
                "recoverable": True
            }
    
    def _parse_with_sqlglot_ast(self, sql_file: Path, content: str, dbt_refs: List[str], dbt_sources: List[str]) -> Dict[str, Any]:
        """Parse SQL using sqlglot AST - REAL AST PARSING."""
        import sqlglot
        from sqlglot import exp
        
        try:
            # Remove dbt macros for clean SQL parsing
            clean_sql = self._remove_dbt_macros(content)
            
            # Parse SQL with AST
            parsed = sqlglot.parse_one(clean_sql, dialect=self.dialect)
            
            # Extract tables from FROM clause (AST-based)
            tables: Set[str] = set()
            for table in parsed.find_all(exp.Table):
                if table.name:
                    tables.add(table.name)
            
            # Extract tables from JOIN clause (AST-based)
            for join in parsed.find_all(exp.Join):
                if join.this and isinstance(join.this, exp.Table):
                    if join.this.name:
                        tables.add(join.this.name)
            
            # Extract CTEs from WITH clause (AST-based)
            ctes: Set[str] = set()
            for cte in parsed.find_all(exp.CTE):
                if cte.alias:
                    ctes.add(cte.alias)
            
            # Extract columns for column-level lineage (AST-based)
            columns: Set[str] = set()
            for col in parsed.find_all(exp.Column):
                columns.add(str(col))
            
            # Combine all dependencies
            all_deps = list(tables) + dbt_refs + dbt_sources
            
            logger.info(f"  Parsed {sql_file.name}: {len(tables)} tables, {len(ctes)} CTEs via sqlglot AST")
            
            return {
                "file": str(sql_file),
                "tables": list(tables),
                "ctes": list(ctes),
                "columns": list(columns),
                "dbt_refs": dbt_refs,
                "dbt_sources": dbt_sources,
                "dependencies": all_deps,
                "parse_method": "sqlglot-ast"
            }
        
        except Exception as e:
            logger.warning(f"sqlglot AST parse failed for {sql_file}: {e}")
            return self._parse_with_regex(sql_file, content, dbt_refs, dbt_sources)
    
    def _parse_with_regex(self, sql_file: Path, content: str, dbt_refs: List[str], dbt_sources: List[str]) -> Dict[str, Any]:
        """Fallback regex-based SQL parsing."""
        import re
        
        tables = re.findall(r'FROM\s+["\']?(\w+)["\']?', content, re.IGNORECASE)
        joins = re.findall(r'JOIN\s+["\']?(\w+)["\']?', content, re.IGNORECASE)
        ctes = re.findall(r'WITH\s+(\w+)\s+AS', content, re.IGNORECASE)
        
        all_tables = list(set(tables + joins))
        all_deps = all_tables + dbt_refs + dbt_sources
        
        return {
            "file": str(sql_file),
            "tables": all_tables,
            "ctes": ctes,
            "columns": [],
            "dbt_refs": dbt_refs,
            "dbt_sources": dbt_sources,
            "dependencies": all_deps,
            "parse_method": "regex-fallback"
        }
    
    def _extract_dbt_refs(self, content: str) -> List[str]:
        """Extract dbt ref() calls."""
        import re
        refs = re.findall(r'\{\{\s*ref\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\}\}', content)
        return [f"models.{ref.replace('/', '.')}" for ref in refs]
    
    def _extract_dbt_sources(self, content: str) -> List[str]:
        """Extract dbt source() calls."""
        import re
        sources = re.findall(r'\{\{\s*source\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\}\}', content)
        return [f"seeds.{s[0]}_{s[1]}" for s in sources]
    
    def _remove_dbt_macros(self, content: str) -> str:
        """Remove dbt Jinja macros for clean SQL parsing."""
        import re
        clean = re.sub(r'\{\{\s*ref\s*\([^}]+\)\s*\}\}', 'SELECT 1', content)
        clean = re.sub(r'\{\{\s*source\s*\([^}]+\)\s*\}\}', 'SELECT 1', clean)
        return clean
    
    def analyze_directory(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Analyze all SQL files in directory with progress reporting."""
        from tqdm import tqdm
        
        sql_files = list(repo_path.rglob("*.sql"))
        results = []
        
        logger.info(f"Analyzing {len(sql_files)} SQL files...")
        
        for sql_file in tqdm(sql_files, desc="SQL files"):
            if "node_modules" not in str(sql_file) and ".git" not in str(sql_file):
                result = self.extract_dependencies(sql_file)
                results.append(result)
        
        return results
