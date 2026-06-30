# REST API Design

Base URL: `/api/v1`

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/refresh` | Refresh token |
| POST | `/auth/register` | User registration |

## Repositories

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/repository` | Register repository |
| GET | `/repository/{id}` | Get repository details |
| GET | `/repository` | List user repositories |
| POST | `/repository/{id}/sync` | Trigger sync job |
| DELETE | `/repository/{id}` | Remove repository |

## Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Submit diff for prediction (202 Accepted) |
| GET | `/prediction/{id}` | Get prediction result |
| GET | `/history/{repository_id}` | Prediction history |
| GET | `/risk/{repository_id}` | Risk summary & trends |

## Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph/{repository_id}` | Latest dependency graph |
| GET | `/graph/{repository_id}/{sha}` | Graph at specific commit |
| GET | `/graph/{repository_id}/subgraph` | Subgraph around changed files |

## Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/github` | GitHub PR push events |
| POST | `/webhooks/gitlab` | GitLab MR events |

## Response Codes

| Code | Usage |
|------|-------|
| 202 | Prediction/sync job accepted |
| 404 | Entity not found |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 501 | Not yet implemented (during build) |
