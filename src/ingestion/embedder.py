import json
import os

import boto3
import litellm
from pinecone import Pinecone

S3 = boto3.client("s3")
CHUNKS_BUCKET = os.environ["CHUNKS_BUCKET"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50


def get_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX_NAME)


def embed_and_upsert(chunks: list[dict]) -> None:
    index = get_pinecone_index()
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["chunk_text"] for c in batch]
        response = litellm.embedding(model=EMBEDDING_MODEL, input=texts)
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
    chunks = []
    for page in paginator.paginate(Bucket=CHUNKS_BUCKET, Prefix=run_prefix):
        for obj in page.get("Contents", []):
            chunk = json.loads(S3.get_object(Bucket=CHUNKS_BUCKET, Key=obj["Key"])["Body"].read())
            chunks.append(chunk)
    embed_and_upsert(chunks)
    return {"statusCode": 200, "body": json.dumps({"vectors_upserted": len(chunks)})}
