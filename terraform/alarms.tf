resource "aws_sns_topic" "alerts" {
  name = "${var.rag_api_name}-alerts"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.rag_api_name}-lambda-errors"
  alarm_description   = "Alarm on Lambda errors for RAG API."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.rag_query.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
  tags          = var.tags
}

data "aws_lb" "streamlit_alb_alarm" {
  name       = "${var.streamlit_app_name}-alb"
  depends_on = [module.streamlit_app]
}

data "aws_lb_target_group" "streamlit_tg_alarm" {
  name       = "${var.streamlit_app_name}-tg"
  depends_on = [module.streamlit_app]
}

resource "aws_cloudwatch_metric_alarm" "streamlit_5xx" {
  alarm_name          = "${var.streamlit_app_name}-target-5xx"
  alarm_description   = "Alarm on Streamlit target 5xx responses."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = data.aws_lb.streamlit_alb_alarm.arn_suffix
    TargetGroup  = data.aws_lb_target_group.streamlit_tg_alarm.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
  tags          = var.tags
}
