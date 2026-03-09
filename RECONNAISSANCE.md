# RECONNAISSANCE.md

## Target Repository Information
| Field | Value |
|-------|-------|
| **Repo Name** | jaffle_shop |
| **Source** | https://github.com/dbt-labs/jaffle_shop |
| **Clone Path** | targets/jaffle_shop |
| **Date** | 2025-03-10 |
| **Analyst** | [Your Name] |
| **Time Spent** | [fill after TASK-005] |

---

## Repo Characteristics
| Characteristic | Value |
|----------------|-------|
| **Total Files** | [count] |
| **Python Files** | [count] |
| **SQL Files** | [count] |
| **YAML Files** | [count] |
| **Notebooks** | [count] |
| **Primary Language** | [e.g., SQL + Python] |
| **Framework** | [e.g., dbt, Airflow, custom] |

---

## 1. Primary Data Ingestion Path
**Answer**: [fill after TASK-005]

**Evidence**:
- File: `[path]:[line]`
- Snippet: `[relevant code]`

**Confidence**: [High/Medium/Low]
**Difficulty**: [What was hard to find?]

---

## 2. Critical Output Datasets/Endpoints (3-5)
| Output | Purpose | Evidence Location | Confidence |
|--------|---------|------------------|------------|
| [name] | [why critical] | `[file]:[line]` | [H/M/L] |

---

## 3. Blast Radius of [Critical Module]
**Module**: `[path/to/module]`

**Direct Dependents**: [list]
**Indirect Dependents**: [list]
**Critical Path Impact**: [what breaks?]

**Evidence**: [grep results / import trace]

---

## 4. Business Logic Distribution
**Concentrated in**: [directories/modules]
**Distributed in**: [scattered locations]
**Observations**: [duplication? inconsistency?]

---

## 5. Git Velocity Map (Top 10 Files, 90 Days)
| File | Commit Count | Interpretation |
|------|-------------|----------------|
| `[path/file]` | [count] | [notes] |

---

## Manual Analysis Difficulty Assessment
- **Easiest question to answer**: [#] because...
- **Hardest question to answer**: [#] because...
- **Where I got lost**: [specific confusion]
- **What I wish I had**: [tooling gap this project should fill]

---

## Notes for Future Targets
This reconnaissance template is designed for ANY target repo.
To analyze a different repo:
1. Clone to `targets/<repo-name>/`
2. Copy this file to `RECONNAISSANCE-<repo-name>.md`
3. Fill in the template manually (TASK-005)
4. Compare Cartographer output against this baseline
