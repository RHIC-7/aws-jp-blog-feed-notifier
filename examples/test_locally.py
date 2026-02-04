"""
Example script to test the Lambda handler locally.
"""

import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lambda_handler import lambda_handler


class MockContext:
    """Mock Lambda context for local testing."""

    def __init__(self):
        self.function_name = "aws-jp-blog-feed-notifier"
        self.memory_limit_in_mb = 256
        self.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:aws-jp-blog-feed-notifier"
        )
        self.aws_request_id = "local-test-request-id"


if __name__ == "__main__":
    print("Testing Lambda handler locally...")
    print("-" * 80)

    # Test event (can be empty)
    event = {}

    # Create mock context
    context = MockContext()

    # Call the Lambda handler
    response = lambda_handler(event, context)

    # Print the response
    print("\nResponse:")
    print(f"Status Code: {response['statusCode']}")
    print("\nBody:")
    body = json.loads(response["body"])
    print(json.dumps(body, indent=2, ensure_ascii=False))

    if response["statusCode"] == 200:
        print(f"\nSuccessfully fetched {body.get('entries_count', 0)} blog entries!")
    else:
        print("\nError occurred!")
