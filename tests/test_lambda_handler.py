"""Tests for the Lambda handler function."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.lambda_handler import lambda_handler, send_notification


@pytest.fixture
def mock_feed_data():
    """Mock feed data for testing."""
    feed = MagicMock()
    feed.bozo = False
    feed.feed = {"title": "AWS Japan Blog"}
    feed.entries = [
        {
            "title": "Test Blog Post 1",
            "link": "https://example.com/post1",
            "published": "2024-01-01T00:00:00Z",
            "summary": "This is a test blog post summary",
        },
        {
            "title": "Test Blog Post 2",
            "link": "https://example.com/post2",
            "published": "2024-01-02T00:00:00Z",
            "summary": "Another test blog post summary",
        },
    ]
    return feed


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    context.aws_request_id = "test-request-id"
    return context


def test_lambda_handler_success(mock_feed_data, lambda_context):
    """Test successful Lambda handler execution."""
    with patch("src.lambda_handler.feedparser.parse") as mock_parse:
        mock_parse.return_value = mock_feed_data

        event = {}
        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["message"] == "Successfully fetched AWS Japan blog feed"
        assert body["entries_count"] == 2
        assert len(body["entries"]) == 2


def test_lambda_handler_feed_parse_error(lambda_context):
    """Test Lambda handler with feed parse error."""
    mock_feed = MagicMock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Parse error")

    with patch("src.lambda_handler.feedparser.parse") as mock_parse:
        mock_parse.return_value = mock_feed

        event = {}
        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


def test_lambda_handler_exception(lambda_context):
    """Test Lambda handler with general exception."""
    with patch("src.lambda_handler.feedparser.parse") as mock_parse:
        mock_parse.side_effect = Exception("Network error")

        event = {}
        response = lambda_handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


def test_send_notification_with_sns(monkeypatch):
    """Test send_notification function with SNS topic."""
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test-topic")

    mock_sns_client = MagicMock()
    with patch("src.lambda_handler.boto3.client") as mock_boto3:
        mock_boto3.return_value = mock_sns_client

        entry = {
            "title": "Test Post",
            "link": "https://example.com/test",
            "published": "2024-01-01T00:00:00Z",
            "summary": "Test summary",
        }

        send_notification(entry)

        mock_boto3.assert_called_once_with("sns")
        mock_sns_client.publish.assert_called_once()


def test_send_notification_without_sns(monkeypatch):
    """Test send_notification function without SNS topic configured."""
    monkeypatch.delenv("SNS_TOPIC_ARN", raising=False)

    entry = {
        "title": "Test Post",
        "link": "https://example.com/test",
        "published": "2024-01-01T00:00:00Z",
        "summary": "Test summary",
    }

    # Should not raise an error
    send_notification(entry)
