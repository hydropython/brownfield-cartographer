# Brownfield Cartographer  Task Breakdown

## Overview
This document breaks the implementation into 29 small, testable tasks. Each task must be verified complete before proceeding to the next.

---

## Setup Phase (Spec Kit)

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-000 | Initialize Spec Kit Constitution | .specify/memory/constitution.md | File exists + 8 rules present |
| TASK-001 | Generate Product Specification | specs/001-brownfield-cartographer/spec.md | File exists + user journeys defined |
| TASK-002 | Generate Technical Plan | specs/001-brownfield-cartographer/plan.md | File exists + tech stack documented |
| TASK-003 | Generate Task Breakdown | specs/001-brownfield-cartographer/tasks.md | File exists + all 29 tasks listed |

---

## Phase 0: Reconnaissance (Manual Baseline)

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-004 | Select Target Repository | RECONNAISSANCE.md (repo selected) | Repo cloned + has 50+ files |
| TASK-005 | Manual Day-One Analysis | RECONNAISSANCE.md (complete) | All 5 questions answered with evidence |

---

## Phase 1: Surveyor Agent (Static Structure)

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-006 | Project Setup & Dependencies | pyproject.toml + src/ structure | uv install succeeds + tree-sitter parses test file |
| TASK-007 | Pydantic Models (Nodes) | src/models/nodes.py | All 4 node types validate with test data |
| TASK-008 | Pydantic Models (Edges + Graph) | src/models/edges.py, src/models/graph.py | Graph serializes to JSON correctly |
| TASK-009 | Tree-Sitter Analyzer | src/analyzers/tree_sitter_analyzer.py | Parses test Python file + extracts functions |
| TASK-010 | Surveyor Agent Core | src/agents/surveyor.py + module_graph.json | Graph has nodes + edges + PageRank computed |

---

## Phase 2: Hydrologist Agent (Data Lineage)

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-011 | SQL Lineage Analyzer | src/analyzers/sql_lineage.py | Parses test SQL + extracts FROM/JOIN tables |
| TASK-012 | DAG Config Parser | src/analyzers/dag_config_parser.py | Parses test YAML + extracts pipeline topology |
| TASK-013 | Hydrologist Agent Core | src/agents/hydrologist.py + lineage_graph.json | Lineage graph matches dbt manifest |

---

## Phase 3: Semanticist Agent (LLM-Powered)

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-014 | Security Scanner | src/agents/security_scanner.py | Detects test secrets + redacts correctly |
| TASK-015 | Purpose Statement Generation | src/agents/semanticist.py (part 1) | Purpose statements generated for test modules |
| TASK-016 | Domain Clustering | src/agents/semanticist.py (part 2) | Clusters match expected domain boundaries |

---

## Phase 4: Archivist + Navigator + Frontend

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-017 | Archivist (CODEBASE.md) | src/agents/archivist.py (part 1) | CODEBASE.md contains all required sections |
| TASK-018 | Archivist (Onboarding Brief) | src/agents/archivist.py (part 2) | onboarding_brief.md answers all 5 Day-One Questions |
| TASK-019 | Navigator Tool 1 (find_implementation) | src/agents/tools/find_implementation.py | Returns correct modules for test queries |
| TASK-020 | Navigator Tool 2 (trace_lineage) | src/agents/tools/trace_lineage.py | Returns correct lineage paths |
| TASK-021 | Navigator Tool 3 (blast_radius) | src/agents/tools/blast_radius.py | Returns correct downstream dependents |
| TASK-022 | Navigator Tool 4 (explain_module) | src/agents/tools/explain_module.py | Returns accurate module explanations |
| TASK-023 | Navigator Agent (LangGraph) | src/agents/navigator.py | All 4 tools accessible via query mode |
| TASK-024 | Frontend Generator | src/frontend/template.html + index.html | Graph renders in browser + search works |
| TASK-025 | CLI Entry Point | src/cli.py | analyze + query commands work end-to-end |
| TASK-026 | Incremental Update Mode | src/orchestrator.py (extension) | Only changed files re-analyzed on re-run |

---

## Validation + Documentation

| Task ID | Name | Deliverable | Verification |
|---------|------|-------------|--------------|
| TASK-027 | Accuracy Report | validation_report.md | Manual vs. Auto comparison for all 5 questions |
| TASK-028 | README.md | README.md | Installation + usage documented |
| TASK-029 | Demo Preparation | Video script + test repos | All 6 demo steps verified |

---

## Task Execution Rules

1. **One task at a time**: Do not start TASK-N+1 until TASK-N is verified complete
2. **Verification required**: Each task has a checkpoint that must pass before moving on
3. **No code without structure**: Every file must match the architecture directory structure
4. **Constitution rules apply**: All 8 guardrail rules enforced for every task
5. **Git commit per task**: Each completed task is committed with task reference

---

## Progress Tracking

| Phase | Tasks | Status |
|-------|-------|--------|
| Setup | TASK-000 to TASK-003 | In Progress |
| Phase 0 | TASK-004 to TASK-005 | Pending |
| Phase 1 | TASK-006 to TASK-010 | Pending |
| Phase 2 | TASK-011 to TASK-013 | Pending |
| Phase 3 | TASK-014 to TASK-016 | Pending |
| Phase 4 | TASK-017 to TASK-026 | Pending |
| Validation | TASK-027 to TASK-029 | Pending |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-03-10 | Initial task breakdown created |
