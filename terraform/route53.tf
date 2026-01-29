locals {
  streamlit_zone_id = var.streamlit_hosted_zone_id != "" ? var.streamlit_hosted_zone_id : aws_route53_zone.mamoru[0].zone_id
}

resource "aws_route53_zone" "mamoru" {
  count = var.streamlit_hosted_zone_id == "" ? 1 : 0
  name  = var.streamlit_domain_name
  tags  = var.tags
}

resource "aws_acm_certificate" "streamlit" {
  provider          = aws.us_east_1
  domain_name       = var.streamlit_domain_name
  validation_method = "DNS"
}

resource "aws_route53_record" "streamlit_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.streamlit.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = local.streamlit_zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "streamlit" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.streamlit.arn
  validation_record_fqdns = [for record in aws_route53_record.streamlit_cert_validation : record.fqdn]
}

# Email reputation: SPF (no mail servers) and DMARC (policy + reporting)
resource "aws_route53_record" "spf" {
  zone_id = local.streamlit_zone_id
  name    = var.streamlit_domain_name
  type    = "TXT"
  ttl     = 300
  records = ["v=spf1 -all"]
}

resource "aws_route53_record" "dmarc" {
  zone_id = local.streamlit_zone_id
  name    = "_dmarc.${var.streamlit_domain_name}"
  type    = "TXT"
  ttl     = 300
  records = ["v=DMARC1; p=none; rua=mailto:${var.alert_email}; fo=1"]
}
