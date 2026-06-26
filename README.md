# Policy Compliance Checker

An AI-powered enterprise compliance platform that automates policy validation by analyzing organizational documents against regulatory and internal policies. The system combines Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and deterministic rule-based validation to identify compliance violations, generate remediation recommendations, and produce audit-ready reports.

**Developed for the Capgemini Agentic AI Buildathon 2026**

---

## Overview

Policy Compliance Checker enables organizations to automate document compliance reviews by comparing uploaded documents against internal policies and regulatory frameworks. The platform provides explainable compliance analysis with policy clause references, severity classification, remediation suggestions, and audit reporting.

---

## Key Features

- Automated compliance analysis for enterprise documents
- Retrieval-Augmented Generation (RAG) for policy retrieval
- Multi-agent AI framework for policy evaluation
- GDPR and internal policy compliance validation
- Compliance scoring with severity classification
- AI-generated remediation recommendations
- Interactive analytics dashboard
- Compliance trend monitoring
- Downloadable audit reports
- Role-Based Access Control (RBAC)
- Custom policy management

---

## Technology Stack

| Layer | Technologies |
|--------|--------------|
| Frontend | React, Vite, JavaScript |
| Backend | FastAPI, Python, SQLAlchemy, Pydantic |
| AI Framework | LangChain, ChromaDB, Groq API, Llama 3 |
| Database | SQLite |
| Deployment | Docker, Docker Compose |

---

## System Architecture

```
                 User Upload
                      │
                      ▼
            Document Parsing Engine
                      │
                      ▼
          Policy Retrieval (RAG Pipeline)
                      │
                      ▼
          Multi-Agent Compliance Analysis
      ┌─────────────────────────────────┐
      │ • GDPR Compliance Agent         │
      │ • Security Policy Agent         │
      │ • Internal Policy Agent         │
      │ • Legal Compliance Agent        │
      └─────────────────────────────────┘
                      │
                      ▼
        Compliance Scoring & Validation
                      │
                      ▼
        Dashboard • Reports • Audit Trail
```

---

## Project Structure

```
policy-compliance-checker/
│
├── backend/
│   ├── app/
│   ├── data/
│   ├── demo_docs/
│   ├── policies/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── screenshots/
├── docker-compose.yml
├── README.md
└── run.sh
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/<your-username>/policy-compliance-checker.git

cd policy-compliance-checker
```

---

### Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows**

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
cd backend

pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

```
http://127.0.0.1:8000
```

API Documentation:

```
http://127.0.0.1:8000/docs
```

---

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend URL:

```
http://localhost:5173
```

---

## Docker Deployment

Run the complete application using Docker:

```bash
docker compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|----------|-----------------------------|--------------------------------|
| GET | `/api/health` | Health check |
| POST | `/api/scan` | Upload and analyze document |
| GET | `/api/scans` | Retrieve scan history |
| GET | `/api/dashboard` | Dashboard analytics |
| GET | `/api/audit` | Audit logs |
| GET | `/api/compliance/trend` | Compliance trends |
| POST | `/api/policy/custom` | Create custom policy |
| GET | `/api/policy/retrieve` | Retrieve policies |
| POST | `/api/scan/{scan_id}/remediate` | Generate remediation |
| DELETE | `/api/scan/{scan_id}` | Delete scan |

---

## Workflow

1. Upload a policy or enterprise document.
2. Parse and preprocess document contents.
3. Retrieve relevant policy clauses using RAG.
4. Perform multi-agent compliance analysis.
5. Detect policy violations and assign severity.
6. Generate remediation recommendations.
7. Produce compliance reports and audit logs.

---

## Screenshots

Include application screenshots inside the `screenshots/` directory.

```
screenshots/
├── dashboard.png
├── upload.png
├── report.png
└── analytics.png
```

---

## Team

**Team NexusZenith**

- Sounak Chatterjee
- Soumyadeep Mitra
- Soutisha Mondal
- Sohini Roy
- Sukanya Barui

---

## Future Enhancements

- Support for ISO 27001, HIPAA, and PCI-DSS
- Cloud-native deployment
- Enterprise authentication (OAuth/SSO)
- Multi-language document analysis
- Real-time compliance monitoring
- Advanced analytics and reporting

---

## License

Developed as part of the **Capgemini Agentic AI Buildathon 2026** for educational and demonstration purposes.
