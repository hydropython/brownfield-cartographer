"""Test tree-sitter and sqlglot integration"""

from pathlib import Path
from src.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer
from src.analyzers.sql_lineage import SQLLineageAnalyzer

print("=" * 60)
print("TESTING PARSING INFRASTRUCTURE")
print("=" * 60)

print("\n=== TREE-SITTER ===")
ts = TreeSitterAnalyzer()
results = ts.analyze_directory(Path("targets/jaffle_shop"))
print(f"Files analyzed: {len(results)}")
for r in results[:3]:
    fname = r.get("file", "unknown")
    lang = r.get("language", "?")
    method = r.get("parse_method", "?")
    print(f"  {fname}: {lang} - {method}")

print("\n=== SQLGLOT ===")
sql = SQLLineageAnalyzer()
results = sql.analyze_directory(Path("targets/jaffle_shop"))
print(f"SQL files analyzed: {len(results)}")
for r in results[:3]:
    fname = r.get("file", "unknown")
    deps = len(r.get("dependencies", []))
    method = r.get("parse_method", "?")
    print(f"  {fname}: {deps} dependencies - {method}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
