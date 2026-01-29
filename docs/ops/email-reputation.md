# Email and domain reputation (SPF, DMARC)

## What was added on 1/29/2026

- **SPF** (apex `mamoruproject.org`): `v=spf1 -all` — Declares that no servers are authorized to send mail for the domain. Reduces spoofing and improves reputation when the domain is not used for email.
- **DMARC** (`_dmarc.mamoruproject.org`): `p=none; rua=mailto:<alert_email>` — Policy “monitor only” and aggregate failure reports sent to your email. You can tighten to `p=quarantine` or `p=reject` after reviewing reports.

These records are now also managed in Terraform (`terraform/route53.tf`) so they stay in sync with the rest of the zone.

## Making the domain more reputable

1. **Keep DMARC in place**  
   Use the reports (rua) to see if anyone is spoofing your domain. After a few weeks with no legitimate mail from `@mamoruproject.org`, consider tightening to `p=quarantine` or `p=reject` so receivers treat failing messages more strictly.

2. **If we later send email from the domain**  
   - Add **SPF** includes for your mail provider (e.g. `v=spf1 include:_spf.google.com ~all` for Google Workspace).  
   - Add **DKIM** (TXT at a selector like `selector._domainkey.mamoruproject.org`) using the value from your provider.  
   - Keep **DMARC** and optionally add `ruf=mailto:...` for forensic (per-message) reports.


