locals {
  default_tags = {
    Deployment = var.prefix
  }
}

resource "aws_lambda_function" "open_search" {
  function_name = "${var.prefix}-opensearch_lambda"
  source_code_hash = filebase64sha256("${path.module}/opensearch_package.zip")
  handler       = "task.lambda_function.cumulus_handler"
  role          = var.cumulus_lambda_role_arn
  filename      = "${path.module}/opensearch_package.zip"
  layers        = var.layers
  runtime       = "python3.10"
  timeout       = 120
  # 2 minutes
  memory_size = 4096

  tags = local.default_tags
  environment {
    variables = merge({
      bucket_name                 = var.s3_bucket_name
      stackName                   = var.prefix
      OPENSEARCH_INDEX            = var.opensearch_index
      OPENSEARCH_BASE_URL         = var.opensearch_base_url
    }, var.env_variables)
  }

  vpc_config {
    security_group_ids = var.security_group_ids
    subnet_ids = var.subnet_ids
  }
}
