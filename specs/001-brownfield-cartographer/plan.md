# Brownfield Cartographer  Technical Implementation Plan

## Architecture Overview

The system follows a 4-agent pipeline with a central Knowledge Graph:

1. **Surveyor (Phase 1)**: Static structure analysis via tree-sitter
2. **Hydrologist (Phase 2)**: Data lineage extraction via sqlglot + tree-sitter
3. **Semanticist (Phase 3)**: LLM-powered purpose extraction + domain clustering
4. **Archivist + Navigator (Phase 4)**: Output generation + query interface

All agents write to/read from a central Knowledge Graph (NetworkX + Vector Store).

---

## Tech Stack

| Component | Technology | Purpose | Version Constraint |
|-----------|-----------|---------|-------------------|
| Language | Python | Implementation | 3.10+ |
| Package Manager | uv | Dependency management | Latest |
| AST Parser | tree-sitter + grammars | Multi-language code parsing | python, sql, yaml |
| SQL Parser | sqlglot | SQL dialect parsing & lineage | Postgres, BigQuery, Snowflake, DuckDB |
| Graph Library | NetworkX | Dependency graphs + algorithms | DiGraph, PageRank, BFS |
| Agent Framework | LangGraph | Navigator query orchestration | StateGraph, tool binding |
| Vector Store | faiss or chromadb | Semantic search index | Embedding similarity |
| LLM API | OpenRouter / Anthropic | Purpose statements + synthesis | Tiered model selection |
| Frontend | Cytoscape.js + Tailwind CDN | Interactive graph visualization | Zero-server static HTML |
| Templating | Jinja2 | CODEBASE.md generation | Structured output |

---

## Data Flow

1. INPUT: Repo path (local or GitHub URL)
2. SURVEYOR (Phase 1):
   - Parse files with tree-sitter (Python/SQL/YAML)
   - Extract imports, functions, classes
   - Analyze git log for change velocity
   - Build module_graph.json (NetworkX DiGraph)
3. HYDROLOGIST (Phase 2):
   - Parse SQL with sqlglot  table dependencies
   - Parse Python  pandas/spark read/write calls
   - Parse YAML  Airflow/dbt config topology
   - Build lineage_graph.json (DataLineageGraph)
4. SEMANTICIST (Phase 3):
   - Generate purpose statements via LLM (code, not docstring)
   - Detect documentation drift (docstring vs. implementation)
   - Cluster modules into domains (embeddings + k-means)
   - Synthesize Five Day-One Answers (LLM + evidence)
5. ARCHIVIST (Phase 4):
   - Generate CODEBASE.md (living context)
   - Generate onboarding_brief.md (5 answers + citations)
   - Serialize graphs to JSON
   - Log all actions to cartography_trace.jsonl
6. NAVIGATOR (Query Mode):
   - find_implementation(concept)  semantic search
   - trace_lineage(dataset, direction)  graph traversal
   - blast_radius(module_path)  impact analysis
   - explain_module(path)  generative summary + evidence

---

## Knowledge Graph Schema

### Node Types (Pydantic)
- ModuleNode: path, language, purpose_statement, domain_cluster, complexity_score, change_velocity_30d, is_dead_code_candidate, last_modified, confidence_score, evidence_type, scope
- DatasetNode: name, storage_type, schema_snapshot, freshness_sla, owner, is_source_of_truth, confidence_score, evidence_type, scope
- FunctionNode: qualified_name, parent_module, signature, purpose_statement, call_count_within_repo, is_public_api, confidence_score
- TransformationNode: source_datasets, target_datasets, transformation_type, source_file, line_range, sql_query_if_applicable, confidence_score

### Edge Types
- IMPORTS: source_module  target_module (weight=import_count)
- PRODUCES: transformation  dataset (data lineage)
- CONSUMES: transformation  dataset (upstream dependency)
- CALLS: function  function (call graph)
- CONFIGURES: config_file  module/pipeline (YAML/ENV relationship)

### Confidence Scoring
| Evidence Type | Confidence Range | Example |
|--------------|-----------------|---------|
| static | 0.9-1.0 | tree-sitter AST parse, sqlglot table ref |
| algorithmic | 0.8-0.95 | PageRank, BFS traversal, git log count |
| inference | 0.6-0.85 | LLM purpose statement, domain clustering |
| heuristic | 0.3-0.7 | Dynamic reference detection, dead code candidate |

---

## Incremental Delivery Plan

### Thursday Interim (March 12)
| Component | Deliverable | Success Criteria |
|-----------|-------------|-----------------|
| Surveyor | module_graph.json | Parses Python files, builds import graph, PageRank works |
| Hydrologist | lineage_graph.json | Parses SQL with sqlglot, extracts table dependencies |
| CLI | cartographer analyze command | Accepts repo path, outputs JSON artifacts |
| Tests | Basic unit tests | Surveyor + Hydrologist have test coverage |

### Sunday Final (March 15)
| Component | Deliverable | Success Criteria |
|-----------|-------------|-----------------|
| Semanticist | Purpose statements + domain clusters | LLM generates purpose for 80%+ modules |
| Archivist | CODEBASE.md + onboarding_brief.md | Answers all 5 Day-One Questions with evidence |
| Navigator | 4 query tools working | Each tool returns evidence-cited answers |
| Frontend | index.html interactive graph | Renders in browser, supports search + zoom |
| Incremental Mode | git diff-based re-analysis | Only changed files re-parsed on re-run |

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Over-scoping | Strict Thursday/Sunday split; no stretch goals before core | Architect |
| LLM hallucination | Constitution Rule 1 + evidence citations + confidence scores | Semanticist |
| Parse failures | Graceful degradation: log warning + skip file, never crash | All agents |
| Secret leakage | Security scanner pre-LLM; redact before ingestion | SecurityScanner |
| Performance | Incremental updates via git diff; cache parsed ASTs | Orchestrator |
| Trust gap | Distinguish static vs. inference in all outputs; audit trace | Archivist |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-03-10 | Initial plan created |
