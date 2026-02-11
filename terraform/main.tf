terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.30.0"
    }
  }
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "aws-jp-blog-feed-notifier-bucket-terraform-state-6f5d3a47" # Replace with output from terraform_state_s3_bucket
    key            = "terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "aws-jp-blog-feed-notifier-dynamodb-table-terraform-lock-6f5d3a47" # Replace with output from terraform_state_dynamodb_table
    encrypt        = true
  }
}

provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      "created_by" = var.created_by
      "project"    = var.project
    }
  }
}