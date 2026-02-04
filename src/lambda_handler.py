"""
AWS Lambda handler for AWS Japan blog feed notifier.

This Lambda function fetches the AWS Japan blog RSS feed and sends notifications
about new blog posts.
"""

import json
import os
from typing import Any

import boto3
import feedparser


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler function.

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Response object with status code and body
    """
    print(f"Event: {json.dumps(event)}")

    try:
        # AWS Japan blog RSS feed URL
        feed_url = os.environ.get("FEED_URL", "https://aws.amazon.com/jp/blogs/news/feed/")

        # Fetch and parse the RSS feed
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            raise ValueError(f"Failed to parse feed: {feed.bozo_exception}")

        # Process the latest entries
        latest_entries = feed.entries[:5]  # Get the 5 most recent entries

        results = []
        for entry in latest_entries:
            result = {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:200],  # First 200 chars
            }
            results.append(result)
            print(f"Blog entry: {result['title']} - {result['link']}")

        response = {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Successfully fetched AWS Japan blog feed",
                    "feed_title": feed.feed.get("title", ""),
                    "entries_count": len(results),
                    "entries": results,
                }
            ),
        }

        return response

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def send_notification(entry: dict[str, str]) -> None:
    """
    Send notification about a new blog entry.

    This is a placeholder function that can be extended to send notifications
    via SNS, SES, Slack, etc.

    Args:
        entry: Blog entry information
    """
    # Example: Send to SNS topic
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if sns_topic_arn:
        sns_client = boto3.client("sns")
        message = f"New AWS Japan Blog Post\n\nTitle: {entry['title']}\nLink: {entry['link']}"
        sns_client.publish(TopicArn=sns_topic_arn, Message=message, Subject=entry["title"])
        print(f"Notification sent for: {entry['title']}")
