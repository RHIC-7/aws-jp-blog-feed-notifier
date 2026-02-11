module "aws-jp-blog-feed-notifier-dynamodb-table" {
  source = "terraform-aws-modules/dynamodb-table/aws"

  name     = "${var.project}-dynamodb-table-${local.resource_suffix}"
  hash_key = "id"

  attributes = [
    {
      name = "id"
      type = "N"
    }
  ]

  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"
}