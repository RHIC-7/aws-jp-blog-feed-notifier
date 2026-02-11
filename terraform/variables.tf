variable "created_by" {
  description = "Tag value for created_by"
  type        = string
  default     = "rhic"
}

variable "project" {
  description = "Tag value for project"
  type        = string
  default     = "aws-jp-blog-feed-notifier"
}

variable "lambda_runtime" {
  description = "Runtime environment for the Lambda function"
  type        = string
  default     = "python3.12"
}

variable "bedrock_inference_profile_id" {
  description = "Bedrock inference profile ID (e.g., jp.amazon.nova-2-lite-v1:0)"
  type        = string
  default     = "jp.amazon.nova-2-lite-v1:0"
}

locals {
  resource_suffix = random_id.resource_suffix.hex
}

resource "random_id" "resource_suffix" {
  byte_length = 4
}