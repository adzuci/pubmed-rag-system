# ADR 0002: Use Biopython Entrez Instead of Raw HTTP Requests

## Status
Accepted

## Context
We need a simple, reliable way to access NCBI E-utilities (ESearch/EFetch) for PubMed ingestion. We can call the endpoints directly with `requests` or use Biopython’s `Bio.Entrez` wrapper.

Reference: https://biopython.org/docs/latest/Tutorial/chapter_entrez.html

## Decision
Use Biopython’s `Bio.Entrez` module for Entrez access in this project.

## Consequences
- Simplifies request construction and parsing.
- Encourages NCBI-compliant usage patterns.
- Adds a lightweight dependency on Biopython.

## Alternatives Considered
- `requests` with manual URL construction and XML parsing: more boilerplate and error-prone.
