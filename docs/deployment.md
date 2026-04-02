# Deployment Guide

End-to-end steps to deploy the AWS RAG Chatbot from scratch.

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| AWS CLI | >= 2.x | Deploy resources, upload frontend |
| Terraform | >= 1.7 | Provision infrastructure |
| Node.js + npm | >= 18 | Build the React frontend |
| Python | 3.12 | Run evaluation scripts locally |

Ensure `aws configure` has been run and your IAM user/role has permissions for: Lambda, S3, CloudFront, API Gateway, Cognito, DynamoDB, Step Functions, EventBridge, SSM, SNS, IAM, CloudWatch.

## Step 1 — Create a Pinecone Index

1. Sign in at [app.pinecone.io](https://app.pinecone.io)
2. Create an index named `aws-rag`:
   - **Dimensions:** 1536
   - **Metric:** Cosine
3. Copy your **API key** from the Pinecone console

## Step 2 — Store Secrets in SSM

Secrets are stored as `SecureString` parameters in AWS SSM Parameter Store. They are never written to Terraform state.

```bash
chmod +x scripts/setup-secrets.sh
./scripts/setup-secrets.sh
```

The script will prompt for:
- OpenAI API key → `/aws-rag-chatbot/openai-api-key`
- Pinecone API key → `/aws-rag-chatbot/pinecone-api-key`

To verify:

```bash
aws ssm get-parameter --name /aws-rag-chatbot/openai-api-key --with-decryption --query Parameter.Value
```

## Step 3 — Configure Terraform Remote State (optional but recommended)

Edit `terraform/providers.tf` and uncomment the `backend "s3"` block:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "aws-rag-chatbot/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

Create the bucket and lock table first:

```bash
aws s3api create-bucket --bucket your-terraform-state-bucket --region us-east-1
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Step 4 — Deploy Infrastructure

Build the Lambda packages first (bundles Python dependencies into the zip):

```bash
chmod +x scripts/build-lambdas.sh
./scripts/build-lambdas.sh
```

Then deploy:

```bash
cd terraform
terraform init
terraform plan    # review changes
terraform apply
```

Note the outputs — you will need them for the frontend:

| Output | Used for |
|---|---|
| `cloudfront_domain` | Frontend URL, Cognito callback URL |
| `api_endpoint` | `VITE_API_URL` |
| `cognito_user_pool_id` | User management |
| `cognito_client_id` | `VITE_COGNITO_CLIENT_ID` |
| `cognito_auth_domain` | `VITE_COGNITO_DOMAIN` |
| `state_machine_arn` | Manual ingestion trigger |

## Step 5 — Build and Deploy the Frontend

```bash
cd frontend

cat > .env <<EOF
VITE_COGNITO_DOMAIN=$(terraform -chdir=../terraform output -raw cognito_auth_domain)
VITE_COGNITO_CLIENT_ID=$(terraform -chdir=../terraform output -raw cognito_client_id)
VITE_API_URL=$(terraform -chdir=../terraform output -raw api_endpoint)
EOF

npm install
npm run build

BUCKET=$(terraform -chdir=../terraform output -raw site_bucket)
aws s3 sync dist/ s3://$BUCKET --delete
```

The CloudFront distribution serves the frontend at `https://<cloudfront_domain>`.

CloudFront caches assets aggressively. To invalidate after a redeployment:

```bash
DIST_ID=$(terraform -chdir=../terraform output -raw cloudfront_distribution_id 2>/dev/null || \
  aws cloudfront list-distributions --query \
  "DistributionList.Items[?Origins.Items[0].DomainName=='${BUCKET}.s3.amazonaws.com'].Id" \
  --output text)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

## Step 6 — Create a Cognito User

```bash
USER_POOL=$(terraform -chdir=terraform output -raw cognito_user_pool_id)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL \
  --username your@email.com \
  --temporary-password TempPass1! \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL \
  --username your@email.com \
  --password YourPassword1! \
  --permanent
```

## Step 7 — Run Initial Ingestion

Trigger the ingestion pipeline manually (it also runs weekly via EventBridge):

```bash
STATE_MACHINE=$(terraform -chdir=terraform output -raw state_machine_arn)
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE \
  --input '{}'
```

Monitor progress in the AWS Step Functions console. The pipeline scrapes AWS content, chunks it, and upserts vectors to Pinecone. Expect 5–15 minutes on first run.

## Step 8 — Smoke Test

1. Visit `https://<cloudfront_domain>` in your browser
2. Log in with the Cognito user you created
3. Ask a question: *"What is the AWS Well-Architected Framework?"*
4. Verify you receive an answer with cited sources
5. Click thumbs up/down to verify feedback is recorded

Check DynamoDB:

```bash
aws dynamodb scan --table-name aws-rag-chatbot-sessions --max-items 1
aws dynamodb scan --table-name aws-rag-chatbot-feedback --max-items 1
```

## Step 9 — Run RAGAS Evaluation (optional)

Requires at least a few sessions in DynamoDB:

```bash
cd /path/to/project
source .venv/bin/activate
python -m src.evaluation.ragas_eval
```

Outputs a JSON report with **faithfulness**, **answer_relevancy**, and **context_recall** scores.

## Teardown

```bash
# Remove frontend assets first (S3 bucket must be empty before Terraform can delete it)
BUCKET=$(terraform -chdir=terraform output -raw site_bucket)
aws s3 rm s3://$BUCKET --recursive

cd terraform
terraform destroy
```

Delete SSM parameters:

```bash
aws ssm delete-parameter --name /aws-rag-chatbot/openai-api-key
aws ssm delete-parameter --name /aws-rag-chatbot/pinecone-api-key
```

## Infrastructure Overview

```
terraform/
├── modules/
│   ├── auth/          Cognito user pool, app client, hosted UI domain
│   ├── frontend/      S3 (private) + CloudFront (OAC) + bucket policy
│   ├── ingestion/     Scraper/Chunker/Embedder Lambdas, S3 raw+chunks,
│   │                  Step Functions state machine, EventBridge rule
│   ├── monitoring/    SNS alerts topic + CloudWatch alarm (SFN failures)
│   ├── query-api/     API Gateway HTTP API, RAG+feedback Lambdas,
│   │                  DynamoDB sessions+feedback tables (PITR)
│   └── secrets/       SSM parameter path references (no secret values)
├── main.tf            Root module — wires all modules together
├── variables.tf       Input variables (region, project name, index name)
├── outputs.tf         Exported values for post-deploy use
└── providers.tf       AWS provider + optional remote state backend
```
