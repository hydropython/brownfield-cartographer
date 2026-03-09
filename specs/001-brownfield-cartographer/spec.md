# Brownfield Cartographer  Product Specification

## Overview
A codebase intelligence system that ingests any GitHub repository or local path containing Python/SQL/YAML data engineering code and produces a living, queryable knowledge graph of architecture, data flows, and semantic structure.

## Target User
Forward-Deployed Engineers (FDEs) who are embedded at client sites and must rapidly develop a working mental model of unfamiliar production systems within 72 hours.

---

## User Journeys

### Journey 1: Cold Start Onboarding
**As an** FDE embedded at a client  
**I want to** point the Cartographer at an unfamiliar codebase  
**So that** I get a working mental model in <1 hour  

**Acceptance Criteria:**
- System accepts local path or GitHub URL
- Analysis completes in <30 minutes for 50k LOC repo
- Outputs `CODEBASE.md` with architecture overview

### Journey 2: Lineage Investigation
**As an** FDE debugging a data pipeline  
**I want to** ask "What produces this dataset?"  
**So that** I can trace upstream dependencies with evidence  

**Acceptance Criteria:**
- Query returns file:line citations
- Distinguishes static analysis () from LLM inference ()
- Handles mixed Python/SQL/YAML codebases

### Journey 3: Impact Assessment
**As an** FDE planning a refactor  
**I want to** ask "What breaks if I change this module?"  
**So that** I understand the blast radius before modifying code  

**Acceptance Criteria:**
- Returns direct + indirect dependents
- Flags external dependencies (ghost nodes)
- Includes confidence scores per edge

### Journey 4: Living Context Injection
**As an** FDE using AI coding assistants  
**I want to** inject `CODEBASE.md` as system context  
**So that** the AI has instant architectural awareness  

**Acceptance Criteria:**
- `CODEBASE.md` is structured for AI consumption
- Contains critical path, data sources, known debt
- Updates incrementally via git diff

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Onboarding Time** | <1 hour to working mental model | Time from `cartographer analyze` to `CODEBASE.md` readable |
| **Answer Accuracy** | 5/5 Day-One Questions correct | Compare `onboarding_brief.md` vs. `RECONNAISSANCE.md` |
| **Evidence Citation** | 100% of claims cite file:line | Audit `cartography_trace.jsonl` |
| **Confidence Transparency** | All outputs include confidence score | Validate schema on all nodes/edges |
| **Incremental Update** | Re-analyze only changed files | Measure time delta: full vs. incremental |

---

## Non-Goals (v1)

| Out of Scope | Reason |
|--------------|--------|
| Cross-repo credential access | Security complexity; use ghost nodes instead |
| Real-time runtime tracing | Requires cluster access; post-v1 feature |
| Non-data-engineering codebases | Focus on FDE's primary domain |
| Multi-language beyond Python/SQL/YAML | Scope control; extensible architecture |

---

## Acceptance Criteria (System-Level)

1. **Input**: Accepts local path or GitHub URL
2. **Output**: Generates `.cartography/` directory with:
   - `CODEBASE.md` (living context)
   - `onboarding_brief.md` (5 Day-One Answers)
   - `module_graph.json` (Surveyor output)
   - `lineage_graph.json` (Hydrologist output)
   - `cartography_trace.jsonl` (audit log)
3. **Query Mode**: Supports `cartographer query` with 4 tools:
   - `find_implementation(concept)`
   - `trace_lineage(dataset, direction)`
   - `blast_radius(module_path)`
   - `explain_module(path)`
4. **Evidence**: Every answer cites file:line + analysis method + confidence
5. **Incremental**: Re-runs only changed files via `git diff`

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-03-10 | Initial spec created |
