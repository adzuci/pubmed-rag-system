data "aws_lb" "streamlit_alb" {
  name       = "${var.streamlit_app_name}-alb"
  depends_on = [module.streamlit_app]
}

resource "aws_cloudfront_distribution" "streamlit_custom" {
  depends_on = [aws_acm_certificate_validation.streamlit]

  origin {
    domain_name = data.aws_lb.streamlit_alb.dns_name
    origin_id   = "${var.streamlit_app_name}-alb-origin"

    custom_header {
      name  = var.streamlit_cf_header_name
      value = var.streamlit_cf_header_value
    }

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  enabled         = true
  is_ipv6_enabled = true
  aliases         = [var.streamlit_domain_name]

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "${var.streamlit_app_name}-alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    cache_policy_id        = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"
    response_headers_policy_id = "60669652-455b-4ae9-85a4-c4c02393f86c"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.streamlit.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = var.tags
}

resource "aws_route53_record" "streamlit_apex_a" {
  zone_id = local.streamlit_zone_id
  name    = var.streamlit_domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.streamlit_custom.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "streamlit_apex_aaaa" {
  zone_id = local.streamlit_zone_id
  name    = var.streamlit_domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.streamlit_custom.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}
