import os
import json
import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

os.environ.update({
    "DYNAMODB_SESSIONS_TABLE": "test-sessions",
    "REPORTS_BUCKET": "test-reports",
    "OPENAI_API_KEY_SSM_PATH": "/test/openai_api_key",
    "AWS_DEFAULT_REGION": "us-east-1",
})


@pytest.fixture
def aws_resources():
    with mock_aws():
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(Name="/test/openai_api_key", Value="test-key", Type="SecureString")
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(TableName="test-sessions", KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"},
                                   {"AttributeName": "timestamp", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        table = ddb.Table("test-sessions")
        table.put_item(Item={"session_id": "s1", "timestamp": "2026-03-01T00:00:00Z",
                              "query": "What is S3?", "answer": "S3 is object storage.",
                              "context_chunks": ["S3 stores objects"], "sources": []})
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-reports")
        yield ddb, s3


def test_fetch_sessions_returns_records(aws_resources):
    from src.evaluation.ragas_eval import fetch_recent_sessions
    records = fetch_recent_sessions(limit=10)
    assert len(records) >= 1
    assert "query" in records[0]


def test_handler_writes_report_to_s3(aws_resources):
    from src.evaluation.ragas_eval import handler
    with patch("src.evaluation.ragas_eval.run_ragas") as mock_ragas:
        mock_ragas.return_value = {"faithfulness": 0.9, "answer_relevancy": 0.85, "context_recall": 0.8}
        response = handler({}, {})
    assert response["statusCode"] == 200
    _, s3 = aws_resources
    objs = s3.list_objects_v2(Bucket="test-reports")
    assert objs["KeyCount"] > 0
