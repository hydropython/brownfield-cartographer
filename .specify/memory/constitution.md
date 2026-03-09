# Brownfield Cartographer  Project Constitution

## Project Identity
- **Name:** Brownfield Cartographer
- **Purpose:** Build a deployable codebase intelligence system for Forward-Deployed Engineer (FDE) onboarding
- **Target Users:** FDEs working in data engineering environments with unfamiliar production codebases
- **Success Metric:** Answers all Five FDE Day-One Questions with evidence citations in <1 hour

---

## Non-Negotiable Principles (8 Rules)

### Rule 1: No Hallucinated Code
Every code snippet must be:
- Syntactically valid
- Dependency-checked against current library docs
- Minimal and testable before scaling

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

Distinguish static analysis () from LLM inference ().

### Rule 4: Graceful Degradation
If a file cannot be parsed:
- Log a warning to `cartography_trace.jsonl`
- Continue processing remaining files
- Never crash the entire pipeline

Handle dynamic references (f-strings, variables) by flagging as "unresolved"  never guess.

### Rule 5: Security First
Never send client code to an LLM without scanning for secrets first.

Requirements:
- Use `detect-secrets` or regex patterns to redact before LLM ingestion
- Log all redactions in `cartography_trace.jsonl`
- Never store secrets in output artifacts

### Rule 6: Cost Awareness
Track LLM token usage throughout analysis.

Model Selection Policy:
- Bulk tasks (purpose statements): Gemini Flash / Mistral (cheap)
- Synthesis tasks (Day-One answers): Claude / GPT-4 (expensive)
- Budget alert at 50% of estimated token limit

### Rule 7: Incremental Delivery
**Thursday Interim:** Surveyor + Hydrologist (structure + lineage)  
**Sunday Final:** Semanticist + Navigator + Frontend (full pipeline)

Never block delivery on stretch goals. Ship working core first.

### Rule 8: User Control
Always ask for explicit confirmation before proceeding to next phase.

If the user expresses doubt:
1. Pause immediately
2. Diagnose root cause
3. Propose verification step
4. Wait for explicit approval to continue

---

## Technical Constraints

| Constraint | Value |
|------------|-------|
| Python Version | 3.10+ |
| Dependency Manager | `uv` |
| AST Parser | `tree-sitter` (Python, SQL, YAML) |
| SQL Parser | `sqlglot` (Postgres, BigQuery, Snowflake, DuckDB) |
| Graph Library | `NetworkX` |
| Agent Orchestration | `LangGraph` |
| Vector Store | `faiss` or `chromadb` |
| Frontend | Zero-server (Cytoscape.js + Tailwind via CDN) |
| Knowledge Graph | Pydantic models + JSON serialization |

---

## Quality Gates

| Gate | Requirement |
|------|-------------|
| Code Length | No code longer than 50 lines without prior validation of smaller components |
| LLM Calls | All calls must track token budget and use tiered model selection |
| Error Handling | Graceful degradation on unparseable files (log + skip) |
| Testing | Each task must have verification checkpoint before proceeding |

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
