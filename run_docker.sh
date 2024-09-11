#!/bin/bash

# Environment variables
OPENAI_API_KEY="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"
NEXT_PUBLIC_GTM="G-V0FCK58L67"
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="ls__72500c09d0884fd09b24a05ae2221ee2"
LANGCHAIN_PROJECT="inform-dev"
LANGSMITH_API_KEY=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
DB_USER=jarsandon
DB_PASS=1testPass2
GROQ_API_KEY=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

# Build Docker image
docker build -t docker-inform-fastapi .

# Run Docker container with environment variables
docker run -p 8080:80 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e DB_USER="$DB_USER" \
  -e DB_PASS="$DB_PASS" \
  -e GROQ_API_KEY="$GROQ_API_KEY" \
  -e LANGCHAIN_TRACING_V2="$LANGCHAIN_TRACING_V2" \
  -e LANGCHAIN_ENDPOINT="$LANGCHAIN_ENDPOINT" \
  -e LANGCHAIN_API_KEY="$LANGCHAIN_API_KEY" \
  -e LANGCHAIN_PROJECT="$LANGCHAIN_PROJECT" \
  -e LANGSMITH_API_KEY="$LANGSMITH_API_KEY" \
  docker-inform-fastapi
