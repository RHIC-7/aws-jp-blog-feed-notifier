module "notifier_lambda_function" {
    source = "terraform-aws-modules/lambda/aws"

    function_name = "${var.project}-lambda-notifier-${local.resource_suffix}"
    description   = "AWS Japan Blog Feed Notifier Lambda Function"
    handler       = "notifier.lambda_handler"
    runtime       = var.lambda_runtime

    source_path = [
        "../src/lambda/notifier.py",
        "../src/lambda/aws_blog_content.py",
        "../src/lambda/bedrock_output_formatter.py",
    ]

    environment_variables = local.lambda_environment_variables
    timeout               = 30

    attach_policy_statements = true
    policy_statements = {
        bedrock_invoke = {
        effect = "Allow"
        actions = [
            "bedrock:InvokeModel",
        ]
        resources = [
            "arn:aws:bedrock:ap-northeast-*::foundation-model/*",
            "arn:aws:bedrock:ap-northeast-*:${data.aws_caller_identity.current.account_id}:inference-profile/*",
        ]
        }

        dynamodb_stream_read = {
        effect = "Allow"
        actions = [
            "dynamodb:DescribeStream",
            "dynamodb:GetRecords",
            "dynamodb:GetShardIterator",
            "dynamodb:ListStreams",
        ]
        resources = [module.aws-jp-blog-feed-notifier-dynamodb-table.dynamodb_table_stream_arn]
        }

        ssm_get_webhook = {
        effect = "Allow"
        actions = [
            "ssm:GetParameter",
        ]
        resources = ["*"]
        }

        kms_decrypt_for_ssm = {
        effect = "Allow"
        actions = [
            "kms:Decrypt",
        ]
        resources = ["*"]
        }
    }
    }

    data "aws_caller_identity" "current" {}

    module "crawl_rss_feed_lambda_function" {
    source = "terraform-aws-modules/lambda/aws"

    function_name = "${var.project}-lambda-crawl-rss-feed-${local.resource_suffix}"
    description   = "AWS Japan Blog Feed Crawler Lambda Function"
    handler       = "crawl_rss_feed.lambda_handler"
    runtime       = var.lambda_runtime

    source_path = "../src/lambda/crawl_rss_feed.py"

    environment_variables = local.lambda_environment_variables
    memory_size           = 256

    attach_policy_statements = true
    policy_statements = {
        dynamodb_write = {
        effect = "Allow"
        actions = [
            "dynamodb:BatchWriteItem",
            "dynamodb:PutItem",
        ]
        resources = [module.aws-jp-blog-feed-notifier-dynamodb-table.dynamodb_table_arn]
        }
    }
    }

    output "notifier_lambda_function" {
    description = "The notifier Lambda function"
    value       = module.notifier_lambda_function
    }

    output "crawl_rss_feed_lambda_function" {
    description = "The crawl RSS feed Lambda function"
    value       = module.crawl_rss_feed_lambda_function
    }

    locals {
    lambda_environment_variables = {
        NEWS_BLOG_FEED_URL    = "https://aws.amazon.com/jp/blogs/news/feed"
        STARTUP_BLOG_FEED_URL = "https://aws.amazon.com/jp/blogs/startup/feed/"
        PSA_BLOG_FEED_URL     = "https://aws.amazon.com/jp/blogs/publicsector/feed"
        CONTENT_NS            = "http://purl.org/rss/1.0/modules/content/"
        BLOG_POSTS_TABLE      = module.aws-jp-blog-feed-notifier-dynamodb-table.dynamodb_table_id
        INFERENCE_PROFILE_ID  = var.bedrock_inference_profile_id
    }
}