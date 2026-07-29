# AI Code Review Agent

An AI-powered full-stack code review application that analyzes GitHub repositories, identifies code-quality and security issues, and generates structured repository-level insights.

The application uses a locally hosted LLM through Ollama, allowing code analysis without sending source code to an external AI service.

## Features

- Analyze public GitHub repositories
- AI-powered source code review
- Repository health score
- Critical, high, medium, and low severity classification
- File-level code findings
- Repository-level AI summary
- Risk identification
- Improvement recommendations
- Concurrent multi-file analysis
- GitHub repository cloning and scanning
- React dashboard
- FastAPI REST API
- Local LLM integration with Ollama
- Docker and Docker Compose support
- Automated backend and frontend testing
- GitHub Actions CI pipelines

## Architecture

```text
                    User
                      |
                      v
              React Dashboard
                      |
                      | HTTP / REST
                      v
                FastAPI API
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Repository Scanner         AI Review Service
          |                       |
          |                       v
          |                 Ollama API
          |                       |
          |                       v
          |               Qwen2.5-Coder 7B
          |
          v
 GitHub Repository
```

## Repository Analysis Flow

```text
GitHub Repository URL
        |
        v
Validate Repository URL
        |
        v
Clone Repository
        |
        v
Scan Supported Source Files
        |
        v
Select Files for Analysis
        |
        v
Concurrent AI Code Reviews
        |
        v
Structured Issue Detection
        |
        +----> Severity Counts
        |
        +----> File-Level Findings
        |
        v
Repository-Level AI Summary
        |
        v
Health Score + Risks + Recommendations
        |
        v
React Dashboard
```

## Technology Stack

### Backend

- Python 3.13
- FastAPI
- Pydantic
- AsyncIO
- Ollama Python Client
- Pytest
- Ruff

### AI

- Ollama
- Qwen2.5-Coder 7B
- Structured JSON responses
- Repository-level summarization

### Frontend

- React
- Vite
- JavaScript
- CSS

### DevOps

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Git

## Project Structure

```text
ai-code-review-agent/
|
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- main.py
|   |
|   |-- tests/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- .env.example
|
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- App.css
|   |   `-- main.jsx
|   |
|   |-- Dockerfile
|   |-- package.json
|   `-- .env.example
|
|-- .github/
|   `-- workflows/
|       |-- backend-ci.yml
|       |-- frontend-ci.yml
|       `-- docker-ci.yml
|
|-- docker-compose.yml
`-- README.md
```

## Running Locally

### Prerequisites

Install:

- Python 3.13+
- Node.js
- Git
- Ollama

Pull the AI model:

```bash
ollama pull qwen2.5-coder:7b
```

Verify Ollama:

```bash
curl http://localhost:11434/api/tags
```

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

fastapi dev app/main.py
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Running with Docker

Make sure Docker Desktop and Ollama are running.

Then:

```bash
docker compose build
docker compose up
```

Open:

```text
Frontend: http://localhost:3000
Backend:  http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
```

The Dockerized backend communicates with the locally running Ollama service through `host.docker.internal`.

## Environment Configuration

Backend:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
MAX_REPOSITORY_FILES=10
MAX_CONCURRENT_REVIEWS=3
FRONTEND_URL=http://localhost:5173
```

Frontend:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Use the included `.env.example` files as templates.

Do not commit real `.env` files or secrets.

## Testing

Backend:

```bash
cd backend

ruff check app tests
pytest -v
```

Frontend:

```bash
cd frontend

npm run lint
npm run build
```

## CI/CD

GitHub Actions automatically validates the project on pushes and pull requests to `main`.

### Backend CI

- Install Python dependencies
- Ruff code-quality checks
- Pytest automated tests

### Frontend CI

- Install npm dependencies
- Frontend linting
- Production React build

### Docker CI

- Build FastAPI Docker image
- Build React/Nginx Docker image

## API

### Health Check

```text
GET /health
```

### Repository Review

```text
POST /api/repositories/review
```

Example request:

```json
{
  "repository_url": "https://github.com/username/repository"
}
```

The API returns structured repository analysis including file findings, severity information, repository summary, and recommendations.

## Current Status

The application currently supports:

- Local AI inference
- Public GitHub repository analysis
- Concurrent source-file review
- Structured AI findings
- Repository-level analysis
- Full-stack dashboard
- Dockerized execution
- Automated CI validation

## Future Improvements

Potential future enhancements include:

- GitHub OAuth
- Private repository support
- Pull-request review integration
- Review history
- Database persistence
- Additional programming-language support
- Cloud deployment
- Automated PR comments
- Configurable AI models
- Expanded security scanning

## Development Workflow

This project follows a branch-based development workflow:

1. Create a feature branch from `main`.
2. Implement and test changes locally.
3. Push the feature branch to GitHub.
4. Open a pull request into `main`.
5. GitHub Actions runs backend, frontend, and Docker CI checks.
6. Merge the pull request after all required checks pass.

## Author

Built as a full-stack AI engineering project demonstrating practical experience with AI integration, backend development, frontend development, testing, Docker, and CI/CD.