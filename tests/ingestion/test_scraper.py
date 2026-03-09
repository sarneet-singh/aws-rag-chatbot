import json
import pytest
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3
import os

os.environ["RAW_BUCKET"] = "test-raw-bucket"

@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-raw-bucket")
        yield s3

def test_scrape_aws_blogs_returns_articles(s3_bucket):
    from src.ingestion.scraper import scrape_aws_blogs
    with patch("src.ingestion.scraper.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
        <html><body>
          <article>
            <h2><a href="/blogs/aws/my-post">My Post Title</a></h2>
            <p class="blog-post-meta">2026-03-01</p>
          </article>
        </body></html>
        """
        results = scrape_aws_blogs(max_pages=1)
    assert len(results) > 0
    assert "title" in results[0]
    assert "source_url" in results[0]

def test_upload_to_s3_stores_json(s3_bucket):
    from src.ingestion.scraper import upload_raw_docs
    docs = [{"title": "Test", "content": "Hello", "source_url": "https://aws.amazon.com", "published_date": "2026-03-01", "doc_type": "blog"}]
    upload_raw_docs(docs, "test-raw-bucket")
    objs = s3_bucket.list_objects_v2(Bucket="test-raw-bucket")
    assert objs["KeyCount"] > 0

def test_lambda_handler_invokes_all_sources(s3_bucket):
    from src.ingestion.scraper import handler
    with patch("src.ingestion.scraper.scrape_aws_blogs") as mock_blogs, \
         patch("src.ingestion.scraper.scrape_whitepapers") as mock_wp, \
         patch("src.ingestion.scraper.scrape_new_announcements") as mock_new, \
         patch("src.ingestion.scraper.scrape_repost") as mock_repost, \
         patch("src.ingestion.scraper.upload_raw_docs") as mock_upload:
        mock_blogs.return_value = [{"title": "b", "content": "x", "source_url": "u", "published_date": "d", "doc_type": "blog"}]
        mock_wp.return_value = []
        mock_new.return_value = []
        mock_repost.return_value = []
        result = handler({}, {})
    assert result["statusCode"] == 200
    mock_upload.assert_called_once()
