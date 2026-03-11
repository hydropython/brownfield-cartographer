"""
Test Script - Verify All Required Files for Thursday Submission
"""

from pathlib import Path
import sys
import json

print("=" * 70)
print("BROWNFIELD CARTOGRAPHER - THURSDAY SUBMISSION REQUIREMENTS CHECK")
print("=" * 70)
print()

# Track results
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def check_file(path, description):
    """Check if file exists."""
    if Path(path).exists():
        results["passed"].append(f" {path} - {description}")
        return True
    else:
        results["failed"].append(f" {path} - {description} - MISSING")
        return False

def check_import(module, description):
    """Check if module can be imported."""
    try:
        __import__(module)
        results["passed"].append(f" {module} - {description}")
        return True
    except Exception as e:
        results["failed"].append(f" {module} - {description} - {str(e)}")
        return False

def check_artifact(path, expected_keys):
    """Check if artifact has required keys."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        missing = [k for k in expected_keys if k not in data]
        if not missing:
            results["passed"].append(f" {path} - All required keys present")
            return True
        else:
            results["warnings"].append(f" {path} - Missing keys: {missing}")
            return False
    except Exception as e:
        results["failed"].append(f" {path} - {str(e)}")
        return False

# ============================================================================
# 1. CHECK REQUIRED FILES
# ============================================================================
print("1. CHECKING REQUIRED FILES")
print("-" * 70)

check_file("src/cli.py", "Entry point")
check_file("src/orchestrator.py", "Agent wiring")
check_file("src/models/__init__.py", "Pydantic schemas")
check_file("src/models/nodes.py", "Node types")
check_file("src/models/edges.py", "Edge types")
check_file("src/analyzers/tree_sitter_analyzer.py", "AST parsing")
check_file("src/analyzers/sql_lineage.py", "SQL extraction")
check_file("src/analyzers/dag_config_parser.py", "YAML parsing")
check_file("src/agents/surveyor.py", "Surveyor agent")
check_file("src/agents/hydrologist.py", "Hydrologist agent")
check_file("src/graph/knowledge_graph.py", "NetworkX wrapper")
check_file("pyproject.toml", "Dependencies")
check_file("README.md", "Documentation")
check_file(".cartography/module_graph.json", "Module graph artifact")
check_file(".cartography/lineage_graph.json", "Lineage graph artifact")

print()

# ============================================================================
# 2. CHECK IMPORTS
# ============================================================================
print("2. CHECKING IMPORTS")
print("-" * 70)

check_import("src.models.nodes", "Node schemas")
check_import("src.models.edges", "Edge schemas")
check_import("src.agents.surveyor", "Surveyor agent")
check_import("src.agents.hydrologist", "Hydrologist agent")

print()

# ============================================================================
# 3. TEST AGENTS
# ============================================================================
print("3. TESTING AGENTS")
print("-" * 70)

try:
    from pathlib import Path
    from src.agents.surveyor import SurveyorAgent
    
    s = SurveyorAgent(repo_path=Path("targets/jaffle_shop"))
    g = s.run()
    
    if len(g.modules) > 0:
        results["passed"].append(f" Surveyor Agent - {len(g.modules)} modules, {len(g.edges)} edges")
    else:
        results["warnings"].append(" Surveyor Agent - No modules found")
except Exception as e:
    results["failed"].append(f" Surveyor Agent - {str(e)}")

try:
    from src.agents.hydrologist import HydrologistAgent
    
    h = HydrologistAgent(repo_path=Path("targets/jaffle_shop"))
    h.run()
    edges = getattr(h, "lineage_edges", [])
    
    if len(edges) > 0:
        results["passed"].append(f" Hydrologist Agent - {len(edges)} lineage edges")
    else:
        results["warnings"].append(" Hydrologist Agent - No edges found")
except Exception as e:
    results["failed"].append(f" Hydrologist Agent - {str(e)}")

print()

# ============================================================================
# 4. CHECK SCHEMA COMPLIANCE
# ============================================================================
print("4. CHECKING SCHEMA COMPLIANCE")
print("-" * 70)

try:
    from src.models.nodes import ModuleNode, DatasetNode, TransformationNode, FunctionNode
    from src.models.edges import Edge, EdgeType
    
    # Check ModuleNode fields
    m = ModuleNode(id="test", path="test.sql", language="sql")
    required_fields = ["path", "language", "purpose_statement", "domain_cluster", 
                       "complexity_score", "change_velocity_30d", "is_dead_code_candidate", "last_modified"]
    missing = [f for f in required_fields if not hasattr(m, f)]
    if not missing:
        results["passed"].append(" ModuleNode - All 8 required fields")
    else:
        results["failed"].append(f" ModuleNode - Missing: {missing}")
    
    # Check DatasetNode fields
    d = DatasetNode(id="test", name="test_table")
    required_fields = ["name", "storage_type", "schema_snapshot", "freshness_sla", "owner", "is_source_of_truth"]
    missing = [f for f in required_fields if not hasattr(d, f)]
    if not missing:
        results["passed"].append(" DatasetNode - All 6 required fields")
    else:
        results["failed"].append(f" DatasetNode - Missing: {missing}")
    
    # Check EdgeType
    required_edges = ["IMPORTS", "PRODUCES", "CONSUMES", "CALLS", "CONFIGURES", 
                      "DBT_REF", "DEPENDS_ON", "TESTS", "RELATIONSHIP"]
    actual = [e.value for e in EdgeType]
    missing = [e for e in required_edges if e not in actual]
    if not missing:
        results["passed"].append(" EdgeType - All 9 required types")
    else:
        results["failed"].append(f" EdgeType - Missing: {missing}")
        
except Exception as e:
    results["failed"].append(f" Schema Check - {str(e)}")

print()

# ============================================================================
# 5. CHECK ARTIFACTS
# ============================================================================
print("5. CHECKING ARTIFACTS")
print("-" * 70)

check_artifact(".cartography/module_graph.json", ["nodes", "edges"])
check_artifact(".cartography/lineage_graph.json", ["nodes", "edges"])

print()

# ============================================================================
# 6. SUMMARY
# ============================================================================
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"PASSED:   {len(results['passed'])}")
print(f"WARNINGS: {len(results['warnings'])}")
print(f"FAILED:   {len(results['failed'])}")
print()

if results["passed"]:
    print("PASSED:")
    for item in results["passed"]:
        print(f"  {item}")

if results["warnings"]:
    print("\nWARNINGS:")
    for item in results["warnings"]:
        print(f"  {item}")

if results["failed"]:
    print("\nFAILED (MUST FIX):")
    for item in results["failed"]:
        print(f"  {item}")

print()
print("=" * 70)

if len(results["failed"]) == 0:
    print(" ALL REQUIREMENTS MET - READY FOR THURSDAY SUBMISSION")
    sys.exit(0)
else:
    print(f" {len(results['failed'])} REQUIREMENTS FAILED - FIX BEFORE SUBMISSION")
    sys.exit(1)
