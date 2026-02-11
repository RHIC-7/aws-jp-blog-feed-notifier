"""AWS JP Blog Feed Notifier - RSS feed crawler Lambda function."""

import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal
from email.utils import parsedate_to_datetime
from hashlib import blake2b
from zoneinfo import ZoneInfo

import boto3

JST = ZoneInfo("Asia/Tokyo")
NEWS_FEED_URL = os.environ.get("NEWS_BLOG_FEED_URL")
STARTUP_FEED_URL = os.environ.get("STARTUP_BLOG_FEED_URL")
PSA_FEED_URL = os.environ.get("PSA_BLOG_FEED_URL")
FEED_URLS = [NEWS_FEED_URL, STARTUP_FEED_URL, PSA_FEED_URL]
CONTENT_NS = os.environ.get("CONTENT_NS")


def _stable_id(url: str) -> int:
    digest = blake2b(url.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "aws-jp-blog-feed-notifier"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _yesterday_jst() -> datetime.date:
    return datetime.now(JST).date() - timedelta(days=1)


def _parse_rss_items(rss_xml: bytes):
    root = ET.fromstring(rss_xml)
    channel = root.find("channel")
    if channel is None:
        return []
    return channel.findall("item")


def lambda_handler(_event, _context):
    """AWS Lambda handler function."""
    table_name = os.environ.get("BLOG_POSTS_TABLE")
    target_date = _yesterday_jst()

    # RSSフィードを取得してパース
    try:
        items = []
        for url in FEED_URLS if FEED_URLS is not None else []:
            print(f"Fetching RSS feed: {url}")
            items.extend(_parse_rss_items(_fetch(url)))
    except (OSError, TimeoutError, ET.ParseError, ValueError) as e:
        return {"ok": False, "error": str(e)}

    # DynamoDBテーブルの取得
    dynamo_db = boto3.resource("dynamodb")
    table = dynamo_db.Table(table_name)

    # 昨日の日付の記事をDynamoDBに保存
    written = 0
    with table.batch_writer() as writer:
        for item in items:
            # 各記事のタイトル、URL、公開日時を取得
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            if not (title and url and pub):
                continue

            try:
                # 公開日時をJSTに変換
                published_jst = parsedate_to_datetime(pub).astimezone(JST)
            except (TypeError, ValueError, OverflowError):
                continue

            # 日付が対象日と異なる場合はスキップ
            if published_jst.date() != target_date:
                continue

            # DynamoDBに記事情報を保存
            writer.put_item(
                Item={
                    "id": Decimal(_stable_id(url)),
                    "date": target_date.isoformat(),
                    "title": title,
                    "url": url,
                }
            )

            print(f"Wrote: {title} ({url})")
            written += 1

    return {
        "ok": True,
        "date": target_date.isoformat(),
        "count": written,
        "feeds": FEED_URLS,
    }


if __name__ == "__main__":
    lambda_handler(None, None)
