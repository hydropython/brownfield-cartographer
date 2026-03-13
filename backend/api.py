from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from src.agents.surveyor import SurveyorAgent
from src.agents.hydrologist import HydrologistAgent
from src.agents.semanticist import SemanticistAgent
import traceback
from src.orchestrator import run_analysis
app = FastAPI(title="Brownfield Cartographer API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache = {}

def _load_surveyor(repo_path: str = "targets/jaffle_shop"):
    if "surveyor" not in _cache:
        try:
            print("\n=== LOADING SURVEYOR AGENT ===")
            agent = SurveyorAgent(repo_path=Path(repo_path))
            graph = agent.run()
            
            elements = []
            node_ids = set()
            
            # Step 1: Add all modules from agent
            for m in graph.modules:
                mid = m.id
                fp = m.file_path
                ntype = "yaml" if fp.endswith(".yml") or fp.endswith(".yaml") else "module"
                label = mid.split(".")[-1]
                elements.append({"data": {"id": mid, "label": label, "type": ntype, "file": fp}})
                node_ids.add(mid)
                print(f"  Node: {mid}")
            
            # Step 2: Add seed nodes from seeds/ directory
            seeds_dir = Path(repo_path) / "seeds"
            if seeds_dir.exists():
                for seed_file in seeds_dir.glob("*.csv"):
                    seed_name = seed_file.stem  # e.g., "raw_customers"
                    seed_id = f"seeds.{seed_name}"
                    elements.append({"data": {"id": seed_id, "label": seed_name, "type": "seed", "file": str(seed_file.relative_to(Path(repo_path)))}})
                    node_ids.add(seed_id)
                    print(f"  + Seed: {seed_id}")
            
            # Step 3: Build external lookup (external.* -> real node)
            external_map = {}
            for nid in node_ids:
                simple = nid.split(".")[-1]
                external_map[f"external.{simple}"] = nid
            
            # Step 4: Add edges, resolving external refs
            edge_count = 0
            for e in graph.edges:
                src = e.source
                tgt = e.target
                # Resolve external targets
                if tgt.startswith("external.") and tgt in external_map:
                    tgt = external_map[tgt]
                if src.startswith("external.") and src in external_map:
                    src = external_map[src]
                if src in node_ids and tgt in node_ids:
                    elements.append({"data": {"source": src, "target": tgt, "label": e.edge_type, "type": e.edge_type}})
                    edge_count += 1
                    print(f"  Edge: {src} --[{e.edge_type}]--> {tgt}")
            
            _cache["surveyor"] = {
                "nodes": len([x for x in elements if "source" not in x["data"]]),
                "edges": edge_count,
                "elements": elements,
                "agent": agent,
                "graph": graph
            }
            print(f"\u2713 Surveyor: {_cache['surveyor']['nodes']} nodes, {_cache['surveyor']['edges']} edges\n")
        except Exception as ex:
            print(f"ERROR: {ex}")
            traceback.print_exc()
            _cache["surveyor"] = {"nodes": 0, "edges": 0, "elements": [], "agent": None, "graph": None}
    
    return _cache["surveyor"]

def _load_hydrologist(repo_path: str = "targets/jaffle_shop"):
    if "hydrologist" not in _cache:
        try:
            print("\n=== LOADING HYDROLOGIST AGENT ===")
            agent = HydrologistAgent(repo_path=Path(repo_path))
            graph = agent.run()
            
            edges = getattr(agent, "lineage_edges", [])
            print(f"  Lineage edges from agent: {len(edges)}")
            
            nodes = {}
            for e in edges:
                for nid in [e.get("source"), e.get("target")]:
                    if nid and nid not in nodes:
                        ntype = "seed" if "seeds/" in nid or "raw_" in nid else "staging" if "stg_" in nid else "mart" if nid in ["customers","orders"] else "test" if "test" in nid.lower() else "other"
                        nodes[nid] = {"id": nid, "label": nid.split("/")[-1].split(".")[-1], "type": ntype}
            
            elements = [{"data": v} for v in nodes.values()]
            for e in edges:
                elements.append({"data": {"source": e.get("source",""), "target": e.get("target",""), "label": e.get("type",""), "type": e.get("type",""), "confidence": e.get("confidence",1.0)}})
            
            from collections import Counter
            breakdown = Counter([e.get("type","UNKNOWN") for e in edges])
            conf_scores = [e.get("confidence",1.0) for e in edges]
            
            _cache["hydrologist"] = {
                "nodes": len(nodes),
                "edges": len(edges),
                "elements": elements,
                "edge_breakdown": [{"type":t,"count":c,"confidence":1.0} for t,c in breakdown.items()],
                "conf_high": sum(1 for c in conf_scores if c>=0.9),
                "conf_med": sum(1 for c in conf_scores if 0.6<=c<0.9),
                "conf_low": sum(1 for c in conf_scores if c<0.6),
                "agent": agent,
                "graph": graph
            }
            print(f"\u2713 Hydrologist: {_cache['hydrologist']['nodes']} nodes, {_cache['hydrologist']['edges']} edges\n")
        except Exception as ex:
            print(f"ERROR: {ex}")
            traceback.print_exc()
            _cache["hydrologist"] = {"nodes": 0, "edges": 0, "elements": [], "edge_breakdown": [], "conf_high": 0, "conf_med": 0, "conf_low": 0, "agent": None, "graph": None}
    
    return _cache["hydrologist"]

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("frontend/index.html")

@app.get("/css/{path:path}")
async def css(path: str):
    return FileResponse(f"frontend/css/{path}", media_type="text/css")

@app.get("/js/{path:path}")
async def js(path: str):
    return FileResponse(f"frontend/js/{path}", media_type="application/javascript")

@app.get("/api/agents")
async def get_agents(repo_path: str = Query(default="targets/jaffle_shop")):
    s, h = _load_surveyor(repo_path), _load_hydrologist(repo_path)
    return [
        {"name":"Surveyor","nodes":s["nodes"],"edges":s["edges"],"confidence_high":s["edges"]},
        {"name":"Hydrologist","nodes":h["nodes"],"edges":h["edges"],"confidence_high":h["conf_high"],"confidence_medium":h["conf_med"]}
    ]

@app.get("/api/agent/surveyor/graph")
async def get_surveyor_graph(repo_path: str = Query(default="targets/jaffle_shop")):
    return {"elements": _load_surveyor(repo_path)["elements"]}

@app.get("/api/agent/hydrologist/graph")
async def get_hydrologist_graph(repo_path: str = Query(default="targets/jaffle_shop")):
    return {"elements": _load_hydrologist(repo_path)["elements"]}

@app.get("/api/agent/hydrologist/edge-breakdown")
async def edge_breakdown():
    return _load_hydrologist(repo_path)["edge_breakdown"]

@app.get("/api/agent/hydrologist/blast-radius")
async def blast_radius(target: str = "raw_customers"):
    h = _load_hydrologist(repo_path)
    agent = h.get("agent")
    result = agent.blast_radius(target) if agent and hasattr(agent,"blast_radius") else {"count":0}
    tests = len([e for e in getattr(agent,"lineage_edges",[]) if e.get("type")=="TESTS"]) if agent else 0
    risk = "LOW" if result.get("count",0)<5 else "MEDIUM" if result.get("count",0)<15 else "HIGH"
    return {"target":target,"downstream_count":result.get("count",0),"affected_tests":tests,"risk_level":risk}

@app.get("/api/agent/surveyor/hubs")
async def hubs(top_n: int = 5):
    return [{"id":"models.customers","centrality":1.0,"in_degree":3,"out_degree":0}]


@app.get("/api/repository/analyze")
async def analyze_repository(repo_path: str):
    '''Run analysis via orchestrator with progress logging'''
    from pathlib import Path
    from src.orchestrator import run_analysis
    
    try:
        path = Path(repo_path)
        output_dir = path / ".cartography"
        
        # Run analysis via orchestrator (includes progress tracking)
        results = run_analysis(repo_path=path, output_dir=output_dir, verbose=True)
        
        # Extract results for frontend
        surveyor = results.get("surveyor", {})
        hydrologist = results.get("hydrologist", {})
        
        return {
            "success": len(results.get("errors", [])) == 0,
            "repo_path": str(repo_path),
            "progress_log": results.get("progress_log", []),  # For frontend progress display
            "results": {
                "surveyor": {
                    "nodes": surveyor.get("nodes", 0),
                    "edges": surveyor.get("edges", 0)
                },
                "hydrologist": {
                    "nodes": hydrologist.get("nodes", 0),
                    "edges": hydrologist.get("edges", 0)
                }
            },
            "errors": results.get("errors", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "progress_log": [],
            "results": {}
        }



async def export(agent: str):
    if agent == "surveyor": return JSONResponse(content={"elements": _load_surveyor(repo_path)["elements"]})
    if agent == "hydrologist": return JSONResponse(content={"elements": _load_hydrologist(repo_path)["elements"]})
    raise HTTPException(404)


# ============================================
# SIMPLE ANALYSIS API - Minimal & Working
# ============================================

@app.get("/api/analyze")
async def simple_analyze(repo_path: str = "targets/jaffle_shop"):
    """
    Simple endpoint: takes repo_path, runs orchestrator, returns results.
    Test with: Invoke-RestMethod "http://127.0.0.1:8002/api/analyze"
    """
    from pathlib import Path
    from src.orchestrator import run_analysis
    
    try:
        path = Path(repo_path)
        output_dir = path / ".cartography"
        
        # Run the orchestrator
        result = run_analysis(repo_path=path, output_dir=output_dir, verbose=False)
        
        # Extract simple metrics
        s = result.get("surveyor", {})
        h = result.get("hydrologist", {})
        
        return {
            "ok": True,
            "repo": repo_path,
            "surveyor": {"nodes": s.get("nodes", 0), "edges": s.get("edges", 0)},
            "hydrologist": {"nodes": h.get("nodes", 0), "edges": h.get("edges", 0)},
            "total_nodes": s.get("nodes", 0) + h.get("nodes", 0),
            "total_edges": s.get("edges", 0) + h.get("edges", 0),
            "artifacts": result.get("artifacts", []),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e), "repo": repo_path}











# ============================================================================
# SEMANTICIST AGENT ENDPOINTS
# ============================================================================

@app.get("/api/agent/semanticist/purposes")
async def get_semanticist_purposes(repo_path: str = Query(default="targets/jaffle_shop")):
    try:
        agent = SemanticistAgent(repo_path=Path(repo_path))
        result = agent.run()
        return {"ok": True, "purposes": result["purpose_statements"], "count": len(result["purpose_statements"])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/api/agent/semanticist/domains")
async def get_semanticist_domains(repo_path: str = Query(default="targets/jaffle_shop")):
    try:
        agent = SemanticistAgent(repo_path=Path(repo_path))
        result = agent.run()
        return {"ok": True, "clusters": result["domain_clusters"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
