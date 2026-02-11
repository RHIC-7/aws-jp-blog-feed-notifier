module "terraform_state_s3_bucket" {
    source = "terraform-aws-modules/s3-bucket/aws"

    bucket = "${var.project}-bucket-terraform-state-${random_id.resource_suffix.hex}"
    acl    = "private"

    control_object_ownership = true
    object_ownership         = "ObjectWriter"

    versioning = {
        enabled = true
    }
}

module "terraform_state_dynamodb_table" {
    source   = "terraform-aws-modules/dynamodb-table/aws"

    name     = "${var.project}-dynamodb-table-terraform-lock-${random_id.resource_suffix.hex}"
    hash_key = "LockID"

    attributes = [
        {
            name = "LockID"
            type = "S"
        }
    ]
}

resource "random_id" "resource_suffix" {
    byte_length = 4
}

output "terraform_state_s3_bucket" {
    description = "The S3 bucket for Terraform state storage"
    value = module.terraform_state_s3_bucket
}

output "terraform_state_dynamodb_table" {
    description = "The DynamoDB table for Terraform state locking"
    value = module.terraform_state_dynamodb_table
}