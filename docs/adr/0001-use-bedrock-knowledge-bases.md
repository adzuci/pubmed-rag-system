# ADR 0001: Use Bedrock Knowledge Bases for Vector Storage

## Status
Accepted

## Context
We need a vector store for a PubMed RAG system that keeps the solution simple and AWS-hosted. Options considered included Amazon OpenSearch Service, Pinecone, and Amazon Bedrock Knowledge Bases. The goal is to minimize setup and operational effort while staying within AWS.

Reference: https://docs.aws.amazon.com/prescriptive-guidance/latest/choosing-an-aws-vector-database-for-rag-use-cases/vector-db-options.html

## Decision
Use Amazon Bedrock Knowledge Bases as the vector store for embeddings and retrieval.

## Consequences
- Reduced infrastructure effort by using a managed AWS-hosted option.
- Simpler integration with Bedrock embeddings and LLMs.
- Less control over low-level index settings compared to a self-managed OpenSearch cluster.

## Alternatives Considered
- Amazon OpenSearch Service: more control and flexibility, but higher operational overhead.
- Pinecone: strong vector search, but external to AWS and adds vendor management.
