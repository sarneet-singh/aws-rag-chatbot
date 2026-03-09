import json
import os
import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

os.environ.update({
    "PINECONE_INDEX_NAME": "test-index",
    "PINECONE_API_KEY_SSM_PATH": "/test/pinecone_api_key",
    "OPENAI_API_KEY_SSM_PATH": "/test/openai_api_key",
    "DYNAMODB_SESSIONS_TABLE": "test-sessions",
    "DYNAMODB_FEEDBACK_TABLE": "test-feedback",
    "AWS_DEFAULT_REGION": "us-east-1",
})


@pytest.fixture
def dynamo_tables():
    with mock_aws():
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(Name="/test/pinecone_api_key", Value="test-pinecone-key", Type="SecureString")
        ssm.put_parameter(Name="/test/openai_api_key", Value="test-openai-key", Type="SecureString")
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(TableName="test-sessions", KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"},
                                   {"AttributeName": "timestamp", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        ddb.create_table(TableName="test-feedback", KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "message_id", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"},
                                   {"AttributeName": "message_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        yield ddb


def test_query_returns_answer_and_sources(dynamo_tables):
    from src.query.rag import query_rag
    mock_matches = [MagicMock(metadata={"chunk_text": "S3 is durable", "source_url": "https://aws.amazon.com/s3", "title": "S3 Overview"}, score=0.9)]
    with patch("src.query.rag.get_pinecone_index") as mock_idx, \
         patch("src.query.rag.litellm.embedding") as mock_embed, \
         patch("src.query.rag.litellm.completion") as mock_complete:
        mock_idx.return_value.query.return_value.matches = mock_matches
        mock_embed.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        mock_complete.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="S3 provides 11 nines durability."))])
        result = query_rag("What is S3 durability?", session_id="sess-1")
    assert "answer" in result
    assert len(result["sources"]) > 0
    assert result["sources"][0]["url"] == "https://aws.amazon.com/s3"


def test_handler_saves_to_dynamodb(dynamo_tables):
    from src.query.rag import handler
    with patch("src.query.rag.query_rag") as mock_query:
        mock_query.return_value = {"answer": "42", "sources": [], "message_id": "msg-1", "session_id": "sess-1"}
        event = {"body": json.dumps({"query": "What is EC2?", "session_id": "sess-1"})}
        response = handler(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["answer"] == "42"


def test_feedback_handler_stores_rating(dynamo_tables):
    from src.query.rag import feedback_handler
    event = {"body": json.dumps({"session_id": "sess-1", "message_id": "msg-1", "rating": "up"})}
    response = feedback_handler(event, {})
    assert response["statusCode"] == 200
    table = dynamo_tables.Table("test-feedback")
    item = table.get_item(Key={"session_id": "sess-1", "message_id": "msg-1"})
    assert item["Item"]["rating"] == "up"
