# OpenSearch Module

This module can be used as part of a terraform deployment to access OpenSearch that has been deployed as part of a cumulus stack. 

Example module configuration:
```terraform
module "cumulus_opensearch_module"  {
  source                    = "<version_tag_url>"
  prefix                    = var.prefix
  region                    = var.region
  s3_bucket_name            = lookup(var.buckets.internal, "name", null)
  cumulus_lambda_role_arn   = module.cumulus.lambda_processing_role_arn
  cumulus_lambda_role_name  = module.cumulus.lambda_processing_role_name
  layers                    = [aws_lambda_layer_version.cma-python.arn]
  memory_size               = 2048
  timeout                   = 900

  subnet_ids         = module.ngap.ngap_subnets_ids
  security_group_ids = [data.terraform_remote_state.data_persistence.outputs.elasticsearch_security_group_id]

  opensearch_index = lookup(var.cumulus_openseach_index, var.api_gateway_stage)
  opensearch_base_url = "https://${lookup(data.terraform_remote_state.data_persistence.outputs, "elasticsearch_hostname", null)}"

  env_variables = {
    private_bucket              = var.private_bucket
    stackName                   = var.prefix
    OPENSEARCH_INDEX            = lookup(var.cumulus_openseach_index, var.api_gateway_stage)
    OPENSEARCH_BASE_URL         = "https://${lookup(data.terraform_remote_state.data_persistence.outputs, "elasticsearch_hostname", null)}"
    CUMULUS_MESSAGE_ADAPTER_DIR = local.CUMULUS_MESSAGE_ADAPTER_DIR
  }
}
```

Once deployed, the ARN of the function can be provided to PyLOT so the OpenSearch
plugin can be used. See the PyLOT repo for more information: https://github.com/ghrcdaac/cloud-operations-tool-py#readme