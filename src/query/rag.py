import json
import os
import uuid
from datetime import datetime, timezone

import boto3
import litellm
from pinecone import Pinecone

from src.utils.ssm import get_secret

PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
PINECONE_API_KEY_SSM_PATH = os.environ["PINECONE_API_KEY_SSM_PATH"]
OPENAI_API_KEY_SSM_PATH = os.environ["OPENAI_API_KEY_SSM_PATH"]
SESSIONS_TABLE = os.environ["DYNAMODB_SESSIONS_TABLE"]
FEEDBACK_TABLE = os.environ["DYNAMODB_FEEDBACK_TABLE"]
EMBEDDING_MODEL = "text-embedding-3-small"
COMPLETION_MODEL = "gpt-4o-mini"
TOP_K = 5

def _ddb():
    return boto3.resource("dynamodb")


def get_pinecone_index():
    return Pinecone(api_key=get_secret(PINECONE_API_KEY_SSM_PATH)).Index(PINECONE_INDEX_NAME)


SYSTEM_PROMPT = """You are an expert AWS Solutions Architect assistant.
Answer questions using ONLY the provided context from AWS documentation.
If the context does not contain enough information, say so clearly.
Always be concise and accurate. Do not make up AWS service details."""


def query_rag(query: str, session_id: str) -> dict:
    litellm.api_key = get_secret(OPENAI_API_KEY_SSM_PATH)
    embed_response = litellm.embedding(model=EMBEDDING_MODEL, input=[query])
    query_vector = embed_response.data[0].embedding

    index = get_pinecone_index()
    results = index.query(vector=query_vector, top_k=TOP_K, include_metadata=True)

    context_parts = []
    sources = []
    seen_urls = set()
    for match in results.matches:
        meta = match.metadata
        context_parts.append(f"[Source: {meta['title']}]\n{meta['chunk_text']}")
        if meta["source_url"] not in seen_urls:
            sources.append({"title": meta["title"], "url": meta["source_url"]})
            seen_urls.add(meta["source_url"])

    context = "\n\n---\n\n".join(context_parts)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]

    completion = litellm.completion(model=COMPLETION_MODEL, messages=messages)
    answer = completion.choices[0].message.content

    message_id = str(uuid.uuid4())
    _ddb().Table(SESSIONS_TABLE).put_item(Item={
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_id": message_id,
        "query": query,
        "answer": answer,
        "sources": sources,
        "context_chunks": [m.metadata["chunk_text"] for m in results.matches],
    })

    return {"answer": answer, "sources": sources, "message_id": message_id, "session_id": session_id}


def handler(event: dict, context) -> dict:
    body = json.loads(event.get("body", "{}"))
    query = body.get("query", "")
    session_id = body.get("session_id", str(uuid.uuid4()))
    if not query:
        return {"statusCode": 400, "body": json.dumps({"error": "query is required"})}
    result = query_rag(query, session_id)
    return {"statusCode": 200, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": json.dumps(result)}


def feedback_handler(event: dict, context) -> dict:
    body = json.loads(event.get("body", "{}"))
    _ddb().Table(FEEDBACK_TABLE).put_item(Item={
        "session_id": body["session_id"],
        "message_id": body["message_id"],
        "rating": body["rating"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"statusCode": 200, "body": json.dumps({"ok": True})}
