# 🗺️ Brownfield Cartographer

![Brownfield Cartographer](https://img.shields.io/badge/Brownfield-Cartographer-2c3e50?style=for-the-badge&logo=project-diagram&logoColor=white)

*Automated codebase intelligence for brownfield projects.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📦 Used Packages

| Package | Purpose |
|---------|---------|
| fastapi, uvicorn | Web API server |
| pydantic | Data validation |
| networkx | Graph algorithms |
| sqlglot | SQL parsing |
| pyyaml | YAML parsing |
| tree-sitter | AST parsing |
| cytoscape.js | Graph visualization |
| chart.js | Statistics charts |

---

##  Models

### Node Types

- **ModuleNode** - Code files with imports, exports, git velocity
- **DatasetNode** - Data tables with schema, ownership, freshness
- **FunctionNode** - Functions with signatures, call counts
- **TransformationNode** - Data transformations with source/target

### Edge Types

- **IMPORTS** - Module imports another module
- **PRODUCES** - Transformation creates dataset
- **CONSUMES** - Transformation uses dataset
- **CALLS** - Function calls another function
- **CONFIGURES** - Config file affects module
- **DBT_REF** - dbt ref() dependency
- **DEPENDS_ON** - SQL FROM/JOIN dependency
- **TESTS** - Test applied to model/column
- **RELATIONSHIP** - Foreign key relationship

---

## 🎯 What It Does

Brownfield Cartographer automatically analyzes existing codebases to create:

1. **Module Dependency Graphs** (Agent 1: Surveyor)
2. **Data Lineage Maps** (Agent 2: Hydrologist)
3. **Semantic Understanding** (Agent 3: Semanticist - coming soon)
4. **Documentation Generation** (Agent 4: Archivist - coming soon)
5. **Natural Language Query** (Agent 5: Navigator - coming soon)

### Use Cases

- Onboarding to legacy codebases
- Impact analysis before refactoring
- Architecture documentation
- Knowledge transfer
- Dead code detection

---
## Quick Start

### Installation
```
git clone https://github.com/your-org/brownfield-cartographer.git
cd brownfield-cartographer
python -m venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

### Run the Dashboard
```
uv run uvicorn backend.api:app --host 127.0.0.1 --port 8002
```

### Open Browser
```

Navigate to: http://127.0.0.1:8002
```

### Analyze Your Codebase
```
from pathlib import Path
from src.agents.surveyor import SurveyorAgent
from src.agents.hydrologist import HydrologistAgent

surveyor = SurveyorAgent(repo_path=Path("path/to/your/repo"))
graph = surveyor.run()
print(f"Found {graph.total_nodes} modules, {graph.total_edges} dependencies")

hydrologist = HydrologistAgent(repo_path=Path("path/to/your/repo"))
lineage_graph = hydrologist.run()
print(f"Found {lineage_graph.number_of_nodes()} nodes, {lineage_graph.number_of_edges()} edges")

```
## Agents

### Agent 1: Surveyor

Extracts module dependencies, imports, exports, and architectural hubs.

#### Node Types

- Module (Dark Blue) - Code files (.sql, .py, .yml)
- YAML (Blue) - Configuration files
- External (Gray, dashed) - Synthetic nodes for unresolved dependencies

#### Edge Types

- IMPORTS - Module imports another module

### Agent 2: Hydrologist

Extracts data lineage from SQL, YAML, and dbt patterns.

#### Node Types

- Seed (Green) - Physical data files (CSV, Parquet)
- Staging (Blue) - Light transformation models
- Mart (Gold) - Business logic models (hubs)
- Test (Red) - YAML tests (not_null, unique, etc.)

#### Edge Types

- DBT_REF - dbt ref() call
- DEPENDS_ON - SQL FROM/JOIN dependency
- TESTS - Test applied to column/model
- RELATIONSHIP - Foreign key relationship

## API Endpoints

### Base URL

http://127.0.0.1:8002

### Available Endpoints

- GET / - Serve frontend dashboard
- GET /api/agents - List all agents with stats
- GET /api/agent/surveyor/graph - Surveyor graph (Cytoscape.js)
- GET /api/agent/hydrologist/graph - Hydrologist graph (Cytoscape.js)
- GET /api/agent/hydrologist/edge-breakdown - Edge type distribution
- GET /api/agent/hydrologist/blast-radius - Blast radius analysis
- GET /api/agent/surveyor/hubs - Top architectural hubs
- GET /api/export/graph/{agent}/json - Export as NetworkX JSON

### Example Response

{"name": "Hydrologist", "nodes": 31, "edges": 37, "confidence_high": 29, "confidence_medium": 8}

## Project Structure
```
brownfield-cartographer/
├── backend/api.py
├── frontend/index.html
├── frontend/css/styles.css
├── frontend/js/app.js
├── src/agents/surveyor.py
├── src/agents/hydrologist.py
├── targets/jaffle_shop/
└── README.md
```

## Known Limitations

### Surveyor Agent

- Ghost nodes shown as gray dashed (synthetic, not real files)
- No tree-sitter parsing yet (uses basic AST)
- Limited edge types (only IMPORTS implemented)
- Git velocity analysis not yet integrated

### Hydrologist Agent

- Column lineage basic extraction (may miss complex SQL)
- dbt macros not expanded (hidden dependencies)
- Dynamic Jinja refs not detected

### General

- Static analysis only (no runtime validation)
- No LLM integration yet
- No vector store for semantic search

## Roadmap

### Phase 1: Surveyor (Current - Alpha)

- Module dependency extraction
- PageRank hub detection
- Circular dependency detection

### Phase 2: Hydrologist (Current - Beta)

- SQL dependency extraction
- dbt ref() detection
- Confidence scoring
- Blast radius analysis

### Phase 3: Semanticist (Planned)

- LLM integration
- Purpose statement generation
- Domain clustering

### Phase 4: Archivist (Planned)

- Documentation generation
- Architecture decision records

### Phase 5: Navigator (Planned)

- Natural language query
- Vector store integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License

## Acknowledgments

- dbt Labs - for the jaffle_shop example project
- NetworkX - for graph algorithms
- Cytoscape.js - for graph visualization
- FastAPI - for the web framework
- Chart.js - for statistics charts

## Support

- Bug Reports: GitHub Issues
- Discussions: GitHub Discussions
- Email: your.email@example.com

---

Built with ❤️ for brownfield developers everywhere.

Version 0.1.0 - March 2026