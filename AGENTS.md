# Repository Guidelines

## Project Structure & Module Organization
- `smart_agent/main.py`: FastAPI entrypoint; wires CORS and includes routers from `smart_agent/src`.
- `smart_agent/src/{routes,controllers,utils,config,validator}`: HTTP endpoints, business logic, helpers, and validation.
- `lambda_handler.py` and `smart_agent/lambda_handler.py`: AWS Lambda adapter (Mangum); loads config from AWS SSM Parameter Store, falls back to `.env` for local use.
- `scripts/package-lambda.py`: Builds `deployment.zip` for Lambda.
- `terraform/main.tf`: IaC for Lambda, API Gateway, SSM, and DynamoDB.
- `.env.sample`: Example local configuration. Do not commit real secrets.

## Build, Test, and Development Commands
- Install deps: `pip install -r smart_agent/requirements.txt`
- Run locally: `uvicorn smart_agent.main:app --reload`
- Package for Lambda: `python scripts/package-lambda.py` (outputs `deployment.zip`)
- Terraform (optional local IaC): `terraform -chdir=terraform init && terraform plan -var="function_name=<agent-name>" -var="s3_bucket=<bucket>" -var="s3_key=<key>" -var="environment=dev"`
- Run tests (if added): `LOCAL_RUN=1 pytest`

## Coding Style & Naming Conventions
- Python 3.11; follow PEP 8 with 4‑space indentation and type hints where practical.
- Files/modules: `snake_case`; classes: `PascalCase`; functions/variables: `snake_case`.
- Keep routes thin; put logic in `controllers` and helpers in `utils`.
- Environment variables are UPPER_SNAKE_CASE; SSM keys live under `/app/$AGENT_NAME`.

## Testing Guidelines
- Framework: `pytest`. Place tests in `tests/` mirroring `smart_agent/src/` and name files `test_*.py`.
- Local tests: set `LOCAL_RUN=1` to bypass SSM, and mock `boto3` where needed.
- Include unit tests for controllers/utils and light integration tests using FastAPI `TestClient`.

## Commit & Pull Request Guidelines
- Commits: concise, imperative mood (e.g., "Update abort logic", "Fix job cleanup").
- Branching: `main` deploys to dev; branches matching `prod*` trigger production workflows via GitHub Actions.
- PRs: include a clear description, linked issues, test steps or sample requests (curl/Postman), and note any env/SSM changes.

## Security & Config Tips
- Repository/agent names must start with `agent-` to satisfy AWS OIDC role trust (see README).
- Never commit secrets. Use GitHub Secrets → AWS SSM sync; `.env` is for local only and is gitignored.
- Control CORS via `ALLOW_ORIGINS`. Set `AGENT_NAME`, `AGENT_TYPE`, `OPENAI_API_KEY`, etc., as secrets for deployments.

