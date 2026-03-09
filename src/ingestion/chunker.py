import json
import os
import uuid

import boto3
import tiktoken

S3 = boto3.client("s3")
RAW_BUCKET = os.environ["RAW_BUCKET"]
CHUNKS_BUCKET = os.environ["CHUNKS_BUCKET"]
ENCODING = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, max_tokens: int = 512, overlap: int = 50) -> list[str]:
    tokens = ENCODING.encode(text)
    if len(tokens) <= max_tokens:
        return [text]
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(ENCODING.decode(chunk_tokens))
        start += max_tokens - overlap
    return chunks


def process_raw_doc(doc: dict) -> list[dict]:
    chunks = chunk_text(doc["content"])
    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "chunk_text": chunk,
            "title": doc["title"],
            "source_url": doc["source_url"],
            "published_date": doc["published_date"],
            "doc_type": doc["doc_type"],
        }
        for chunk in chunks
    ]


def handler(event: dict, context) -> dict:
    run_prefix = event.get("run_prefix", "")
    paginator = S3.get_paginator("list_objects_v2")
    total_chunks = 0
    for page in paginator.paginate(Bucket=RAW_BUCKET, Prefix=run_prefix):
        for obj in page.get("Contents", []):
            raw = json.loads(S3.get_object(Bucket=RAW_BUCKET, Key=obj["Key"])["Body"].read())
            chunks = process_raw_doc(raw)
            for chunk in chunks:
                key = f"{run_prefix}/{chunk['chunk_id']}.json"
                S3.put_object(Bucket=CHUNKS_BUCKET, Key=key, Body=json.dumps(chunk), ContentType="application/json")
            total_chunks += len(chunks)
    return {"statusCode": 200, "body": json.dumps({"chunks_created": total_chunks})}
