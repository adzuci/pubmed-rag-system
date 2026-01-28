module "streamlit_app" {
  source = "aws-ia/serverless-streamlit-app/aws"

  app_name            = var.streamlit_app_name
  environment         = "dev"
  app_version         = var.streamlit_app_version
  aws_region          = var.aws_region
  path_to_app_dir     = "${path.module}/../ui"
  path_to_build_spec  = "${path.module}/../ui/buildspec.yml"
  create_vpc_resources = true
  custom_header_name  = var.streamlit_cf_header_name
  custom_header_value = var.streamlit_cf_header_value

  tags = var.tags
}
