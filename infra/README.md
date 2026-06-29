# 🏗️ Infrastructure & Deployment

<div align="center">

![Docker](https://img.shields.io/badge/Docker-Compose_v2-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![K8s](https://img.shields.io/badge/Kubernetes-Manifests-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Prometheus](https://img.shields.io/badge/Observability-Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)

**Infrastructure as Code (IaC) for Local, Edge, and Production environments.**

[⬅️ Back to Root](../README.md)

</div>

---

## 1. Executive Overview

### Purpose
The `infra/` module defines the deployment architecture constraint bounds using Infrastructure as Code (IaC). It manages the containerization strategy and orchestration manifests for the entire MLOps system.

### Business & Technical Problems Solved
- **Business**: Eliminates "it works on my machine" syndromes, accelerating Time-To-Market (TTM) for clinical model updates.
- **Technical**: Provides a declarative, immutable definition of the deployment topology. Standardizes network boundaries, persistence layers, and service discovery across local Docker Compose and production Kubernetes clusters.

### Role Within the System
The foundational runtime backbone. It provisions the isolated network meshes and computes nodes required by the Frontend, Inference API, and Observability stack.

---

## 2. System Context & Architecture

### Deployment Context Diagram

```mermaid
graph TD
    subgraph K8s Cluster [Production Kubernetes Cluster]
        Namespace(NS: mlops-system)
        
        subgraph Compute Layer
             Pod1([Frontend Pods])
             Pod2([Inference API Pods])
        end
        
        subgraph Logging & Metrics
             Pod3([Prometheus Pod])
             Pod4([Grafana Pod])
        end
        
        Namespace --> Pod1
        Namespace --> Pod2
        Namespace --> Pod3
        Namespace --> Pod4
    end

    Ingress[Nginx Ingress Controller] -->|Routes| Pod1
    Ingress -->|Routes /api| Pod2
```

### Architectural Style
- **Platform-Agnostic Microservices**: Architecture is agnostic to the underlying cloud provider (AWS/GCP/Azure) relying purely on standard Kubernetes primitives or Docker APIs.
- **Stateless Application Layer**: Frontend and API containers hold zero state, pushing state entirely to Volume Mounts (Monitoring series data).

---

## 3. Component-Level Design

### Core Directories

1. **`infra/docker/`**
   - **Responsibility**: Local/Edge deployment definitions. Contains `Dockerfile.inference`, `Dockerfile.frontend`, `Dockerfile.training`, `docker-compose.yml`, and `nginx.conf`.
2. **`infra/k8s/`**
   - **Responsibility**: Production cluster definitions mapping equivalent compose architectures into Scalable Deployments, Services, and Namespaces.

---

## 4. Infrastructure & Deployment

### Docker Compose Topology (Local/Edge)

| Service | Container Name | Port | Description |
| :--- | :--- | :--- | :--- |
| `inference-api` | `mlops-inference-api` | `8000` | The core Python prediction engine. |
| `frontend` | `mlops-frontend` | `8080` | Nginx serving the Web UI. |
| `prometheus` | `mlops-prometheus` | `9090` | Time-series metric collector. |
| `grafana` | `mlops-grafana` | `3000` | Visualization dashboard server. |

**Command Structure**:
```bash
docker-compose -f infra/docker/docker-compose.yml up --build -d
```

### Kubernetes Topology (Production)
Deployments are separated logically into individual YAML files to prevent blast radii overlapping.
- `namespace.yaml`: Hard boundary `mlops-system`.
- `inference-deployment.yaml` / `inference-service.yaml`: API compute and service discovery.
- `frontend-deployment.yaml` / `frontend-service.yaml`: Web UI pods and NodePort (30880).
- `prometheus-deployment.yaml` / `prometheus-service.yaml` / `prometheus-configmap.yaml`: Metric collection.
- `grafana-deployment.yaml` / `grafana-service.yaml`: Dashboard visualization.

---

## 5. Security Architecture

- **Rootless Containers**: Dockerfiles enforce `USER appuser` or `USER nginx` directives. Processes cannot exploit host-level kernel vulnerabilities trivially.
- **Network Isolation**: By default, Docker Compose deploys a custom bridge `mlops-network`. Containers do not expose ports automatically; only mapped host ports allow ingress.
- **Immutable Tags**: Production manifests should replace `latest` tags with explicit SHA digests to prevent upstream poisoning.

---

## 6. Performance & Scalability

- **Horizontal Pod Autoscaling (HPA)**: The `/inference` service is explicitly stateless. K8s manifests can be augmented with HPA scaled on target `CPU=70%` to spawn multiple API replicas during high HTTP load.
- **Resource Limits**: (Future recommendation) Add CPU/Memory bounds (`resources.requests` and `limits`) to preventing Noisy Neighbor out-of-memory (OOM) cluster crashes.

---

## 7. Reliability & Fault Tolerance

- **Liveness Probes**: The inference container executes an internal `HEALTHCHECK` using a localized Python HTTP request to `/health` every 30 seconds.
- **Restart Policies**: Compose dictates `restart: unless-stopped` to auto-recover from transient segfaults or kernel reboots.

---

## 8. Observability

- **Prometheus Volume Retention**: Explicitly mounted to a persistent volume `prometheus-data` to survive container cycling. Data retention defaults to 7 days to cap disk bloat.
- **Dashboards**: Grafana provisioning auto-loads structured dashboards referencing the Prometheus internal DNS target.

---

## 9. Testing Strategy
Currently tested via `docker-compose up` smoke testing and manual validation of endpoint HTTP 200s. 
*Recommendation: Implement `kube-val` or `conftest` to run static OPA (Open Policy Agent) checks on YAML files in CI.*

---

## 10. Configuration & Environment Variables

| Variable | Deployment | Default | Description |
| :--- | :--- | :--- | :--- |
| `GRAFANA_ADMIN_PASSWORD` | Docker/K8s | `changeme` | Root access for Dashboards. MUST be changed in Production. |
| `PROMETHEUS_RETENTION` | Docker | `7d` | Storage duration ceiling. |

---

## 11. Development Guide

### Applying Kubernetes Locally (Requires Minikube/Docker Desktop K8s)
```bash
kubectl apply -f infra/k8s/00-namespace.yaml
kubectl apply -f infra/k8s/
```
To observe live cluster spin-up:
```bash
kubectl get pods -n mlops-system -w
```

---

## 12. Future Improvements

- **Helm Charts**: Abstracting the raw K8s YAMLs into Helm Charts (`values.yaml`) to allow dynamic environment templating (e.g., Staging vs. Prod clusters).
- **Terraform Integration**: Extend IaC to provision the underlying hardware (EKS/GKE nodes, VPCs) prior to applying workloads.