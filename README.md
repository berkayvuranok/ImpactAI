# Code Impact Predictor AI

Production-grade AI system that predicts the downstream impact of source code changes using **Graph Neural Networks**, **vector search**, and **LLM reasoning**.

```mermaid
flowchart LR
    DIFF[Git Diff / PR] --> SYS[Code Impact Predictor AI]
    SYS --> ML[GNN + Classical ML]
    SYS --> VEC[Vector Search]
    SYS --> LLM[LLM Reasoning]
    ML -->|predicts| NUM[Risk · Regression · Files]
    LLM -->|explains only| TXT[Root Cause · Rationale]
```

---

## What It Predicts

```mermaid
flowchart TB
    IN([Git Diff / Pull Request])

    IN --> F1[Files likely to break]
    IN --> F2[Affected services]
    IN --> F3[Risk score 0–100]
    IN --> F4[Regression probability]
    IN --> F5[Confidence score]
    IN --> F6[Suggested reviewers]
    IN --> F7[Similar historical commits]
    IN --> F8[Root cause explanation]
    IN --> F9[Why files are predicted]

    F1 -.- M1[GNN node classification]
    F2 -.- M2[Graph traversal + GNN]
    F3 -.- M3[GNN regression head]
    F4 -.- M4[GNN binary head]
    F5 -.- M5[Ensemble variance]
    F6 -.- M6[Ownership graph + ML ranking]
    F7 -.- M7[Qdrant vector search]
    F8 -.- M8[LLM — not prediction]
    F9 -.- M9[SHAP + attention + LLM]

    style M8 fill:#f9f,stroke:#333
    style M9 fill:#f9f,stroke:#333
```

```mermaid
flowchart LR
    subgraph Prediction["🔢 ML Prediction"]
        GNN[GNN]
        CLF[Classical ML]
        ENS[Ensemble]
    end
    subgraph Explanation["💬 LLM Explanation"]
        EXP[Explanation Generator]
        XAI[SHAP / Attention]
    end
    GNN --> ENS
    CLF --> ENS
    ENS --> XAI --> EXP
```

---

## Architecture

> Detay: [`docs/architecture/`](docs/architecture/)

### Deployment

```mermaid
flowchart TB
    subgraph Clients
        FE[React Dashboard]
        CLI[CLI / CI Plugin]
        WH[GitHub · GitLab Webhook]
    end

    subgraph Gateway["Traefik :80"]
        TR[Reverse Proxy]
        RL[Rate Limiter]
    end

    subgraph App
        API[FastAPI :8000]
        WK[Celery Worker]
    end

    subgraph Storage
        PG[(PostgreSQL :5432)]
        RD[(Redis :6379)]
        QD[(Qdrant :6333)]
        GV[/Graph JSON /data/graphs/]
        RV[/Git Repos /data/repos/]
        MV[/Models /app/models/]
    end

    subgraph Obs["Observability"]
        PR[Prometheus :9090]
        GR[Grafana :3000]
    end

    FE & CLI & WH --> TR --> RL --> API
    API --> WK & PG
    WK --> RD & PG & QD & GV & RV & MV
    API & WK --> PR --> GR
```

### System Overview

```mermaid
flowchart TB
    subgraph Client
        UI[React]
        CI[CLI / CI]
        GH[Webhooks]
    end

    subgraph Gateway
        GW[Traefik]
        AU[JWT + OAuth2]
    end

    subgraph Services
        API[FastAPI]
        CW[Celery Workers]
    end

    subgraph Analysis
        GIT[Git Service]
        DF[Diff Parser]
        AS[AST Analyzer]
        GB[Graph Builder]
        FE[Feature Engineering]
    end

    subgraph ML
        EM[Embeddings]
        GN[GNN]
        RK[Risk Model]
        HS[Historical Search]
        RV[Reviewer Recommender]
    end

    subgraph Reasoning
        LM[LLM Service]
        EX[Explanation]
        XA[XAI]
    end

    subgraph Data
        PG[(PostgreSQL)]
        RE[(Redis)]
        QT[(Qdrant)]
        GS[Git Storage]
    end

    UI & CI & GH --> GW --> AU --> API
    API --> CW
    CW --> GIT --> DF --> AS --> GB --> FE
    FE --> EM --> GN --> RK
    FE --> HS
    RK --> RV
    GN --> XA
    RK --> LM --> EX
    EM & HS --> QT
    API --> PG
    CW --> RE
    GIT --> GS
```

### Clean Architecture

```mermaid
flowchart TB
    subgraph PRES["presentation/"]
        RT[Routes]
        DI[Dependencies]
    end

    subgraph APP["application/"]
        UC[Use Cases]
        SV[Services]
    end

    subgraph DOM["domain/"]
        EN[Entities]
        VO[Value Objects]
        IF[Interfaces / Ports]
    end

    subgraph INF["infrastructure/"]
        DB[PostgreSQL Repos]
        GT[Git · Diff · AST · Graph]
        VQ[Embeddings · Qdrant]
        CQ[Celery · Config]
    end

    subgraph MLAY["ml/"]
        MD[CodeImpactGNN]
        FT[Features · Tensors]
        TR[Training · Registry]
        IFR[Inference]
    end

    RT --> UC --> IF
    SV --> IF
    DB & GT & VQ & IFR -.-> IF
    CQ --> GT & VQ
    TR --> MD
    IFR --> MD
```

### Bounded Contexts

```mermaid
flowchart LR
    IC[Identity<br/>Users · Roles · Tokens]
    RC[Repository<br/>Repos · Commits · PRs · Sync]
    AC[Analysis<br/>Diffs · AST · Complexity]
    GC[Graph<br/>Nodes · Edges · Snapshots]
    KC[Knowledge<br/>Embeddings · Issues · Similarity]
    PC[Prediction<br/>Risk · Files · Confidence]

    RC --> AC --> GC --> PC
    KC --> PC
```

### Database

```mermaid
erDiagram
    users ||--o{ repositories : owns
    users ||--o{ predictions : creates
    users ||--o{ reviewer_profiles : has
    repositories ||--o{ commits : contains
    repositories ||--o{ pull_requests : contains
    repositories ||--o{ graph_snapshots : has
    repositories ||--o{ sync_jobs : has
    repositories ||--o{ embeddings : has
    pull_requests ||--o{ predictions : triggers
    predictions ||--o{ affected_file_predictions : has
    predictions ||--o{ similar_commits : has
    graph_snapshots ||--o{ graph_nodes : contains
    graph_snapshots ||--o{ graph_edges : contains
    commits ||--o| issues : fixes
    ml_models ||--o{ predictions : used_by

    users { uuid id PK string email string role }
    repositories { uuid id PK string url string provider }
    commits { uuid id PK string sha boolean is_regression }
    predictions { uuid id PK float risk_score string status }
    graph_snapshots { uuid id PK string commit_sha int node_count }
    graph_nodes { uuid id PK string node_type string file_path }
    graph_edges { uuid id PK string edge_type float weight }
    embeddings { uuid id PK string entity_type string qdrant_point_id }
    ml_models { uuid id PK string version string artifact_path boolean is_active }
```

### Celery Pipeline

```mermaid
flowchart LR
    SYNC[sync_repository_task] --> BUILD[build_graph_task]
    BUILD --> INDEX[index_embeddings_task]

    SYNC --> G1[Clone / Pull]
    SYNC --> G2[Persist Commits]

    BUILD --> G3[DependencyGraphBuilder]
    BUILD --> G4[Graph JSON]
    BUILD --> G5[(graph_snapshots)]

    INDEX --> G6[Sentence Transformer]
    INDEX --> G7[(Qdrant)]
    INDEX --> G8[(embeddings)]
```

### Offline Training

```mermaid
flowchart TD
    A[Git History] --> B[Label Extraction]
    B --> C[Feature Engineering]
    C --> D[Graph Construction]
    D --> E[Embeddings]
    E --> F[Dataset Assembly]
    F --> G[GNN Training]
    F --> H[Risk Classifier]
    G & H --> I[Evaluation]
    I --> J{OK?}
    J -->|No| K[Tuning]
    K --> G
    J -->|Yes| L[Model Registry]
    L --> M[Inference Deploy]
```

### Online Inference

```mermaid
flowchart LR
    IN[Diff] --> P1[Parse]
    P1 --> P2[AST]
    P2 --> P3[Graph]
    P3 --> P4[Node Features]
    P4 --> P5[GNN]
    P5 --> P6[Risk Head]
    P5 --> P7[Files Head]
    P4 --> P8[Qdrant Search]
    P6 & P7 & P8 --> P10[Ensemble]
    P10 --> P11[XAI]
    P11 --> P12[LLM Explain]
    P12 --> OUT[Response]
```

### Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant Q as Redis Queue
    participant W as Worker
    participant G as Git / Graph
    participant N as GNN
    participant D as Qdrant
    participant L as LLM
    participant B as PostgreSQL

    C->>A: POST /predict
    A->>B: prediction pending
    A->>Q: enqueue
    A-->>C: 202 prediction_id

    Q->>W: job
    W->>G: context + graph
    W->>N: inference
    W->>D: similar commits
    W->>L: explanation
    W->>B: store results

    C->>A: GET /prediction/id
    A->>B: fetch
    A-->>C: full result
```

### API Map

```mermaid
flowchart TB
    API["/api/v1"]

    API --> H[GET /health ✅]
    API --> REP[Repository ✅]
    API --> AN[Analyze ✅]
    API --> GR[Graph ✅]
    API --> EM[Embeddings ✅]
    API --> SR[Search ✅]
    API --> PR[Predict ✅]
    API --> PD[Prediction ✅]

    REP --> R1[POST /repository]
    REP --> R2[GET /repository/id]
    REP --> R3[POST /repository/id/sync]

    AN --> A1[POST /analyze/diff]

    GR --> G1[GET /graph/repo]
    GR --> G2[GET /graph/repo/sha]
    GR --> G3[GET /graph/repo/subgraph]
    GR --> G4[POST /graph/repo/build]

    EM --> E1[POST /embeddings/index/id]

    SR --> S1[POST /search/similar]
    SR --> S2[GET /search/similar/repo]

    PR --> P1[POST /predict]
    PD --> P2[GET /prediction/id]

    style H fill:#9f9
    style R1 fill:#9f9
    style R2 fill:#9f9
    style R3 fill:#9f9
    style A1 fill:#9f9
    style G1 fill:#9f9
    style G2 fill:#9f9
    style G3 fill:#9f9
    style G4 fill:#9f9
    style E1 fill:#9f9
    style S1 fill:#9f9
    style S2 fill:#9f9
    style P1 fill:#9f9
    style P2 fill:#9f9
```

### Tech Stack

```mermaid
flowchart TB
    subgraph Backend
        PY[Python 3.11+]
        FA[FastAPI]
        CE[Celery]
        RD[Redis]
    end

    subgraph ML
        PT[PyTorch]
        PYG[PyTorch Geometric]
        ST[Sentence Transformers]
        SK[scikit-learn]
    end

    subgraph Data
        PG[(PostgreSQL)]
        QD[(Qdrant)]
        GP[GitPython]
    end

    subgraph AI
        OAI[OpenAI]
        ANT[Claude]
    end

    subgraph Ops
        DK[Docker Compose]
        PM[Prometheus]
        GF[Grafana]
        TR[Traefik]
    end

    PY --> FA & CE & PT
    FA --> PG & RD
    CE --> RD
    PT --> PYG
    ST --> QD
    FA --> PM --> GF
    DK --> TR
```

### Project Structure

```mermaid
flowchart TB
    ROOT[ImpactAI/]

    ROOT --> DOC[docs/architecture/]
    ROOT --> SRC[src/code_impact/]
    ROOT --> TST[tests/]
    ROOT --> SCR[scripts/]
    ROOT --> ALB[alembic/]
    ROOT --> DKR[docker/]

    SRC --> DOM[domain/]
    SRC --> APP[application/]
    SRC --> INF[infrastructure/]
    SRC --> ML[ml/]
    SRC --> PRE[presentation/]

    DOM --> D1[entities · value_objects · interfaces]
    APP --> A1[use_cases · services · schemas]
    INF --> I1[git · analysis · graph · embeddings · persistence · queue]
    ML --> M1[models · features · training · inference · registry]
    PRE --> P1[api routes · dependencies]

    TST --> T1[unit/ · integration/ · support/]
```

### Build Roadmap

```mermaid
flowchart LR
    S1["1 ✅ Foundation"]
    S2["2 ✅ Git & Analysis"]
    S3["3 ✅ Dependency Graph"]
    S4["4 ✅ Embeddings + Qdrant"]
    S5["5 ✅ GNN Training"]
    S6["6 ✅ Risk + Reviewers"]
    S7["7 ✅ LLM Explanation"]
    S8["8 ✅ Full REST API"]
    S9["9 🔲 React Frontend"]
    S10["10 🔲 XAI"]
    S11["11 🔲 Evaluation"]
    S12["12 🔲 Production"]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10 --> S11 --> S12

    style S1 fill:#9f9
    style S2 fill:#9f9
    style S3 fill:#9f9
    style S4 fill:#9f9
    style S5 fill:#9f9
    style S6 fill:#fdd
    style S7 fill:#fdd
    style S8 fill:#fdd
    style S9 fill:#fdd
    style S10 fill:#fdd
    style S11 fill:#fdd
    style S12 fill:#fdd
```

---

## Quick Start

```bash
cp .env.example .env
docker compose up -d
open http://localhost:8000/api/v1/docs   # API
open http://localhost:3000               # Grafana (admin/admin)
open http://localhost:9090               # Prometheus
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v

export SECRET_KEY="dev-secret-key-minimum-32-characters"
export DATABASE_URL="postgresql+asyncpg://cip:cip_secret@localhost:5432/code_impact"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/1"
export CELERY_RESULT_BACKEND="redis://localhost:6379/2"
uvicorn code_impact.presentation.api.main:app --reload
```

## License

MIT
