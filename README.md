# AWS JP Blog Feed Notifier

A Python-based AWS Lambda function that monitors the AWS Japan blog RSS feed and sends notifications about new blog posts.

## Features

- Fetches and parses the AWS Japan blog RSS feed
- Processes the latest blog entries
- Can send notifications via AWS SNS (optional)
- Built with modern Python tools (uv, Python 3.12+)
- Fully tested with pytest

## Project Structure

```
aws-jp-blog-feed-notifier/
├── src/
│   ├── __init__.py
│   └── lambda_handler.py    # Main Lambda handler function
├── tests/
│   ├── __init__.py
│   └── test_lambda_handler.py  # Unit tests
├── pyproject.toml           # Project configuration and dependencies
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- AWS Account (for deployment)

## Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone this repository:
```bash
git clone https://github.com/RHIC-7/aws-jp-blog-feed-notifier.git
cd aws-jp-blog-feed-notifier
```

3. Install dependencies using uv:
```bash
uv sync
```

## Development

### Running Tests

Run the test suite:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Code Formatting and Linting

Format code with ruff:
```bash
uv run ruff format src tests
```

Lint code:
```bash
uv run ruff check src tests
```

Auto-fix linting issues:
```bash
uv run ruff check --fix src tests
```

## Lambda Function

### Handler Function

The main Lambda handler is located in `src/lambda_handler.py`. The function:
- Accepts standard Lambda event and context parameters
- Fetches the AWS Japan blog RSS feed
- Parses and processes the latest entries
- Returns a JSON response with blog post information

### Environment Variables

- `FEED_URL` (optional): RSS feed URL (defaults to AWS Japan blog feed)
- `SNS_TOPIC_ARN` (optional): SNS topic ARN for sending notifications

### Example Event

The Lambda function accepts any event (can be empty):
```json
{}
```

### Example Response

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Successfully fetched AWS Japan blog feed\", \"feed_title\": \"AWS Japan Blog\", \"entries_count\": 5, \"entries\": [...]}"
}
```

## Deployment to AWS Lambda

### Using AWS CLI

1. Create a deployment package:
```bash
# Sync dependencies
uv sync --no-dev

# Create a deployment directory
mkdir -p lambda_package

# Copy the source code
cp -r src/* lambda_package/

# Install dependencies to the package directory
uv pip install --target lambda_package -r pyproject.toml

# Create a ZIP file
cd lambda_package
zip -r ../lambda_function.zip .
cd ..
```

2. Create or update the Lambda function:
```bash
aws lambda create-function \
  --function-name aws-jp-blog-feed-notifier \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_LAMBDA_ROLE \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30 \
  --memory-size 256
```

3. Update an existing function:
```bash
aws lambda update-function-code \
  --function-name aws-jp-blog-feed-notifier \
  --zip-file fileb://lambda_function.zip
```

### IAM Role Requirements

The Lambda function requires the following permissions:
- Basic Lambda execution role (`AWSLambdaBasicExecutionRole`)
- SNS publish permissions (if using SNS notifications)

Example IAM policy for SNS:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:*"
    }
  ]
}
```

### Using AWS SAM or Terraform

For infrastructure as code, consider using:
- AWS SAM (Serverless Application Model)
- Terraform
- AWS CDK

Example CloudFormation/SAM template snippet:
```yaml
Resources:
  BlogFeedNotifier:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: aws-jp-blog-feed-notifier
      Runtime: python3.12
      Handler: lambda_handler.lambda_handler
      Code: ./lambda_package
      Timeout: 30
      MemorySize: 256
      Environment:
        Variables:
          FEED_URL: https://aws.amazon.com/jp/blogs/news/feed/
```

## Testing Locally

Test the Lambda function locally:
```bash
uv run python -c "from src.lambda_handler import lambda_handler; import json; print(json.dumps(lambda_handler({}, None), indent=2))"
```

## Scheduling

To run the Lambda function on a schedule, use Amazon EventBridge (CloudWatch Events):

1. Create an EventBridge rule with a schedule expression:
   - Rate: `rate(1 hour)` - Run every hour
   - Cron: `cron(0 9 * * ? *)` - Run daily at 9 AM UTC

2. Set the Lambda function as the target

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

See the [LICENSE](LICENSE) file for details.

## Resources

- [AWS Japan Blog](https://aws.amazon.com/jp/blogs/news/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [AWS Lambda Python Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)