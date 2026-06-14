# ComplianceAI – Multi-Agent Policy Compliance Checker

## Overview

ComplianceAI is an AI-powered policy compliance assessment platform developed for the Capgemini Agentify Buildathon. The solution automatically analyzes organizational documents, detects policy violations, maps findings to relevant regulations, and generates actionable compliance recommendations.

The platform combines a FastAPI backend, React frontend, vector-based policy retrieval, and a multi-agent AI council to provide intelligent compliance auditing and risk assessment.

---

## Problem Statement

Organizations handle large volumes of policies, contracts, SOPs, employee guidelines, and compliance documents. Manual compliance reviews are:

* Time-consuming
* Error-prone
* Difficult to scale
* Expensive to maintain

ComplianceAI automates the review process by identifying violations, assigning risk levels, generating remediation guidance, and maintaining an auditable compliance trail.

---

## Key Features

### AI-Powered Compliance Analysis

* Automated document ingestion
* Policy violation detection
* Risk categorization
* Compliance scoring

### Multi-Agent Council Architecture

The platform utilizes multiple AI agents that collaborate during analysis:

* Compliance Agent
* Security Agent
* Risk Assessment Agent
* Regulatory Mapping Agent
* Recommendation Agent

### Regulatory Mapping

Maps findings against:

* Internal policies
* Compliance rules
* Regulatory requirements
* Organizational governance standards

### Vector Search & Knowledge Retrieval

* ChromaDB vector database
* Semantic policy retrieval
* Context-aware compliance analysis

### Compliance Dashboard

* Compliance score visualization
* Trend monitoring
* Violation analytics
* Audit history

### Audit & Governance

* Audit trail generation
* Historical scan records
* Tenant-based segregation
* Role-based access control

### Report Generation

* Detailed compliance reports
* Risk summaries
* Remediation recommendations
* Executive-level compliance insights

---

## Solution Architecture

```text
                    ┌────────────────────┐
                    │ React Frontend     │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ FastAPI Backend    │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼

 ┌─────────────┐     ┌────────────────┐    ┌─────────────┐
 │ Parser      │     │ Multi-Agent    │    │ ChromaDB    │
 │ Engine      │────►│ Council        │◄──►│ Vector Store│
 └─────────────┘     └────────────────┘    └─────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Compliance Engine  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Reports & Audit    │
                    └────────────────────┘
```

---

## Technology Stack

### Frontend

* React
* Vite
* JavaScript
* HTML/CSS

### Backend

* FastAPI
* Python
* Uvicorn

### Database

* SQLite
* ChromaDB

### AI & NLP

* OpenAI Models
* Embedding Models
* Semantic Retrieval

### Security

* Role-Based Access Control (RBAC)
* Tenant Isolation
* Audit Logging

---

## Project Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── rbac.py
│   │
│   └── pipeline/
│       ├── agents.py
│       ├── orchestrator.py
│       ├── parser.py
│       ├── pdf_generator.py
│       ├── precedence.py
│       ├── regmap.py
│       ├── rules.py
│       └── vectorstore.py
│
└── data/

frontend/
│
├── src/
├── public/
└── components/
```

---

## Workflow

### Step 1 – Upload Document

Users upload a policy, SOP, contract, or compliance document.

### Step 2 – Parsing

The parser extracts textual content from the document.

### Step 3 – Knowledge Retrieval

Relevant policy sections are retrieved from the vector database.

### Step 4 – Multi-Agent Review

Multiple AI agents independently analyze the document.

### Step 5 – Conflict Resolution

Agent outputs are consolidated and prioritized.

### Step 6 – Compliance Scoring

The system calculates:

* Compliance Score
* Risk Score
* Severity Distribution

### Step 7 – Report Generation

A detailed compliance report is generated with remediation recommendations.

---

## API Highlights

### Health Check

```http
GET /api/health
```

### Document Scan

```http
POST /api/scan
```

### Compliance Trends

```http
GET /api/compliance/trend
```

### Audit Records

```http
GET /api/audit
```

---

## Innovation

### Multi-Agent Compliance Council

Instead of relying on a single AI model, multiple specialized agents collaborate to improve accuracy and reduce hallucinations.

### Retrieval-Augmented Compliance Analysis

Compliance decisions are supported using policy context retrieved from the vector knowledge base.

### Explainable Compliance Findings

Every violation includes:

* Severity
* Justification
* Recommended remediation

### Enterprise Readiness

* Auditability
* Governance support
* Multi-tenant architecture
* Role-based permissions

---

## Future Enhancements

* Real-time compliance monitoring
* Regulatory update tracking
* Automated remediation workflows
* Explainable AI dashboards
* Advanced analytics and forecasting
* Integration with enterprise document repositories

---

## Team

Developed as part of the Capgemini Agentify Buildathon.

ComplianceAI demonstrates how multi-agent AI systems can streamline compliance operations, improve governance, and reduce regulatory risk through intelligent document analysis and automated policy assessment.