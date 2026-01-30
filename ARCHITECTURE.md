# Architecture

This document describes Mamoru’s architecture in three views: the high level **Cloud Deployment** view, the **Data Ingestion** view (pipeline into the Knowledge Base), and **Bedrock Zoomed In** view (how retrieval and generation work inside AWS Bedrock).

**Note:** The diagrams below do not depict ECS (where the Streamlit UI runs) or IAM roles and policies.

---

## 1. Cloud Deployment

A user accesses Mamoru through CloudFront, which handles HTTPS and global edge caching. Requests are routed through an Application Load Balancer to the Streamlit UI, which serves the interactive experience. When a user submits a question, the UI makes a secure call to API Gateway. API Gateway invokes a single Lambda function (`rag_handler`), which orchestrates the request. The Lambda first retrieves relevant context from the Bedrock Knowledge Base. Those retrieved chunks are used to augment the prompt sent to the Bedrock LLM. The LLM generates an answer grounded in the retrieved literature. The Lambda returns a structured JSON response back to the UI. The UI renders the response to the user, completing the RAG loop.

```mermaid
flowchart TB
  %% =========================
  %% Runtime RAG
  %% =========================

  U[User]

  subgraph AWS["AWS"]
    direction TB

    %% Edge + UI
    CF[CloudFront]
    ALB[ALB]
    UI[Streamlit UI]

    CF --> ALB --> UI

    %% API
    APIGW[API Gateway]
    UI -->|HTTPS| APIGW

    %% Lambda inner box
    subgraph LAMBDAS["Lambda functions"]
      direction TB
      RH[Lambda: rag_query]
    end

    APIGW -->|Invoke| RH
    RH -->|Response JSON| UI

    %% RAG components
    KB[Bedrock Knowledge Base]
    LLM[Bedrock LLM]

    RH -->|Retrieve| KB
    KB -->|Chunks| RH
    RH -->|Augment prompt| LLM
    LLM -->|Answer| RH
  end

  %% Entry
  U --> CF

  %% =========================
  %% Styling (polished)
  %% =========================
  classDef aws fill:#f7f7f7,stroke:#3a3a3a,stroke-width:1.6px,rx:8,ry:8;
  classDef external fill:#ffffff,stroke:#3a3a3a,stroke-width:1.6px,rx:8,ry:8;
  classDef lambda fill:#fff6e8,stroke:#b26a00,stroke-width:1.6px,rx:8,ry:8;

  class AWS,CF,ALB,UI,APIGW,KB,LLM aws;
  class LAMBDAS,RH lambda;
  class U external;
```

---

## 2. Data Ingestion

We start with PubMed, pulling peer-reviewed clinical literature using standard ESearch / EFetch APIs. Articles are collected by a local ingest notebook or Lambda, focused purely on retrieval, not interpretation. The raw content is stored in S3 (`raw/`) as a durable source of truth so it can be reprocessed over time. A processing step cleans, chunks, and adds metadata needed for retrieval. The processed output is written to S3 (`processed/`) as structured JSON. That data is then synced into a Bedrock Knowledge Base, where it’s embedded and indexed. The key idea is separation of concerns: raw data is preserved, processing is repeatable, and indexing is managed by AWS.

```mermaid
flowchart TB
  %% =========================
  %% Data Ingestion + Indexing
  %% =========================

  A[PubMed] -->|ESearch / EFetch| B[Local Ingest Notebook or Lambda]
  B -->|Raw text| S3Raw[(S3: raw/)]

  subgraph AWS["AWS"]
    direction TB

    S3Raw -->|Trigger / Batch Process| P[Processing Notebook or Lambda]
    P -->|Processed JSON| S3Processed[(S3: processed/)]
    S3Processed -->|Sync| KB[Bedrock Knowledge Base]
  end

  %% =========================
  %% Styling
  %% =========================
  classDef aws fill:#f7f7f7,stroke:#3a3a3a,stroke-width:1.6px,rx:8,ry:8;
  classDef external fill:#ffffff,stroke:#3a3a3a,stroke-width:1.6px,rx:8,ry:8;
  classDef storage fill:#ffffff,stroke:#3a3a3a,stroke-width:1.6px,rx:18,ry:18;

  class A,B external;
  class AWS,P,KB aws;
  class S3Raw,S3Processed storage;
```

---

## 3. Bedrock Zoomed In

The flow starts in the Lambda (`rag_query`), which is responsible only for orchestration, not retrieval logic. The Lambda calls Bedrock Agent Runtime using the RetrieveAndGenerate API. Bedrock pulls documents from the Knowledge Base, which is backed by an S3 `processed/` prefix defined in Terraform. During ingestion, the Knowledge Base chunks the documents and generates embeddings using a Bedrock-managed default embedding model. Those embeddings are stored in OpenSearch Serverless, which acts as the vector store. At query time, Bedrock performs a top-k similarity search against the vector store to find the most relevant chunks. The retrieved context is then used to augment the prompt sent to the foundation model. The Claude 3.5 Sonnet model generates an answer grounded in the retrieved content. Bedrock returns the answer along with citations, which the Lambda passes back to the application.

```mermaid
flowchart TB
  %% =========================
  %% Bedrock Zoom-in
  %% =========================

  S3["S3 (processed/) aws_s3_bucket.data s3_inclusion_prefixes=processed/"]
  LAMBDA["Lambda aws_lambda_function.rag_query"]

  subgraph BEDROCK["AWS Bedrock"]
    direction TB

    KBR["Bedrock Agent Runtime boto3.client('bedrock-agent-runtime') RetrieveAndGenerate"]
    KB["Knowledge Base module.bedrock.default_kb_identifier"]

    subgraph VSTORE["Vector Store (OpenSearch)"]
      direction TB
      AOSS["AOSS collection module.bedrock.default_collection.name"]
    end

    EMB["Embeddings (Bedrock-managed default)"]
    LLM["Foundation Model var.bedrock_model_arn claude-3.5-sonnet"]

    %% Indexing / ingestion path
    S3 -->|Ingest documents| KB
    KB -->|Chunk + embed| EMB
    EMB -->|Write vectors| AOSS

    %% Query path (runtime)
    KBR -->|Retrieve top-k| KB
    KB <-->|Similarity search| AOSS
    KBR -->|Augment prompt| LLM
  end

  %% Lambda orchestration
  LAMBDA -->|Call RetrieveAndGenerate| KBR
  KBR -->|Answer + citations| LAMBDA

  %% Styling
  classDef aws fill:#f7f7f7,stroke:#3a3a3a,stroke-width:1.6px,rx:8,ry:8;
  classDef lambda fill:#fff6e8,stroke:#b26a00,stroke-width:1.6px,rx:8,ry:8;
  classDef storage fill:#ffffff,stroke:#3a3a3a,stroke-width:1.6px,rx:18,ry:18;

  class BEDROCK,KBR,KB,AOSS,EMB,LLM aws;
  class LAMBDA lambda;
  class S3 storage;
```
