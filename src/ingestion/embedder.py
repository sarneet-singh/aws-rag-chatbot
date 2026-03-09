import json
import os

import boto3
import litellm
from pinecone import Pinecone

from src.utils.ssm import get_secret

S3 = boto3.client("s3")
CHUNKS_BUCKET = os.environ["CHUNKS_BUCKET"]
PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
PINECONE_API_KEY_SSM_PATH = os.environ["PINECONE_API_KEY_SSM_PATH"]
OPENAI_API_KEY_SSM_PATH = os.environ["OPENAI_API_KEY_SSM_PATH"]
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50

_pinecone_index = None


def get_pinecone_index():
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=get_secret(PINECONE_API_KEY_SSM_PATH))
        _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    return _pinecone_index


def embed_and_upsert(chunks: list[dict]) -> None:
    index = get_pinecone_index()
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["chunk_text"] for c in batch]
        response = litellm.embedding(model=EMBEDDING_MODEL, input=texts, api_key=get_secret(OPENAI_API_KEY_SSM_PATH))
        vectors = [
            {
                "id": chunk["chunk_id"],
                "values": item.embedding,
                "metadata": {
                    "chunk_text": chunk["chunk_text"],
                    "title": chunk["title"],
                    "source_url": chunk["source_url"],
                    "published_date": chunk["published_date"],
                    "doc_type": chunk["doc_type"],
                },
            }
            for chunk, item in zip(batch, response.data)
        ]
        index.upsert(vectors=vectors)
    print(f"Upserted {len(chunks)} vectors to Pinecone")


def handler(event: dict, context) -> dict:
    run_prefix = event.get("run_prefix", "")
    paginator = S3.get_paginator("list_objects_v2")
    total_vectors = 0
    for page in paginator.paginate(Bucket=CHUNKS_BUCKET, Prefix=run_prefix):
        page_chunks = []
        for obj in page.get("Contents", []):
            chunk = json.loads(S3.get_object(Bucket=CHUNKS_BUCKET, Key=obj["Key"])["Body"].read())
            page_chunks.append(chunk)
        if page_chunks:
            embed_and_upsert(page_chunks)
            total_vectors += len(page_chunks)
    return {"statusCode": 200, "body": json.dumps({"vectors_upserted": total_vectors})}
