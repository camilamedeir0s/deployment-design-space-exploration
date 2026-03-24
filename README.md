# Exploring the Deployment Design Space of Microservice Applications

This repository contains the artifacts and scripts to reproduce the methodology presented in the ECSA 2026 submission:

"Exploring the Deployment Design Space of Microservice Applications"

The approach models a microservice application as a weighted service interaction graph and explores the deployment design space using two structural forces:

- Communication (inter-service interaction across boundaries)
- Contention (resource concentration within execution units)

The workflow follows a reproducible pipeline aligned with the methodological structure described in the paper.

---

## Repository Structure
```
data/
  raw/                  # Input data extracted from profiling (Prometheus, Jaeger)
  processed/            # Generated results (scores, Pareto, patterns)

scripts/

experiments/
  k6/
    scenarios/          # Load testing scenarios
    scripts/            # Automation scripts
  deployments/
    kmeans_validation/  # Deployment manifests for validation
```
---

## Methodology Overview

The methodology follows six main steps:

Profiling and Weight Extraction
Architectural Model Definition
Exhaustive Configuration Evaluation
Structural Analysis (Score, Pareto, Knee)
Structural Pattern Extraction
(Optional) Runtime Validation

---

## 1. Profiling and Weight Extraction

The structural model requires two inputs:

- Inter-service communication weights (edges)
- Service resource demand weights (nodes)

These are extracted from a **single profiling execution** of a fully distributed deployment (one service per execution unit).

### Load Testing

Workload is generated using k6:

- Scenarios: `experiments/k6/scenarios`
- Automation scripts: `experiments/k6/scripts`  

The number of virtual users (VUs) should be adjusted according to the available infrastructure capacity.

### Communication Weights (Jaeger)

- Source: distributed traces
- Metric: number of calls between services per user action
- Aggregation:

```
W(u → v) = Σ_f π_f * calls_f(u → v)
```

Where:
- `f` = user-facing function
- `π_f` = relative frequency in workload

### Resource Weights (Prometheus)

Collected per service (per pod):

- CPU (millicores)
- Memory (MiB)

Both are computed using **P95 over time windows**, then normalized:

```
cpu_norm = CPU_p95 / 1000
mem_norm = Mem_p95 / 512

w_s = max(cpu_norm, mem_norm)
```

These values represent the structural resource demand of each service.

---

## 2. Architectural Model Definition

The application is modeled as a weighted directed graph:
- Nodes represent services
- Edges represent inter-service calls
- Weights encode communication intensity and resource demand

Two structural metrics are defined for each deployment configuration:

- Communication: fraction of interaction crossing execution boundaries
- Contention: maximum resource concentration within a group

A composite score is defined as:
```
score(C) = α · communication(C) + (1 − α) · contention(C)
```
This model enables evaluating configurations analytically without executing them.

---

## 3. Exhaustive Configuration Evaluation

All possible deployment configurations (service partitions) are evaluated.

Run:

```bash
python scripts/compute_exhaustive_scores.py
```

### Output

Generated in:
```
data/processed/exhaustive_configurations_alpha_05.csv
```

Each configuration contains:

- communication
- contention
- score
- rank
- config_str (service grouping)

---

## 4. Structural Analysis (Score, Pareto, Knee)

The configuration space is analyzed jointly using:

- Score-based ordering
- Pareto frontier (communication vs contention)
- Knee-point detection

Run:
```
python scripts/generate_pareto.py
```
### Output

```
data/processed/pareto_2d_alpha_05.csv
```

This step identifies structurally efficient configurations and separates distinct trade-off regimes.

---

## 5. Structural Pattern Extraction

Patterns are extracted based on structural regimes defined in the previous step.

Run:

```
python scripts/extract_structural_patterns.py
```

### Outputs
Stored in `data/processed/`:

- Heatmaps (images)
- Co-location probability matrices (CSV)
- Markdown report describing detected patterns

These patterns reveal recurring service groupings in different regions of the deployment space.

---

## 6. (Optional) Runtime Validation via K-Means Sampling

To validate the structural model against runtime behavior, a subset of configurations can be selected using clustering.

### Step 1: Generate representative configurations

Run the K-Means selection script (located in `scripts/`).

### Step 2: Deploy configurations

Deployment manifests are available in:

```
experiments/deployments/kmeans_validation/
```

These are generated using Service Weaver.

### Step 3: Execute load tests

Reuse k6 scenarios to evaluate:

- P95 latency
- Sensitivity under network delay

⚠️ **Important (Minikube users)**:
When running the full pipeline using:
```
./run_k6_pipeline.sh
```

You must execute the following command in a separate terminal:
```
minikube tunnel
```

This is required to expose LoadBalancer services and allow the test scripts to correctly reach the application endpoint.

---

## Notes on Reproducibility

- Structural weights are extracted from a single profiling execution
- All configurations are evaluated analytically without re-deployment
- Runtime validation is performed on a small, structurally diverse subset
- This approach assumes that communication patterns and resource demand remain stable under the same workload profile

---

## Key Insight

The deployment design space exhibits:

- Structured trade-offs between communication and contention
- Pareto-optimal regions
- Stable co-location patterns across configurations

This enables reducing the search space before expensive runtime experimentation.
