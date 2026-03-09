import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from datasets import Dataset

DDB = boto3.resource("dynamodb")
S3 = boto3.client("s3")
SESSIONS_TABLE = os.environ["DYNAMODB_SESSIONS_TABLE"]
REPORTS_BUCKET = os.environ["REPORTS_BUCKET"]


def fetch_recent_sessions(limit: int = 100) -> list[dict]:
    table = DDB.Table(SESSIONS_TABLE)
    response = table.scan(Limit=limit, FilterExpression=Attr("query").exists())
    return response.get("Items", [])


def run_ragas(records: list[dict]) -> dict:
    dataset = Dataset.from_list([{
        "question": r["query"],
        "answer": r["answer"],
        "contexts": r.get("context_chunks", []),
        "ground_truth": r["answer"],
    } for r in records if r.get("context_chunks")])

    if len(dataset) == 0:
        return {"error": "no records with context to evaluate"}

    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
    return {k: float(v) for k, v in result.items()}


def handler(event: dict, context) -> dict:
    records = fetch_recent_sessions()
    metrics = run_ragas(records)
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "sample_size": len(records), "metrics": metrics}
    key = f"ragas-report-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    S3.put_object(Bucket=REPORTS_BUCKET, Key=key, Body=json.dumps(report, indent=2), ContentType="application/json")
    print(f"RAGAS report: {metrics}")
    return {"statusCode": 200, "body": json.dumps(report)}
