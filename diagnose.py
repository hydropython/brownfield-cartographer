#!/usr/bin/env python3
"""Minimal diagnostic for Surveyor data flow."""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path.cwd()))

print("=" * 70)
print("BROWNFIELD CARTOGRAPHER  DIAGNOSTIC")
print("=" * 70)

# 1. Test Surveyor Agent Directly
print("\n[1/4] Testing Surveyor Agent...")
try:
    from src.agents.surveyor import SurveyorAgent
    s = SurveyorAgent(repo_path=Path("targets/jaffle_shop"))
    g = s.run()
    
    print(f"   Modules: {len(g.modules)}")
    print(f"   Edges: {len(g.edges)}")
    
    print("\n  Module IDs:")
    for m in g.modules:
        print(f"     {m.id}")
    
    print("\n  Edge details:")
    for e in g.edges:
        print(f"     {e.source} --[{e.edge_type}]--> {e.target}")
        
except Exception as ex:
    print(f"   ERROR: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Test Backend Endpoint Logic
print("\n[2/4] Testing Backend Data Extraction...")
try:
    elements = []
    node_ids = set()
    
    # Add nodes
    for module in g.modules:
        mid = getattr(module, "id", "unknown")
        fp = getattr(module, "file_path", "")
        is_ghost = getattr(module, "is_ghost_node", False)
        
        if is_ghost or mid.startswith("external."):
            ntype = "external"
        elif fp.endswith(".sql"):
            ntype = "module"
        elif fp.endswith(".yml") or fp.endswith(".yaml"):
            ntype = "yaml"
        else:
            ntype = "other"
        
        elements.append({"data": {"id": mid, "label": mid.split(".")[-1], "type": ntype}})
        node_ids.add(mid)
    
    # Add edges
    edge_count = 0
    for edge in g.edges:
        src = getattr(edge, "source", "")
        tgt = getattr(edge, "target", "")
        if src in node_ids and tgt in node_ids:
            elements.append({"data": {"source": src, "target": tgt, "label": "IMPORTS"}})
            edge_count += 1
        else:
            print(f"     SKIP edge: {src} --> {tgt} (node not found)")
    
    print(f"   Elements built: {len(elements)} total")
    print(f"   Nodes: {len([e for e in elements if 'source' not in e['data']])}")
    print(f"   Edges: {edge_count}")
    
except Exception as ex:
    print(f"   ERROR: {ex}")
    import traceback
    traceback.print_exc()

# 3. Test API Response Format
print("\n[3/4] Testing API Response Format...")
try:
    import json
    response = {"elements": elements}
    json_str = json.dumps(response, indent=2)
    
    # Show first 500 chars
    print(f"   Valid JSON: {len(json_str)} bytes")
    print(f"  Preview: {json_str[:500]}...")
    
except Exception as ex:
    print(f"   ERROR: {ex}")

# 4. Summary
print("\n[4/4] Summary")
print("-" * 70)
print(f"  Surveyor modules: {len(g.modules)}")
print(f"  Surveyor edges:   {len(g.edges)}")
print(f"  Elements for Cytoscape: {len(elements)}")
print(f"  Edges that will render: {edge_count}")
print("-" * 70)

if edge_count == 0:
    print("\n WARNING: 0 edges will render!")
    print("  Possible causes:")
    print("  1. Edge source/target don't match any node id")
    print("  2. Node ids have different format than edge references")
    print("\n  Debug: Check if edge targets exist in node_ids set")
    for e in g.edges:
        src = getattr(e, "source", "")
        tgt = getattr(e, "target", "")
        src_ok = "" if src in node_ids else ""
        tgt_ok = "" if tgt in node_ids else ""
        print(f"    {src_ok} {src} --> {tgt_ok} {tgt}")
else:
    print("\n Edges should render correctly in frontend")

print("\n" + "=" * 70)
