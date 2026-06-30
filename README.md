# Code Impact Predictor AI

Production-grade AI system that predicts the downstream impact of source code changes using **Graph Neural Networks**, **vector search**, and **LLM reasoning** — with strict separation between ML prediction and LLM explanation.

## What It Predicts

Given a Git diff or Pull Request:

| Output | Method |
|--------|--------|
| Files likely to break | GNN node classification |
| Affected services | Graph traversal + GNN |
| Risk score (0–100) | GNN regression head |
| Regression probability | GNN binary head |
| Confidence score | Ensemble variance |
| Suggested reviewers | Ownership graph + ML ranking |
| Similar historical commits | Qdrant vector search |
| Root cause explanation | LLM (not prediction) |
| Why files are predicted | SHAP + attention + LLM |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI API │────▶│  Celery Workers │
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                       │
                    ┌──────▼───────┐     ┌─────────▼─────────┐
                    │  PostgreSQL  │     │  ML Pipeline      │
                    └──────────────┘     │  GNN + Embeddings │
                                         └─────────┬─────────┘
                           ┌─────────────┐         │
                           │   Qdrant    │◀────────┘
                           └─────────────┘
```

See [docs/architecture/](docs/architecture/) for full system design.

## Tech Stack

- **Backend**: Python, FastAPI, Celery, Redis
- **ML**: PyTorch, PyTorch Geometric, Sentence Transformers
- **Vector DB**: Qdrant
- **Database**: PostgreSQL
- **LLM**: OpenAI / Claude (explanation only)
- **Monitoring**: Prometheus, Grafana
- **Deploy**: Docker Compose

## Quick Start

```bash
# Clone and configure
cp .env.example .env

# Start all services
docker compose up -d

# API available at
open http://localhost:8000/api/v1/docs

# Grafana at http://localhost:3000 (admin/admin)
# Prometheus at http://localhost:9090
```

## Project Structure

```
ImpactAI/
├── docs/architecture/          # System design documents
├── src/code_impact/
│   ├── domain/                 # Entities, value objects, interfaces (DDD)
│   ├── application/            # Use cases, schemas (CQRS)
│   ├── infrastructure/         # DB, queue, config, ML adapters
│   └── presentation/           # FastAPI routes
├── tests/
│   ├── unit/
│   └── integration/
├── alembic/                    # Database migrations
├── docker/                     # Dockerfile, Prometheus, Grafana
├── docker-compose.yml
└── pyproject.toml
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/unit/ -v

# Run API locally
export SECRET_KEY="dev-secret-key-minimum-32-characters"
export DATABASE_URL="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/1"
export CELERY_RESULT_BACKEND="redis://localhost:6379/2"
uvicorn code_impact.presentation.api.main:app --reload
```

## Build Roadmap

| Step | Status | Focus |
|------|--------|-------|
| 1 | ✅ | Foundation: Architecture, Domain, Infrastructure |
| 2 | ✅ | Git Service, Diff Parser, AST Analyzer |
| 3 | ✅ | Dependency Graph Builder |
| 4 | ✅ | Vector Embedding Service + Qdrant |
| 5 | 🔲 | GNN Model + Training Pipeline |
| 6 | 🔲 | Risk Prediction + Reviewer Recommender |
| 7 | 🔲 | LLM Reasoning + Explanation Layer |
| 8 | 🔲 | REST API (full endpoints) |
| 9 | 🔲 | React Frontend + Visualizations |
| 10 | 🔲 | XAI (SHAP, Attention) |
| 11 | 🔲 | Evaluation Framework |
| 12 | 🔲 | CI/CD, Monitoring, Production Hardening |

## License

MIT
