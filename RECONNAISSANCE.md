# RECONNAISSANCE.md

## Target Repository Information
| Field | Value |
|-------|-------|
| **Repo Name** | jaffle_shop |
| **Source** | https://github.com/dbt-labs/jaffle_shop |
| **Clone Path** | targets/jaffle_shop |
| **Date** | 2025-03-10 |
| **Analyst** | kIDIST d. |
| **Time Spent** | 20 minutes |

---

## Repo Characteristics
| Characteristic | Value |
|----------------|-------|
| **Total Files** | 19 |
| **Python Files** | 0 |
| **SQL Files** | 5 |
| **YAML Files** | 3 |
| **Notebooks** | 0 |
| **Primary Language** | SQL |
| **Framework** | dbt |

---

## Five FDE Day-One Questions — Answers

### Question 1: What is the primary data ingestion path?

**Answer**: Data enters via CSV seed files (seeds/*.csv). dbt automatically loads seeds as tables (configured via seed-paths: ["seeds"] in dbt_project.yml). Staging models read from seeds, and final models read from staging.

**Evidence**:
- Seed files: seeds/raw_customers.csv, seeds/raw_orders.csv, seeds/raw_payments.csv
- Config: dbt_project.yml declares seed-paths: ["seeds"]
- Data flow: seeds/raw_*.csv -> models/staging/stg_*.sql -> models/customers.sql, orders.sql
- Final model pattern (models/customers.sql:3): select * from {{ ref('stg_customers') }}

**Confidence**: High (explicit dbt convention + verified SQL patterns)
**Difficulty**: Moderate - required understanding dbt seed convention vs. explicit sources declaration

---

### Question 2: What are the 3-5 most critical output datasets/endpoints?

**Answer**: The two critical output models are customers and orders, both located in models/ directory.

| Output | Purpose | Evidence Location | Confidence |
|--------|---------|------------------|------------|
| customers | Core customer dimension with derived metrics (first_order, lifetime_value) | models/customers.sql + models/schema.yml docs | High |
| orders | Order facts with payment type breakdown | models/orders.sql + models/schema.yml docs | High |

**Evidence Notes**:
- models/schema.yml documents both models with full column specs + tests
- Both are terminal nodes (no downstream ref() calls in SQL files)
- Small repo: only 2 final output models

---

### Question 3: What is the blast radius if the most critical module fails?

**Module**: models/customers.sql

**Answer**: If customers.sql fails or its schema changes, the orders model's relationship test would fail, and any downstream BI tool or dashboard depending on customer dimensions would break.

**Direct Dependents**: 
- models/orders.sql has a test dependency via models/schema.yml

**Indirect Dependents**: 
- Any BI tool or dashboard querying customers or orders

**Critical Path Impact**:
- If customers schema changes (e.g., remove customer_id):
  1. orders model relationship test would fail
  2. Any downstream dashboard using customer dimensions would break
  3. Customer lifetime value calculations would be unavailable

**Evidence**:
- models/schema.yml line ~38: orders.customer_id has relationships test to ref('customers')
- models/customers.sql contains business logic: customer_lifetime_value, first_order, number_of_orders

**Confidence**: High (explicit YAML test declaration + SQL review)

---

### Question 4: Where is the business logic concentrated vs. distributed?

**Answer**: Business logic is concentrated in the final models (customers.sql, orders.sql), while staging models perform only light transformation.

**Concentrated in**:
- models/customers.sql - Customer aggregations:
  - first_order (MIN of order_date)
  - most_recent_order (MAX of order_date)
  - number_of_orders (COUNT)
  - customer_lifetime_value (SUM of payments via JOIN)
- models/orders.sql - Order aggregations by payment type
- models/schema.yml - Declarative tests + documentation

**Distributed in**:
- models/staging/*.sql - Light transformation (renaming, type casting only)
- Minimal distribution; clean dbt architecture

**Observations**:
- Staging layer does minimal transformation (SELECT * with renaming)
- Final models contain ALL business logic (aggregations, derived metrics)
- Tests are declarative in YAML (not code)
- No Python business logic
- No duplication detected
- Clear separation: staging (raw to clean) -> marts (clean to metrics)

**Confidence**: High (small codebase fully auditable)

---

### Question 5: What has changed most frequently in the last 90 days (git velocity map)?

**Answer**: This is a tutorial/example repo with limited recent activity. In a production repo, git velocity would reveal active development areas.

| File | Commit Count | Interpretation |
|------|-------------|----------------|
| models/customers.sql | Tutorial repo (limited history) | Core model, likely stable |
| models/schema.yml | Tutorial repo (limited history) | Config + tests, stable |
| seeds/raw_customers.csv | Tutorial repo (limited history) | Static test data |

**Note**: This is a tutorial/example repo with limited recent activity. In a production repo, git velocity would reveal active development areas.

**Confidence**: Low (tutorial repo not representative of production velocity)

---

## Manual Analysis Difficulty Assessment

- **Easiest question to answer**: #2 (Critical Outputs) because models/schema.yml explicitly documents customers and orders as the final models with full column specs and tests.
- **Hardest question to answer**: #1 (Ingestion Path) because this version lacks explicit sources: declarations; had to understand dbt seed convention via dbt_project.yml.
- **Where I got lost**: Initially looked for sources: in schema.yml; discovered seeds are loaded implicitly via seed-paths config.
- **What I wish I had**: 
  - A tool that auto-discovers dbt patterns (seeds vs. sources vs. external tables)
  - Visual DAG showing seed to staging to marts flow without running dbt docs generate
  - One-command lineage trace from any model to its ultimate sources
  - Automatic blast radius calculation showing test dependencies + SQL dependencies

---

## Key Insights for Cartographer Design

1. **Must handle multiple dbt patterns**: Some projects use sources:, others use seeds implicitly
2. **Test dependencies matter**: schema.yml relationships tests create implicit dependencies
3. **Staging vs. marts distinction**: Clear architectural pattern that should be auto-detected
4. **Business logic concentration**: Final models contain aggregations; staging is light transformation
5. **Evidence format**: File:line citations are critical (e.g., models/customers.sql:3)

---

## Notes for Future Targets

This reconnaissance template is designed for ANY target repo.
To analyze a different repo:
1. Clone to targets/<repo-name>/
2. Copy this file to RECONNAISSANCE-<repo-name>.md
3. Fill in the template manually (TASK-005)
4. Compare Cartographer output against this baseline

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2025-03-10 | Initial reconnaissance completed for jaffle_shop |