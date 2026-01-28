# Scheduled PubMed ingest (AWS)

This outlines a safe path to store the NCBI API key in AWS and run the ingest on a schedule.

## Secrets
Store the key in AWS Secrets Manager (no plaintext in repo).

Example secret name:
- `pubmed-rag/ncbi`

Example JSON value:
```json
{"NCBI_EMAIL":"you@example.com","NCBI_API_KEY":"REPLACE_ME"}
```

Suggested IAM policy for the runtime role:
- `secretsmanager:GetSecretValue` for the secret ARN
- `kms:Decrypt` if a customer-managed KMS key is used

## Scheduled runs (EventBridge -> Lambda)
Recommended for small periodic jobs.

1) Package the ingest code as a Lambda handler.
2) Add the secret name as an env var: `NCBI_SECRET_ARN`.
3) In the handler, fetch and parse the secret, then set `Entrez.email`/`Entrez.api_key`.
4) Configure an EventBridge rule (cron or rate) to trigger the Lambda.
5) Write raw results to `s3://<bucket>/raw/` and processed to `s3://<bucket>/processed/`.

Minimal schedule examples:
- Hourly: `rate(1 hour)`
- Daily at 02:00 UTC: `cron(0 2 * * ? *)`

## Scheduled runs (EventBridge -> ECS task)
If the ingest code grows or exceeds Lambda limits, use a scheduled ECS task.

1) Build a container image with the ingest script.
2) Run the task with a task role that can read the secret and write to S3.
3) Use EventBridge Scheduler to invoke the task on a cron/rate schedule.

## Rollback
- Disable the EventBridge rule / Scheduler target.
- Revoke the runtime role's `secretsmanager:GetSecretValue` permission.
