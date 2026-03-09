import json
import os
import uuid
from datetime import datetime, timezone

import boto3
import requests
from bs4 import BeautifulSoup

S3 = boto3.client("s3")
RAW_BUCKET = os.environ["RAW_BUCKET"]
BASE_BLOG_URL = "https://aws.amazon.com/blogs/aws"
BASE_WHITEPAPER_URL = "https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html"
BASE_NEW_URL = "https://aws.amazon.com/new"


def _get(url: str, timeout: int = 10) -> BeautifulSoup | None:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "aws-rag-bot/1.0"})
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def scrape_aws_blogs(max_pages: int = 5) -> list[dict]:
    docs = []
    for page in range(1, max_pages + 1):
        url = f"{BASE_BLOG_URL}?pg={page}"
        soup = _get(url)
        if not soup:
            break
        for article in soup.find_all("article"):
            link_tag = article.find("a")
            if not link_tag:
                continue
            href = link_tag.get("href", "")
            source_url = href if href.startswith("http") else f"https://aws.amazon.com{href}"
            title = link_tag.get_text(strip=True)
            date_tag = article.find(class_="blog-post-meta")
            published_date = date_tag.get_text(strip=True) if date_tag else ""
            content_soup = _get(source_url)
            content = content_soup.get_text(separator=" ", strip=True) if content_soup else title
            docs.append({"title": title, "content": content, "source_url": source_url,
                         "published_date": published_date, "doc_type": "blog"})
    return docs


def scrape_whitepapers(max_pages: int = 3) -> list[dict]:
    docs = []
    urls = [
        "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
        "https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html",
    ]
    for url in urls:
        soup = _get(url)
        if not soup:
            continue
        content = soup.get_text(separator=" ", strip=True)
        title = soup.find("title")
        docs.append({"title": title.get_text() if title else url, "content": content,
                     "source_url": url, "published_date": "", "doc_type": "whitepaper"})
    return docs


def scrape_new_announcements(max_pages: int = 3) -> list[dict]:
    docs = []
    for page in range(1, max_pages + 1):
        soup = _get(f"{BASE_NEW_URL}?pg={page}")
        if not soup:
            break
        for item in soup.select(".lb-item"):
            link = item.find("a")
            if not link:
                continue
            href = link.get("href", "")
            source_url = href if href.startswith("http") else f"https://aws.amazon.com{href}"
            title = link.get_text(strip=True)
            docs.append({"title": title, "content": title, "source_url": source_url,
                         "published_date": "", "doc_type": "announcement"})
    return docs


def upload_raw_docs(docs: list[dict], bucket: str) -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for doc in docs:
        key = f"{run_id}/{uuid.uuid4()}.json"
        S3.put_object(Bucket=bucket, Key=key, Body=json.dumps(doc), ContentType="application/json")
    print(f"Uploaded {len(docs)} docs to s3://{bucket}/")


def handler(event: dict, context) -> dict:
    all_docs = []
    all_docs.extend(scrape_aws_blogs())
    all_docs.extend(scrape_whitepapers())
    all_docs.extend(scrape_new_announcements())
    upload_raw_docs(all_docs, RAW_BUCKET)
    return {"statusCode": 200, "body": json.dumps({"docs_ingested": len(all_docs)})}
