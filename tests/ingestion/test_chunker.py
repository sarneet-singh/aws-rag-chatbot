import json
import os
import pytest
from unittest.mock import patch
from moto import mock_aws
import boto3

os.environ["RAW_BUCKET"] = "test-raw-bucket"
os.environ["CHUNKS_BUCKET"] = "test-chunks-bucket"


@pytest.fixture
def s3_with_raw():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-raw-bucket")
        s3.create_bucket(Bucket="test-chunks-bucket")
        doc = {"title": "Test Doc", "content": "word " * 600, "source_url": "https://aws.amazon.com",
               "published_date": "2026-03-01", "doc_type": "blog"}
        s3.put_object(Bucket="test-raw-bucket", Key="run/doc1.json", Body=json.dumps(doc))
        yield s3


def test_chunk_text_splits_at_token_limit():
    from src.ingestion.chunker import chunk_text
    text = "word " * 600
    chunks = chunk_text(text, max_tokens=512, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)


def test_chunk_text_small_content_returns_one_chunk():
    from src.ingestion.chunker import chunk_text
    text = "short content"
    chunks = chunk_text(text, max_tokens=512, overlap=50)
    assert len(chunks) == 1


def test_handler_reads_raw_and_writes_chunks(s3_with_raw):
    from src.ingestion.chunker import handler
    result = handler({"run_prefix": "run"}, {})
    assert result["statusCode"] == 200
    objs = s3_with_raw.list_objects_v2(Bucket="test-chunks-bucket")
    assert objs["KeyCount"] > 0
