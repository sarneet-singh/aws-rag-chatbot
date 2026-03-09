# AWS RAG Chatbot

A serverless RAG chatbot that answers AWS architecture questions using auto-ingested AWS content, with Cognito auth, cited sources, and RAGAS evaluation.

## Architecture

EventBridge triggers a Step Functions pipeline (Scraper → Chunker → Embedder Lambdas) weekly. A React frontend on S3/CloudFront talks to a RAG Lambda via API Gateway (Cognito JWT auth). LiteLLM abstracts the LLM provider. Pinecone stores vectors with source metadata returned alongside answers.

## Tech Stack

- **Backend:** Python 3.12, AWS Lambda, Step Functions, API Gateway, Cognito, DynamoDB, S3, CloudFront, EventBridge, SNS
- **AI/ML:** LiteLLM, OpenAI (gpt-4o-mini + text-embedding-3-small), Pinecone, RAGAS
- **Frontend:** React (Vite)
- **Infrastructure:** Terraform

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Fill in your API keys
```

## Run Tests

```bash
pytest tests/ -v --tb=short
```

## Deploy

See `terraform/` for infrastructure and `docs/plans/` for the full implementation plan.
