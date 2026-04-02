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
BASE_NEW_URL = "https://aws.amazon.com/new"

# Documentation sections to fully crawl (entry page + all sidebar sub-pages)
DOC_SECTIONS = [
    "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
    "https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html",
    "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html",
    "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
    "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
    "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html",
    "https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html",
    "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
]

# Maximum sub-pages to crawl per doc section
MAX_SUBPAGES = 30


def _get(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "aws-rag-bot/1.0"})
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def _extract_doc_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract relative sub-page links from an AWS docs page."""
    from urllib.parse import urljoin, urlparse
    base_parsed = urlparse(base_url)
    base_prefix = f"{base_parsed.scheme}://{base_parsed.netloc}{'/'.join(base_parsed.path.split('/')[:-1])}/"

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") or href.startswith("#") or not href.endswith(".html"):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if (parsed.netloc == base_parsed.netloc and
                full_url.startswith(base_prefix) and
                full_url not in links):
            links.append(full_url)
    return links


def _extract_page_content(soup: BeautifulSoup) -> str:
    """Extract main content text from an AWS docs page."""
    for tag in soup.select("nav, footer, script, style, [class*='feedback'], [id*='feedback'], .breadcrumb"):
        tag.decompose()
    for selector in ["main", "#main-content", ".awsui-content", "article", ".main-col-body"]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)


def scrape_doc_section(entry_url: str, max_pages: int = MAX_SUBPAGES) -> list[dict]:
    """Recursively crawl an AWS doc section up to max_pages, following sub-page links."""
    docs = []
    seen = set()
    queue = [entry_url]

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        soup = _get(url)
        if not soup:
            continue

        content = _extract_page_content(soup)
        if len(content) < 100:
            continue

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url
        docs.append({
            "title": title,
            "content": content,
            "source_url": url,
            "published_date": "",
            "doc_type": "documentation",
        })
        print(f"Scraped: {title[:70]}")

        # Enqueue sub-pages discovered on this page
        for link in _extract_doc_links(soup, url):
            if link not in seen:
                queue.append(link)

    return docs


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
            if content_soup is None:
                continue
            content = _extract_page_content(content_soup)
            if len(content) < 100:
                continue
            docs.append({"title": title, "content": content, "source_url": source_url,
                         "published_date": published_date, "doc_type": "blog"})
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


def upload_raw_docs(docs: list[dict], bucket: str, run_id: str | None = None) -> str:
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for doc in docs:
        key = f"{run_id}/{uuid.uuid4()}.json"
        S3.put_object(Bucket=bucket, Key=key, Body=json.dumps(doc), ContentType="application/json")
    print(f"Uploaded {len(docs)} docs to s3://{bucket}/")
    return run_id


def handler(event: dict, context) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    all_docs = []

    print("Scraping AWS documentation sections...")
    for url in DOC_SECTIONS:
        all_docs.extend(scrape_doc_section(url))

    print("Scraping AWS blogs...")
    all_docs.extend(scrape_aws_blogs())

    print("Scraping AWS announcements...")
    all_docs.extend(scrape_new_announcements())

    upload_raw_docs(all_docs, RAW_BUCKET, run_id=run_id)
    return {"statusCode": 200, "run_prefix": run_id, "body": json.dumps({"docs_ingested": len(all_docs)})}
