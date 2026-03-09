import json
import os
import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

os.environ["CHUNKS_BUCKET"] = "test-chunks-bucket"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["PINECONE_INDEX_NAME"] = "test-index"
os.environ["OPENAI_API_KEY"] = "test-openai-key"


@pytest.fixture
def s3_with_chunks():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-chunks-bucket")
        chunk = {"chunk_id": "abc-123", "chunk_text": "AWS S3 is object storage",
                 "title": "S3 Overview", "source_url": "https://aws.amazon.com/s3",
                 "published_date": "2026-01-01", "doc_type": "blog"}
        s3.put_object(Bucket="test-chunks-bucket", Key="run/abc-123.json", Body=json.dumps(chunk))
        yield s3


def test_embed_chunks_calls_litellm(s3_with_chunks):
    from src.ingestion.embedder import embed_and_upsert
    with patch("src.ingestion.embedder.litellm.embedding") as mock_embed, \
         patch("src.ingestion.embedder.get_pinecone_index") as mock_index:
        mock_embed.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        mock_idx = MagicMock()
        mock_index.return_value = mock_idx
        embed_and_upsert([{"chunk_id": "abc", "chunk_text": "test",
                           "title": "T", "source_url": "u", "published_date": "d", "doc_type": "blog"}])
        mock_embed.assert_called_once()
        mock_idx.upsert.assert_called_once()


def test_pinecone_upsert_includes_metadata(s3_with_chunks):
    from src.ingestion.embedder import embed_and_upsert
    captured = {}
    with patch("src.ingestion.embedder.litellm.embedding") as mock_embed, \
         patch("src.ingestion.embedder.get_pinecone_index") as mock_index:
        mock_embed.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        mock_idx = MagicMock()
        mock_index.return_value = mock_idx
        mock_idx.upsert.side_effect = lambda vectors: captured.update({"vectors": vectors})
        embed_and_upsert([{"chunk_id": "abc", "chunk_text": "test content",
                           "title": "Title", "source_url": "https://aws.com",
                           "published_date": "2026-01-01", "doc_type": "blog"}])
    vec = captured["vectors"][0]
    assert vec["metadata"]["source_url"] == "https://aws.com"
    assert vec["metadata"]["title"] == "Title"
    assert "chunk_text" in vec["metadata"]
