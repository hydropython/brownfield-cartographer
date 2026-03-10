
# Brownfield Cartographer — Constitution v1.1

*Git-First, Incremental, Production-Grade Code Analysis for FDE Onboarding*

**Last Updated:** March 2025  
**Final Deadline:** Sunday March 15, 03:00 UTC  
**Status:** Phase 1 (Surveyor) Complete — Phase 2 (Hydrologist) In Progress

---

## Project Identity

| Field | Value |
|-------|-------|
| **Name** | Brownfield Cartographer |
| **Purpose** | Deployable codebase intelligence system for Forward-Deployed Engineer (FDE) onboarding |
| **Target Users** | FDEs working in data engineering environments with unfamiliar production codebases |
| **Success Metric** | Answers all Five FDE Day-One Questions with evidence citations in <1 hour |
| **Final Deadline** | Sunday March 15, 03:00 UTC |

---

## Non-Negotiable Principles (8 Rules)

### Rule 1: No Hallucinated Code
Every code snippet must be:
- ✅ Syntactically valid
- ✅ Dependency-checked against current library docs
- ✅ Minimal and testable before scaling

If uncertain about a library API, search official docs before suggesting code.

### Rule 2: Verification Before Progression
Do not proceed to Phase N until Phase N-1 is confirmed working on the user's machine.

Each task must include:
1. Expected output
2. How to test locally
3. Failure recovery steps

### Rule 3: Evidence-Based Outputs
Every claim in generated artifacts must cite evidence:
- File path + line number
- Analysis method (static vs. LLM inference)
- Confidence score (0.0-1.0)

| Evidence Type | Confidence | Source |
|--------------|------------|--------|
| `static` | 1.0 | Direct AST parse (tree-sitter) |
| `algorithmic` | 0.9 | Graph algorithm (PageRank, reachability) |
| `inference` | 0.6 | LLM or heuristic inference |
| `heuristic` | 0.3 | Pattern match or best guess |

### Rule 4: Graceful Degradation (Fail-Open)
If a file cannot be parsed:
- Log a warning to `cartography_trace.jsonl`
- Continue processing remaining files
- Never crash the entire pipeline

Handle dynamic references (f-strings, variables) by flagging as "unresolved" — never guess.

### Rule 5: Security First
Never send client code to an LLM without scanning for secrets first.

Requirements:
- Use `detect-secrets` or regex patterns to redact before LLM ingestion
- Log all redactions in `cartography_trace.jsonl`
- Never store secrets in output artifacts

### Rule 6: Cost Awareness
Track LLM token usage throughout analysis.

| Task Type | Model Selection | Rationale |
|-----------|-----------------|-----------|
| Bulk tasks (purpose statements) | Gemini Flash / Mistral | Cheap, fast |
| Synthesis tasks (Day-One answers) | Claude / GPT-4 | Expensive, accurate |
| Budget alert | 50% of estimated token limit | Prevent overruns |

### Rule 7: Incremental Delivery
| Deadline | Deliverable |
|----------|-------------|
| **Thursday Interim** | Surveyor + Hydrologist (structure + lineage) |
| **Sunday Final** | Semanticist + Navigator + Frontend (full pipeline) |

Never block delivery on stretch goals. Ship working core first.

### Rule 8: User Control
Always ask for explicit confirmation before proceeding to next phase.

If the user expresses doubt:
1. Pause immediately
2. Diagnose root cause
3. Propose verification step
4. Wait for explicit approval to continue

---

## Git-First Incremental Workflow

### Complete Incremental Analysis Flow

The incremental re-analysis pipeline follows this exact sequence:

**Step 1 — Load Previous State:** Load previous `module_graph.json` from `.cartography/` directory if it exists. This preserves historical node and edge data for unchanged files.

**Step 2 — Identify Changed Files:** Run `git diff <base_commit_sha> --name-only` to get the list of files that have changed since the last analysis. This ensures we only re-parse what has actually changed.

**Step 3 — Re-Analyze Changed Files:** Re-analyze only changed files via `Surveyor.analyze_module()` method. Unchanged files retain their previously parsed nodes and edges without re-parsing.

**Step 4 — Merge Graph State:** Merge new nodes and edges with preserved graph state from the previous run. New nodes are added, modified nodes are updated, and the graph structure is maintained.

**Step 5 — Mark Stale Nodes:** Mark stale nodes (from deleted files) as `is_stale: true` in the graph metadata. These nodes are retained for historical reference but flagged as no longer present in the codebase.

**Step 6 — Re-Run Graph Algorithms:** Re-run PageRank and Strongly Connected Components (SCC) algorithms on the updated graph to recalculate architectural hubs and circular dependencies based on the new structure.

**Step 7 — Output with Incremental Flag:** Output updated `module_graph.json` with `incremental_mode: true` flag in the metadata to indicate this was a partial re-analysis rather than a full scan.

### Reproducibility Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| Commit tracking | Every artifact includes `base_commit_sha` |
| Timestamp | `analyzed_at` in ISO 8601 format |
| Determinism | Re-running with same commit SHA produces identical output |
| Audit trail | `cartography_trace.jsonl` logs all parsing decisions |

### Git Integration Points

| Component | Git Command | Purpose |
|-----------|------------|---------|
| GitVelocityAnalyzer | `git log --follow --since="<date>" -- <file>` | Change frequency per file |
| Surveyor.incremental_mode | `git diff <sha> --name-only` | Identify changed files |
| ModuleNode.git_sha | `git rev-parse HEAD` | Record commit at analysis time |
| Archivist.trace logging | `git show <sha>:<file>` | Reproduce file state at analysis |

---

## File Structure (Spec-Compliant)
```
brownfield-cartographer/
├── src/
│ ├── cli.py # Entry point: analyze, query commands
│ ├── orchestrator.py # Pipeline: Surveyor → Hydrologist → Semanticist → Archivist
│ ├── models/ # Pydantic schemas
│ │ ├── nodes.py # ModuleNode, DatasetNode, FunctionNode, TransformationNode
│ │ ├── edges.py # Edge, EdgeType
│ │ └── graph.py # CartographyGraph (Pydantic container)
│ ├── analyzers/ # Low-level parsing logic
│ │ ├── tree_sitter_analyzer.py # Multi-language AST parsing (LanguageRouter)
│ │ ├── sql_lineage.py # sqlglot-based SQL dependency extraction
│ │ └── dag_config_parser.py # Airflow/dbt YAML config parsing
│ ├── agents/ # High-level analysis agents
│ │ ├── surveyor.py # Static structure: module graph, PageRank, git velocity
│ │ ├── hydrologist.py # Data lineage: blast_radius, find_sources/sinks
│ │ ├── semanticist.py # LLM enrichment: purpose statements, doc drift
│ │ ├── archivist.py # Documentation: CODEBASE.md, onboarding brief
│ │ └── navigator.py # Interactive query agent with 4 tools
│ └── graph/
│ └── knowledge_graph.py # NetworkX wrapper with serialization
├── .cartography/ # Output artifacts (gitignored)
│ ├── module_graph.json # Surveyor output (NetworkX node_link_data)
│ ├── lineage_graph.json # Hydrologist output (data flow graph)
│ ├── CODEBASE.md # Archivist output (auto-generated docs)
│ ├── onboarding_brief.md # Archivist output (FDE onboarding guide)
│ └── cartography_trace.jsonl # Audit log (one JSON line per parsing decision)
├── targets/ # Target codebases for analysis
│ ├── jaffle_shop/ # dbt demo project (Phase 1 target)
│ └── <additional_targets>/ # Phase 2+ targets
├── pyproject.toml # Locked dependencies (uv)
├── README.md # Usage: install, analyze, query
└── CONSTITUTION.md # This document
```

---


---

## Artifact Specifications

### .cartography/module_graph.json (Surveyor Output)

| Field | Type | Description |
|-------|------|-------------|
| repo_name | string | Target repository name |
| repo_path | string | Local path or URL |
| analyzed_at | datetime | Analysis timestamp (ISO 8601) |
| base_commit_sha | string | Git commit SHA at analysis time |
| incremental_mode | bool | True if partial re-analysis via git diff |
| total_nodes | int | Total node count |
| total_edges | int | Total edge count |
| architectural_hubs | list[str] | Top 5 modules by PageRank centrality |
| dead_code_candidates | list[str] | Exported symbols with in_degree=0 |
| parse_warnings | list[str] | Non-fatal parse issues |
| nodes | list | NetworkX node_link_data format |
| links | list | NetworkX edge_link_data format |

### .cartography/lineage_graph.json (Hydrologist Output)

| Field | Type | Description |
|-------|------|-------------|
| sources | list[str] | Entry-point tables (find_sources()) |
| sinks | list[str] | Output tables (find_sinks()) |
| transformations | list | SQL/dbt transformations |
| blast_radius | dict | table_id → downstream impact |
| lineage_edges | list | table → transformation → table |

### .cartography/cartography_trace.jsonl (Audit Log)

| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | ISO 8601 timestamp |
| file_path | string | File being processed |
| action | string | parse, skip, warn, error |
| result | string | Outcome description |
| confidence | float | 0.0-1.0 confidence score |
| evidence_type | string | static, algorithmic, inference, heuristic |

---

## Four-Agent Pipeline

| Agent | Phase | Purpose | Key Outputs |
|-------|-------|---------|-------------|
| Surveyor | 1 | Static structure analysis | module_graph.json, PageRank hubs, git velocity |
| Hydrologist | 2 | Data lineage extraction | lineage_graph.json, blast_radius, sources/sinks |
| Semanticist | 3 | LLM enrichment | Purpose statements, doc drift detection, domain clustering |
| Archivist | 4 | Documentation generation | CODEBASE.md, onboarding_brief.md, trace logging |

### Navigator Agent (Query Interface)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| find_implementation | Locate symbol definition | symbol_name | file:line, signature, confidence |
| trace_lineage | Trace data flow | table_name | upstream/downstream tables |
| blast_radius | Compute impact | table_name | affected downstream modules |
| explain_module | Generate explanation | module_path | purpose statement, key functions |

---

## Technical Constraints

| Constraint | Value |
|------------|-------|
| Python Version | 3.10+ |
| Dependency Manager | uv |
| AST Parser | tree-sitter 0.22+ (Python, SQL, YAML) |
| SQL Parser | sqlglot (Postgres, BigQuery, Snowflake, DuckDB) |
| Graph Library | NetworkX 3.x |
| Agent Orchestration | LangGraph |
| Vector Store | faiss or chromadb |
| Frontend | Zero-server (Cytoscape.js + Tailwind via CDN) |
| Knowledge Graph | Pydantic models + NetworkX JSON serialization |

---

## Quality Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| Code Length | No code >50 lines without prior validation | Enforced |
| LLM Calls | All calls track token budget + tiered model selection | Phase 3 |
| Error Handling | Graceful degradation on unparseable files | Enforced |
| Testing | Each task has verification checkpoint | Enforced |
| PageRank | Real PageRank (alpha=0.85), not in-degree alternative | TASK-007 |
| Incremental Mode | git diff-based re-analysis | Phase 2 |

---

## Success Criteria by Phase

### Phase 1 (Surveyor) — COMPLETE (TASK-007)

- [x] Tree-sitter 0.22+ API (QueryCursor)
- [x] LanguageRouter for Python/SQL/YAML
- [x] Module graph with 142+ edges
- [x] PageRank hub detection (alpha=0.85, scipy)
- [x] Git velocity + Pareto 80/20 core
- [x] NetworkX node_link_data JSON output
- [x] Graceful degradation (fail-open)

### Phase 2 (Hydrologist) — IN PROGRESS (TASK-008)

- [ ] sqlglot-based SQL lineage extraction
- [ ] dbt ref()/source() resolution
- [ ] blast_radius computation
- [ ] lineage_graph.json output
- [ ] find_sources()/find_sinks() methods

### Phase 3 (Semanticist) — PLANNED (TASK-009)

- [ ] LLM purpose statement generation
- [ ] Doc drift detection
- [ ] Domain clustering
- [ ] Day-One question answering
- [ ] ContextWindowBudget management

### Phase 4 (Archivist + Navigator) — PLANNED (TASK-010+)

- [ ] CODEBASE.md generation
- [ ] onboarding_brief.md
- [ ] Navigator interactive query mode
- [ ] cartography_trace.jsonl audit log
- [ ] Incremental update mode (git diff)

---

## Communication Protocol

| Situation | Required Action |
|-----------|-----------------|
| Uncertain about library API | Search docs before suggesting code |
| Suggestion fails | Diagnose root cause before proposing alternatives |
| Phase transition | Ask for explicit confirmation before proceeding |
| User expresses doubt | Pause, diagnose, propose verification, wait for approval |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-03-10 | Initial constitution created |
| 1.1 | 2025-03-12 | Git-first workflow, file structure, artifact specs, four-agent pipeline, PageRank requirement, incremental analysis flow |

---

*Brownfield Cartographer Constitution v1.1 — Git-First Incremental Design, Spec-Compliant*
"""

# Write the file at correct path
with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✓ Created constitution.md at correct path: {output_path.absolute()}")
print(f"  Size: {output_path.stat().st_size} bytes")
print(f"  Lines: {len(content.splitlines())}")
'@ | Out-File -FilePath "create_constitution_correct.py" -Encoding UTF8

# Run the Python script
python create_constitution_correct.py

# Clean up
Remove-Item "create_constitution_correct.py"