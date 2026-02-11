resource "aws_lambda_event_source_mapping" "blog_posts_inserted" {
  event_source_arn  = module.aws-jp-blog-feed-notifier-dynamodb-table.dynamodb_table_stream_arn
  function_name     = module.notifier_lambda_function.lambda_function_arn
  starting_position = "LATEST"

  batch_size = 10
  enabled    = true
}
