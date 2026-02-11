terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 6.30.0"
        }
    }
    required_version = ">= 1.5.0"
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