# 🚀 Universal AI Data Integration & Validation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![.NET](https://img.shields.io/badge/.NET-8.0-purple.svg)](https://dotnet.microsoft.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5.svg)](https://kubernetes.io)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)](https://github.com/features/actions)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Enabled-orange.svg)](https://opentelemetry.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> An enterprise-grade, AI-powered data integration and validation platform supporting 50+ data sources, intelligent ETL/ELT pipelines, real-time monitoring, and a modern React dashboard. Built with Python, .NET, and React following Clean Architecture, DDD, and microservices patterns.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Services](#services)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The **Universal AI Data Integration & Validation Platform** is a production-ready, open-source enterprise SaaS platform that enables organizations to:

- **Ingest** data from 50+ heterogeneous sources (REST, SOAP, GraphQL, CSV, Excel, PDF, databases, message queues, cloud storage, IoT, healthcare, financial)
- **Validate** data using AI-assisted rules, business logic, and domain-specific validators (FHIR, HL7, GST, PAN, IBAN, etc.)
- **Transform** and enrich data using configurable pipelines with AI-powered mapping
- **Deliver** to 20+ destinations including data warehouses, APIs, and notification channels
- **Monitor** pipeline executions with real-time dashboards, alerts, and observability
- **Govern** data with lineage tracking, audit logs, RBAC, and approval workflows

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (.NET)                          │
│                    Rate Limiting | Auth | Routing                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼───────┐  ┌──────▼───────┐
│  Auth Service│  │  User Service  │  │  Reporting   │
│   (.NET)     │  │   (.NET)       │  │  Service     │
└──────────────┘  └────────────────┘  └──────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                     Python Microservices                          │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │  Ingestion  │ │  Validation  │ │    Transformation        │  │
│  │  Service    │ │  Service     │ │    Service               │  │
│  └─────────────┘ └──────────────┘ └──────────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │  AI Service │ │  PDF Service │ │    Analytics Service     │  │
│  └─────────────┘ └──────────────┘ └──────────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐                               │
│  │  Scheduling │ │ Notification │                               │
│  │  Service    │ │  Service     │                               │
│  └─────────────┘ └──────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                     Data & Message Layer                          │
│  PostgreSQL │ MongoDB │ Redis │ ElasticSearch │ Kafka │ ChromaDB  │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Data Sources (50+)
- REST, SOAP, GraphQL APIs
- CSV, Excel, PDF (with OCR), XML, JSON, Parquet, Avro, ORC
- Google Sheets, AWS S3, Azure Blob, FTP/SFTP
- MySQL, PostgreSQL, SQL Server, Oracle, MongoDB, Redis
- Kafka, RabbitMQ, Azure Service Bus, Amazon SQS, Google Pub/Sub
- Webhooks, Email Attachments, Manual/Drag-Drop Upload
- Healthcare: FHIR APIs, HL7 Messages, EDI Files
- Financial: Invoices, Bank Statements, Purchase Orders
- IoT Streaming Data

### AI Features
- Document Classification & Entity Extraction (NER)
- Invoice, Medical Report & Contract Understanding
- Fraud Detection & Risk Analysis
- Auto Schema Mapping & Validation
- Anomaly Detection & Quality Scoring
- AI Chat Assistant with RAG
- Natural Language Pipeline Querying
- Predictive Failure Detection

### Pipeline Orchestration
- Visual Drag-and-Drop Pipeline Designer
- Prefect, Airflow, Dagster support
- Scheduling, Retries, Checkpointing
- CDC, Incremental Loads, Streaming ETL
- Approval Workflows (Maker-Checker)

### Security
- JWT + OAuth2 + MFA
- RBAC with granular permissions
- PII Detection & Masking
- Secrets Management (Vault)
- OWASP protections, Audit Logging

### Observability
- Prometheus + Grafana dashboards
- OpenTelemetry + Jaeger tracing
- ELK Stack for log aggregation
- Real-time pipeline monitoring

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS, ShadCN, Material UI |
| Python Backend | FastAPI, Pydantic v2, SQLAlchemy 2, Beanie, Motor, Celery |
| .NET Backend | ASP.NET Core 8, Minimal APIs, EF Core, SignalR, Hangfire, gRPC |
| Databases | PostgreSQL, MongoDB, Redis, ElasticSearch, ChromaDB, FAISS |
| AI/ML | OpenAI, LangChain, HuggingFace, spaCy, Tesseract OCR |
| Pipelines | Prefect, Apache Airflow, Dagster |
| Messaging | Apache Kafka, RabbitMQ |
| Infrastructure | Docker, Kubernetes, Helm, Terraform |
| CI/CD | GitHub Actions, Azure DevOps |
| Observability | Prometheus, Grafana, Jaeger, ELK Stack, OpenTelemetry |
| Cloud | AWS, Azure, GCP |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- .NET 8 SDK

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/enterprise-ai-data-platform.git
cd enterprise-ai-data-platform
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

### 3. Access Services
| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| API Gateway | http://localhost:8000 |
| Ingestion API | http://localhost:8001/docs |
| Validation API | http://localhost:8002/docs |
| AI Service API | http://localhost:8003/docs |
| Grafana | http://localhost:3001 |
| Kibana | http://localhost:5601 |
| Jaeger UI | http://localhost:16686 |
| Flower (Celery) | http://localhost:5555 |

### 4. Default Credentials
```
Admin: admin@platform.com / Admin@123
Demo:  demo@platform.com  / Demo@123
```

---

## 📁 Project Structure

```
enterprise-ai-data-platform/
├── frontend/                    # Next.js + React + TypeScript
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   ├── components/          # Reusable UI components
│   │   ├── features/            # Feature modules
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities & API clients
│   │   └── types/               # TypeScript types
│   └── ...
├── python-services/
│   ├── ingestion-service/       # Data source connectors
│   ├── validation-service/      # Validation engine
│   ├── transformation-service/  # ETL/ELT engine
│   ├── ai-service/              # AI/ML features
│   ├── pdf-service/             # PDF processing & OCR
│   ├── scheduling-service/      # Pipeline scheduling
│   ├── notification-service/    # Alerts & notifications
│   └── analytics-service/       # Reporting & analytics
├── dotnet-services/
│   ├── auth-service/            # Authentication & authorization
│   ├── user-service/            # User & tenant management
│   ├── gateway-service/         # API gateway
│   └── reporting-service/       # Report generation
├── pipelines/
│   ├── prefect/                 # Prefect flows
│   ├── airflow/                 # Airflow DAGs
│   └── dagster/                 # Dagster assets
├── ai/
│   ├── rag/                     # Retrieval Augmented Generation
│   ├── vector-db/               # Vector database setup
│   ├── embeddings/              # Embedding models
│   ├── document-intelligence/   # Document AI
│   ├── agents/                  # Autonomous AI agents
│   └── prompt-library/          # Prompt templates
├── infrastructure/
│   ├── docker/                  # Dockerfiles
│   ├── kubernetes/              # K8s manifests
│   ├── helm/                    # Helm charts
│   ├── terraform/               # IaC
│   └── github-actions/          # CI/CD workflows
├── databases/                   # Migrations & seeds
├── monitoring/                  # Observability configs
├── testing/                     # Test suites
├── sample-data/                 # Sample datasets
├── scripts/                     # Utility scripts
└── docs/                        # Documentation
```

---

## 🔌 Services

### Python Services

| Service | Port | Description |
|---------|------|-------------|
| ingestion-service | 8001 | Data source connectors & ingestion |
| validation-service | 8002 | Rule-based & AI validation engine |
| transformation-service | 8003 | ETL/ELT transformation engine |
| ai-service | 8004 | AI/ML features & agents |
| pdf-service | 8005 | PDF processing & OCR |
| scheduling-service | 8006 | Pipeline scheduling & orchestration |
| notification-service | 8007 | Alerts, email, Slack, Teams |
| analytics-service | 8008 | Reporting & analytics |

### .NET Services

| Service | Port | Description |
|---------|------|-------------|
| gateway-service | 8000 | API Gateway with rate limiting |
| auth-service | 8010 | JWT/OAuth2 authentication |
| user-service | 8011 | User & tenant management |
| reporting-service | 8012 | Report generation & export |

---

## 📖 API Documentation

- **Swagger UI**: http://localhost:8000/swagger
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infrastructure/kubernetes/
```

### Helm Chart
```bash
helm install ai-platform infrastructure/helm/ai-platform/
```

### Terraform (Cloud)
```bash
cd infrastructure/terraform/aws
terraform init && terraform apply
```

---

## 🧪 Testing

```bash
# Unit tests
pytest testing/unit/ -v

# Integration tests
pytest testing/integration/ -v

# Performance tests
locust -f testing/performance/locustfile.py

# Security tests
bandit -r python-services/
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🗺️ Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for planned features.

---

<p align="center">Built with ❤️ for the enterprise open-source community</p>
