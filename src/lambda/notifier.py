"""AWS Lambda function to send notifications on new or updated blog posts."""
import json
import os
import urllib.request

import boto3
from aws_blog_content import extract_main_text
from bedrock_output_formatter import (bedrock_output_to_text,
                                      format_nova_summary)
from boto3.dynamodb.types import TypeDeserializer

SSM_WEBHOOK_PARAM = "/Blog/Webhook"
PROMPT_MAX_LENGTH = 1000
INFERENCE_PROFILE_ID = os.environ.get("INFERENCE_PROFILE_ID")
BEDROCK_REGION = os.environ.get("MODEL_REGION")
_deserializer = TypeDeserializer()

SYSTEM_PROMPT_TEMPLATE = """
<persona>You are an AWS Solutions Architect specialist.</persona>
<instruction>Summarize the content inside <input></input> tags.

This is a blog post summary task (not a release note task).
Explain what the blog post is about, what problem it solves, and who it is for.
If the post contains steps, requirements, or key takeaways, include them.

Output the analysis in <thinking></thinking> tags as bullet points.
Each bullet line must start with "- " and end with "\n".
Then output the final short summary in <summary></summary> as per
<summaryRule></summaryRule>.
You are not allowed to utilize any information except in the input.
Output format shall be in accordance with <outputFormat></outputFormat> tags.
</instruction>

<outputLanguage>In {language}.</outputLanguage>

<summaryRule>
The final summary must consist of 1 or 2 sentences.
Avoid quoting or using unnecessary quotation marks.
</summaryRule>

<outputFormat>
<thinking>(bullet points of the input)</thinking>
<summary>(final summary)</summary>
</outputFormat>

Follow the instruction.
"""

USER_INPUT_TEMPLATE = """<input>{blog_body}</input>"""


def _build_system_prompt(language: str = "Japanese") -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(language=language)


def _build_user_message(blog_body: str) -> str:
    return USER_INPUT_TEMPLATE.format(blog_body=blog_body)


def _ddb_image_to_dict(image: dict) -> dict:
    return {k: _deserializer.deserialize(v) for k, v in (image or {}).items()}


def _get_webhook_url() -> str:
    ssm = boto3.client("ssm")
    resp = ssm.get_parameter(Name=SSM_WEBHOOK_PARAM, WithDecryption=True)
    return resp["Parameter"]["Value"]


def _get_conversation(user_text: str) -> list:
    return [
        {
            "role": "user",
            "content": [
                {
                    "text": user_text,
                }
            ],
        },
    ]


def _post_json(url: str, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def get_url_content(url: str) -> str:
    """Fetch the content of the given URL."""
    with urllib.request.urlopen(url, timeout=10) as response:
        page_html = response.read().decode("utf-8", errors="replace")

    return extract_main_text(page_html)


def get_ai_summary(text: str) -> str:
    """Generate a concise summary using AWS Bedrock model."""
    # プロンプトを構築
    system_prompt = _build_system_prompt(language="Japanese")
    user_message = _build_user_message(text[:PROMPT_MAX_LENGTH])
    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
    )

    if not INFERENCE_PROFILE_ID:
        raise ValueError("INFERENCE_PROFILE_ID is not set")

    response = bedrock_client.converse(
        modelId=INFERENCE_PROFILE_ID,
        system=[{"text": system_prompt}],
        messages=_get_conversation(user_message),
        inferenceConfig={"maxTokens": 500, "temperature": 0.3},
    )

    raw = bedrock_output_to_text(response)
    if not raw:
        raise ValueError("Bedrock response did not contain text content")
    return format_nova_summary(raw)


def lambda_handler(event, _context):
    """AWS Lambda handler function."""
    webhook_url = _get_webhook_url()
    sent = 0

    # DynamoDB Streamsのイベントから新規または更新されたブログ投稿を検出し、通知を送信
    for record in (event or {}).get("Records", []):
        print(f"Processing record: {record}")
        # ブログが新規作成された時のみ処理を行う
        if record.get("eventName") != "INSERT":
            continue

        # DynamoDBのNewImageを取得
        new_image = (record.get("dynamodb") or {}).get("NewImage")
        print(f"NewImage: {new_image}")
        if not new_image:
            continue

        # DynamoDBのイメージを辞書形式に変換
        item = _ddb_image_to_dict(new_image)
        title = item.get("title")
        url = item.get("url")

        if not (title and url):
            continue

        try:
            # ブログ記事の内容を取得し、AI要約を生成
            content = get_url_content(url)
            print(f"Fetched content length: {len(content)}")
            summary = get_ai_summary(content)
            print(f"Generated summary: {summary}")

            # 通知ペイロードを作成してWebhookに送信
            body = {
                "title": title,
                "text": summary,
                "url": url,
            }
            _post_json(webhook_url, body)
            print(f"Sent notification: {title} ({url})")
            sent += 1
        except OSError:
            continue

    return {"ok": True, "sent": sent}


if __name__ == "__main__":
    lambda_handler(None, None)
