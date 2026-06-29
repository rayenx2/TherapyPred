# 📚 Documentation Hub

<div align="center">

![Documentation](https://img.shields.io/badge/Docs-Diátaxis-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Up_to_Date-green?style=for-the-badge)

**Central index for the MLOps System documentation.**

[⬅️ Back to Root](../README.md)

</div>

---

## 1. Executive Overview

### Purpose
The Documentation Hub acts as the centralized root node for exploring the architectural and functional documentation of the MLOps System. It indexes domain-specific README files across the repository, ensuring technical teams can rapidly locate domain-specific details.

### Business & Technical Problems Solved
Without a centralized documentation index, complex repositories devolve into tribal knowledge, increasing onboarding time and the risk of architectural violations. This hub solves the discoverability problem by mapping sub-domains securely.

### Role Within the System
It provides navigation boundaries, directing Architects towards System Design, Devs towards pipelines, and Ops towards infrastructure manifests.

---

## 2. System Context & Architecture

### Cross-System Documentation Flow
The documentation architecture maps directly to the repository’s modular design.

```mermaid
graph TD
    Root[Root README] --> Hub(Docs Hub)
    Hub --> Backend[Inference & Models]
    Hub --> DataOps[Data & Pipelines]
    Hub --> FrontendOps[Frontend]
    Hub --> InfraOps[Infra & Monitoring]
    Hub --> TestOps[Automated Tests]
```

### Design Principles Applied
We strictly follow the **Diátaxis Framework**:
1. **Tutorials**: Onboarding & fast-starts (Root README).
2. **How-To Guides**: Action-oriented steps (Per module).
3. **Reference**: Technical lookup (Schemas & Configs).
4. **Explanation**: Context and 'Why' (Architecture sections).

---

## 3. Core Module Navigation

| Component | Link | Responsibility |
| :--- | :--- | :--- |
| **Data** | [README](../data/README.md) | Schema definitions, DVC tracking, and data constraints. |
| **Pipelines** | [README](../pipelines/README.md) | The DAG execution (Ingest → Validate → Train → Evaluate). |
| **Training** | [README](../training/README.md) | Random Forest algorithm, hyperparameters, and logic. |
| **Models** | [README](../models/README.md) | Artifact versioning (`.joblib`) and serialization. |
| **Metrics** | [README](../metrics/README.md) | Performance reports (`scores.json`) and KPI definitions. |
| **Inference** | [README](../inference/README.md) | FastAPI service, endpoints, and validation schemas. |
| **Frontend** | [README](../frontend/README.md) | Web UI logic, DOM manipulation, and static asset serving. |
| **Infrastructure** | [README](../infra/README.md) | Docker, Kubernetes manifests, and network topology. |
| **Monitoring** | [README](../monitoring/README.md) | Prometheus & Grafana stack configuration. |
| **Validation** | [README](../validation/README.md) | CI/CD gates and release checklists. |
| **Tests** | [README](../tests/README.md) | Automated unit and integration testing boundaries. |