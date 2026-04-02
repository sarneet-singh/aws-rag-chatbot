#!/usr/bin/env bash
# Run this ONCE before `terraform apply` to store secrets out-of-band.
set -euo pipefail
PROJECT=${1:-rag-chatbot}

read -rsp "OpenAI API key: " OPENAI_API_KEY; echo
read -rsp "Pinecone API key: " PINECONE_API_KEY; echo

aws ssm put-parameter --name "/${PROJECT}/openai_api_key" --value "$OPENAI_API_KEY" --type SecureString --overwrite
aws ssm put-parameter --name "/${PROJECT}/pinecone_api_key" --value "$PINECONE_API_KEY" --type SecureString --overwrite
echo "Secrets stored in SSM Parameter Store."
