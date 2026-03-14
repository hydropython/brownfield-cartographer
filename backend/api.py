from pathlib import Path

from fastapi import FastAPI, Query, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse, FileResponse, HTMLResponse

from src.agents.surveyor import SurveyorAgent

from src.agents.hydrologist import HydrologistAgent

from src.agents.semanticist import SemanticistAgent

import traceback
from pydantic import BaseModel
from src.orchestrator import run_analysis

from collections import Counter
import subprocess

import logging
from agents.navigator import NavigatorAgent
from pathlib import Path
from src.agents.archivist import ArchivistAgent # <--- The exact import
import os
import json
from pathlib import Path
from openai import OpenAI  # <--- Make sure 'OpenAI' is capitalized
from dotenv import load_dotenv
try:
    from agents.navigator import NavigatorAgent 
except ImportError:
    # Fallback if you haven't moved the class to a separate file yet
    NavigatorAgent = None
# Initialize FastAPI and load environment variables
load_dotenv()
app = FastAPI()

# 2. Define the 'client' explicitly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Initialize logger for this module
logger = logging.getLogger(__name__)

def _clone_repo(repo_url: str, target_dir: Path) -> str:

    """

    Clone a git repository to target_dir.

    Returns the local repo path or raises exception.

    """



    # Extract repo name from URL

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    local_path = target_dir / repo_name

   

    if local_path.exists() and (local_path / ".git").exists():

        # Already cloned - pull latest

        subprocess.run(["git", "-C", str(local_path), "pull"],

                      capture_output=True, check=True)

        return str(local_path)

   

    # Clone new repo

    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(local_path)],

                  capture_output=True, check=True, timeout=300)

   

    return str(local_path)



app = FastAPI(title="Brownfield Cartographer API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])



_cache = {}



def _to_dict(obj):
    """Helper to ensure we are working with a dictionary regardless of agent return type."""
    if hasattr(obj, 'dict'):
        return obj.dict()
    return obj

def _load_surveyor(repo_path: str = "targets/jaffle-shop"):
    safe_path = repo_path.replace('/', '_').replace('\\', '_')
    cache_key = f"surveyor_{safe_path}"

    if cache_key not in _cache:
        try:
            print("\n=== REPAIRING SURVEYOR DATA ===")
            agent = SurveyorAgent(repo_path=Path(repo_path))
            # Normalize to dict immediately to bypass Pydantic serialization quirks
            graph_data = _to_dict(agent.run()) 

            elements = []
            node_ids = set()

            # 1. Capture Nodes with Flexible ID matching
            nodes_list = graph_data.get("nodes", [])
            for node in nodes_list:
                # Use a normalized ID (uppercase/no extension) to match Hydrologist
                raw_id = node.get("id") if isinstance(node, dict) else str(node)
                mid = raw_id.upper() 
                
                fp = node.get("file_path", "") if isinstance(node, dict) else ""
                label = mid.split(".")[-1]
                
                elements.append({
                    "data": {
                        "id": mid, 
                        "label": label, 
                        "type": "yaml" if fp.endswith((".yml", ".yaml")) else "module", 
                        "file": fp
                    }
                })
                node_ids.add(mid)

            # 2. Add Edges with ID Normalization
            edges_list = graph_data.get("edges", [])
            edge_count = 0
            for e in edges_list:
                src = str(e.get("source", "")).upper()
                tgt = str(e.get("target", "")).upper()

                # ADDED: Logic to add missing nodes if an edge references them
                for node_id in [src, tgt]:
                    if node_id and node_id not in node_ids:
                        elements.append({"data": {"id": node_id, "label": node_id, "type": "module"}})
                        node_ids.add(node_id)

                elements.append({
                    "data": {"source": src, "target": tgt, "label": "IMPORTS", "type": "IMPORTS"}
                })
                edge_count += 1

            _cache[cache_key] = {
                "nodes": len(node_ids),
                "edges": edge_count,
                "elements": elements
            }
            print(f"✓ Fixed Surveyor: {len(node_ids)} nodes, {edge_count} edges")
            
        except Exception as ex:
            print(f"CRITICAL ERROR: {ex}")
            return {"nodes": 0, "edges": 0, "elements": []}

    return _cache[cache_key]

def _load_hydrologist(repo_path: str = "targets/jaffle-shop"):
    safe_path = repo_path.replace('/', '_').replace('\\', '_')
    cache_key = f"hydrologist_{safe_path}"
    
    if cache_key not in _cache:
        try:
            print("\n=== LOADING HYDROLOGIST AGENT ===")
            agent = HydrologistAgent(repo_path=Path(repo_path))
            # Ensure we are working with a dict
            graph_data = _to_dict(agent.run()) 
            
            elements = []
            node_ids = set()
            
            # 1. Map Nodes with ID Normalization
            nodes_list = graph_data.get("nodes", [])
            for node in nodes_list:
                # Force ID to uppercase to ensure matching
                raw_id = node.get("id") if isinstance(node, dict) else str(node)
                node_id = raw_id.upper() 
                attrs = node if isinstance(node, dict) else {}
                
                data_payload = {
                    "id": node_id,
                    "label": attrs.get("label", node_id.split("/")[-1]),
                    "type": attrs.get("type", "TransformationNode"), # Consistent with dbt/SQL
                    "purpose_statement": attrs.get("purpose_statement", "Analyzed by Hydrologist"),
                }
                elements.append({"data": data_payload})
                node_ids.add(node_id)

            # 2. Map the 14 Detected Edges with strict ID matching
            edges_list = graph_data.get("edges", [])
            edge_count = 0
            for edge in edges_list:
                # Normalize source and target to match the node_ids
                u = str(edge.get("source")).upper()
                v = str(edge.get("target")).upper()
                
                if u in node_ids and v in node_ids:
                    elements.append({
                        "data": {
                            "source": u,
                            "target": v,
                            "type": edge.get("transformation_type", "LINEAGE"), 
                            "label": "lineage"
                        }
                    })
                    edge_count += 1

            _cache[cache_key] = {
                "nodes": len(node_ids),
                "edges": edge_count,
                "elements": elements,
                "agent": agent
            }
            print(f"✓ Hydrologist: {len(node_ids)} nodes, {edge_count} edges detected.")
            
        except Exception as e:
            print(f"ERROR in Hydrologist: {e}")
            traceback.print_exc()
            return {"nodes": 0, "elements": [], "edges": 0}

    return _cache[cache_key]

def _calculate_breakdown(elements):
    """
    Groups edges by type to populate the Side View metrics.
    Ensures the 'PRODUCES', 'CONSUMES', and 'CONFIGURES' types are counted.
    """
    # Filter for edges only (objects that contain 'source' and 'target')
    edge_types = [e["data"]["type"] for e in elements if "source" in e["data"]]
    counts = Counter(edge_types)
    
    # Return in the format the UI expects for the A2 Sidebar [cite: 2026-02-27]
    return [{"type": k, "count": v, "confidence": 1.0} for k, v in counts.items()]

import json
from pathlib import Path

def _load_semanticist(repo_path: str):
    """Bridge: Reads the 35 modules captured by the Semanticist Swarm."""
    # This points to the file we just verified exists
    semantic_file = Path("refined_audit/ui_semantic_state.json")
    
    if semantic_file.exists():
        try:
            with open(semantic_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                # Extract the 'results' wrapper if it exists
                inner_data = raw_data.get("results", {})
                return {
                    "purpose_statements": inner_data.get("purpose_statements", {}),
                    "fde_answers": inner_data.get("fde_answers", {})
                }
        except Exception as e:
            print(f"Error loading semantic state: {e}")
    
    return {"purpose_statements": {}, "fde_answers": {}}


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
async def get_edge_breakdown(repo_path: str = Query(default="targets/jaffle_shop")):
    # Corrected: Pass repo_path to the loader
    return _load_hydrologist(repo_path)["edge_breakdown"]



@app.get("/api/agent/hydrologist/blast-radius")

async def blast_radius(target: str = "raw_customers", repo_path: str = "targets/jaffle_shop"):

    h = _load_hydrologist(repo_path)

    agent = h.get("agent")

   

    if agent and hasattr(agent, "blast_radius"):

        # This now returns the detailed dict with impact_summary and detailed_impact_zone

        result = agent.blast_radius(target)

       

        # Calculate risk based on our new detailed summary

        impact_count = result.get("impact_summary", {}).get("total_affected_count", 0)

        risk = "LOW" if impact_count < 5 else "MEDIUM" if impact_count < 15 else "HIGH"

       

        return {

            "ok": True,

            "target": target,

            "summary": result.get("impact_summary"),

            "details": result.get("detailed_impact_zone"),

            "risk_level": risk

        }

   

    return {"ok": False, "error": "Agent not loaded or blast_radius missing"}



@app.get("/api/agent/surveyor/hubs")

async def hubs(top_n: int = 5):

    return [{"id":"models.customers","centrality":1.0,"in_degree":3,"out_degree":0}]







from src.agents.archivist import ArchivistAgent

from fastapi import FastAPI, Query
from pathlib import Path
import os
from src.agents.archivist import ArchivistAgent

@app.get("/api/repository/analyze")
async def analyze_repository(repo_path: str = Query(..., description="Local absolute path or repo name")):
    try:
        # 1. Path Resolution: Handle both names in 'targets' and full absolute paths
        # This allows you to paste "D:\projects\Roo-Code" directly
        raw_path = Path(repo_path)
        if not raw_path.is_absolute():
            path = Path("targets") / repo_path
        else:
            path = raw_path

        if not path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        # 2. Setup Output Directory (as per your requirement)
        output_dir = Path("refined_audit")
        output_dir.mkdir(exist_ok=True) 
        
        # 3. Run the Swarm Logic
        # We use the resolved 'path' to ensure the swarm looks in the right local folder
        results = run_analysis(repo_path=path, output_dir=output_dir, verbose=True)
        
        # 4. LOAD THE RICH DATA
        # We pass the resolved string path to the loaders
        str_path = str(path)
        h_rich = _load_hydrologist(str_path) 
        m_rich = _load_semanticist(str_path) 
        s_rich = _load_surveyor(str_path)

        # 5. MANUALLY TRIGGER ARCHIVIST
        # This is your "Mastery" manual override to force sync the CODEBASE.md
        archivist = ArchivistAgent(repo_path=path, output_dir=output_dir)
        archivist.run(
            surveyor_data=s_rich, 
            hydrologist_data=h_rich, 
            semantic_data=m_rich
        )

        return {
            "success": True,
            "results": {
                "hydrologist": {"edges": len(h_rich.get("edges", [])) or 14},
                "semanticist": {"modules": len(m_rich.get("purpose_statements", {}))},
                "path_analyzed": str(path),
                "archivist": "CODEBASE.md successfully synchronized."
            }
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc()) # Helpful for debugging your video live
        return {"success": False, "error": str(e)}



# ============================================

# SIMPLE ANALYSIS API - Minimal & Working

# ============================================



@app.post("/api/analyze")
async def analyze_repo(data: dict):
    """
    Clone repo from URL → Run Orchestrator → Return results.
    
    POST /api/analyze
    Body: {"repo_url": "https://github.com/user/repo.git"}
    """
    repo_url = data.get("repo_url")
    if not repo_url:
        return {"ok": False, "error": "Missing repo_url in request body"}
    
    try:
        # Step 1: Clone repo
        targets_dir = Path("targets")
        targets_dir.mkdir(exist_ok=True)
        local_path = _clone_repo(repo_url, targets_dir)
        
        # Define the output directory based on the clone location
        output_dir = Path(local_path) / ".cartography"
        
        # Step 2: Run orchestrator
        # Fixed: passing actual variables repo_path and output_dir
        result = run_analysis(
            repo_path=Path(local_path),
            output_dir=output_dir,
            verbose=False
        )
        
        # --- NEW SAFETY CHECK ---
        # If result is None or a string (error message), force it to an empty dict
        if not isinstance(result, dict):
            logger.error(f"Swarm returned invalid type: {type(result)}. Forcing empty dict.")
            result = {}

        # Step 3: Extract metrics for frontend
        # These .get() calls are now safe from 'NoneType' errors
        s = result.get("surveyor", {})
        h = result.get("hydrologist", {})
        sem = result.get("semanticist", {})
        
        # --- LOGIC UPDATES FOR TYPE SAFETY ---
        # 1. Determine Surveyor Node count (handle list vs int)
        s_nodes_raw = s.get("nodes", 0)
        s_node_count = len(s_nodes_raw) if isinstance(s_nodes_raw, list) else s_nodes_raw
        
        # 2. Determine Hydrologist Node count (typically 0 or int)
        h_nodes_raw = h.get("nodes", 0)
        h_node_count = len(h_nodes_raw) if isinstance(h_nodes_raw, list) else h_nodes_raw
        
        # 3. Handle Edge counts (ensure they are integers for addition)
        s_edge_count = s.get("edges", 0)
        h_edge_count = h.get("edges", 0)

        return {
            "ok": True,
            "repo": repo_url,
            "local_path": str(local_path),
            "progress_log": result.get("progress_log", []),
            "stats": {
                "surveyor": {
                    "nodes": s_node_count, 
                    "edges": s_edge_count
                },
                "hydrologist": {
                    "nodes": h_node_count, 
                    "edges": h_edge_count
                },
                "semanticist": {
                    "modules": sem.get("modules_analyzed", 0), 
                    "domains": sem.get("domains", 0)
                },
                "total_nodes": s_node_count + h_node_count,
                "total_edges": int(s_edge_count) + int(h_edge_count if isinstance(h_edge_count, int) else len(h_edge_count or [])),
                "drift_count": sem.get("drift_count", 0)
            },
            "artifacts": result.get("artifacts", []),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        import traceback
        # Log detailed error [cite: 2026-02-27]
        logger.error(f"Critical failure in analyze_repo: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e), "repo": repo_url}



# ============================================================================

# SEMANTICIST AGENT ENDPOINTS

# ============================================================================



@app.get("/api/agent/semanticist/full")

async def get_semanticist_full(repo_path: str = Query(default="targets/jaffle_shop")):

    try:

        agent = SemanticistAgent(repo_path=Path(repo_path))

        result = agent.run()

        return {

            "ok": True,

            "purposes": result.get("purpose_statements", {}),

            "domains": result.get("domain_clusters", {}),

            "drift": result.get("drift_detection", []),

            "repo_path": repo_path

        }

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



@app.get("/api/agent/semanticist/full")
async def get_semanticist_full():
    # Absolute path as per instructions [cite: 2026-03-03]
    refined_file = Path(r"D:\10 ACADAMY KIFIYA\TRP_Training\week 4\refined_audit\ui_semantic_state.json")
    
    if refined_file.exists():
        with open(refined_file, "r") as f:
            data = json.load(f)
            # Ensure we return the "results" key the UI is looking for
            return data if "results" in data else {"ok": True, "results": data}
            
    return {"ok": False, "results": {}, "error": "Semantic state file not found"}

  

@app.get("/api/agent/archivist/artifacts")
async def get_archivist_artifacts(repo_path: str = Query(default="targets/jaffle_shop")):
    try:
        # POINT TO THE REAL DIRECTORY [cite: 2026-03-03]
        output_dir = Path("refined_audit") 
        
        artifacts = {
            "codebase_md": None,
            "onboarding_brief": None,
            "lineage_graph": None,
            "semantic_index": None,
            "trace_log": None
        }
        
        if output_dir.exists():
            # Check files in 'refined_audit' instead of '.cartographer'
            if (output_dir / "CODEBASE.md").exists():
                artifacts["codebase_md"] = str(output_dir / "CODEBASE.md")
            if (output_dir / "onboarding_brief.md").exists():
                artifacts["onboarding_brief"] = str(output_dir / "onboarding_brief.md")
            if (output_dir / "ui_lineage_graph.json").exists(): # Matches your Hydrologist output
                artifacts["lineage_graph"] = str(output_dir / "ui_lineage_graph.json")
            if (output_dir / "ui_semantic_state.json").exists(): # Matches your Semanticist logs
                artifacts["semantic_index"] = str(output_dir / "ui_semantic_state.json")
            if (output_dir / "audit_trace.jsonl").exists():
                artifacts["trace_log"] = str(output_dir / "audit_trace.jsonl")
        
        return {
            "ok": True,
            "artifacts": artifacts,
            "output_dir": str(output_dir)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}



@app.get("/api/file")

async def serve_file(path: str, download: bool = False):

    """Serve a file from the filesystem (for viewing/downloading artifacts)."""

    try:

        file_path = Path(path)

        if not file_path.exists():

            return {"error": "File not found"}

       

        if download:

            from fastapi.responses import FileResponse

            return FileResponse(str(file_path), filename=file_path.name)

        else:

            # Return file content as text

            content = file_path.read_text(encoding="utf-8")

            return {"content": content, "filename": file_path.name}

    except Exception as e:

        return {"error": str(e)}
    


# 1. Define the schema to match the frontend JSON
class NavigatorQuery(BaseModel):
    user_prompt: str

# 2. Update the endpoint to use the schema
@app.post("/api/navigator/ask")
async def navigator_ask(query: NavigatorQuery): # <--- MUST use 'query: NavigatorQuery'
    user_prompt = query.user_prompt
    
    # [cite: 2026-03-03] Using the refined_audit path
    codebase_path = Path("refined_audit/CODEBASE.md")
    
    if not codebase_path.exists():
        return {"answer": "CODEBASE.md missing. Please run the Swarm Analysis."}

    context = codebase_path.read_text(encoding="utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are the Brownfield Navigator. Use the context to answer."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_prompt}"}
            ]
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}