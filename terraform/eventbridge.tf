module "crawl_rss_feed_eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  bus_name   = "default"
  create_bus = false

  attach_lambda_policy = true
  lambda_target_arns   = [module.crawl_rss_feed_lambda_function.lambda_function_arn]

  schedules = {
    lambda-cron = {
      description         = "Cron schedule to trigger RSS feed crawling every day"
      schedule_expression = "cron(0 7 * * ? *)" # 07:00 AM JST daily
      timezone            = "Asia/Tokyo"
      state               = false
      arn                 = module.crawl_rss_feed_lambda_function.lambda_function_arn
      input               = jsonencode({ "job" : "cron-by-rate" })
    }
  }
}