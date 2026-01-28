data "aws_caller_identity" "current" {}

locals {
  kb_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${module.bedrock.knowledge_base_role_name}"
  current_principal_arn = data.aws_caller_identity.current.arn
  access_policy_name    = "os-access-${substr(var.rag_api_name, 0, 16)}"
}

resource "aws_opensearchserverless_access_policy" "kb_admins" {
  name = local.access_policy_name
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "index"
          Resource = [
            "index/${module.bedrock.default_collection.name}/*"
          ]
          Permission = [
            "aoss:UpdateIndex",
            "aoss:DeleteIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument",
            "aoss:CreateIndex"
          ]
        },
        {
          ResourceType = "collection"
          Resource = [
            "collection/${module.bedrock.default_collection.name}"
          ]
          Permission = [
            "aoss:DescribeCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:CreateCollectionItems",
            "aoss:UpdateCollectionItems"
          ]
        }
      ],
      Principal = compact(concat(var.opensearch_admin_principals, [local.kb_role_arn, local.current_principal_arn]))
    }
  ])
}
