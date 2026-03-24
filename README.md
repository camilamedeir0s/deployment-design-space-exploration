# Exploring the Deployment Design Space of Microservice Applications

This repository contains the artifacts and scripts to reproduce the methodology presented in the ECSA 2026 submission:

"Exploring the Deployment Design Space of Microservice Applications"

The approach models a microservice application as a weighted service interaction graph and explores the deployment design space using two structural forces:

- Communication (inter-service interaction across boundaries)
- Contention (resource concentration within execution units)

The workflow follows a fully reproducible pipeline, from data collection to structural analysis and pattern extraction.

---

## Repository Structure
```
data/
  raw/                  # Input data extracted from profiling (Prometheus, Jaeger)
  processed/            # Generated results (scores, Pareto, patterns)

scripts/
  compute_exhaustive_scores.py
  generate_pareto.py
  extract_structural_patterns.py

experiments/
  k6/
    scenarios/          # Load testing scenarios
    scripts/            # Automation scripts
  deployments/
    kmeans_validation/  # Deployment manifests for validation
```
---

## Methodology Overview

The methodology follows four main steps:

1. Profiling and Data Extraction  
2. Exhaustive Configuration Scoring  
3. Pareto Frontier Extraction  
4. Structural Pattern Analysis  

An optional fifth step performs runtime validation using sampled configurations.

---

## 1. Profiling and Data Extraction

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

## 2. Exhaustive Configuration Scoring

All possible deployment configurations (partitions of services) are evaluated.

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
- position (global ranking)
- config_str (service grouping)

---

## 3. Pareto Frontier Extraction

Extract the non-dominated configurations in the (communication, contention) space.

Run:

```
python scripts/generate_pareto.py
```

### Output
```
data/processed/pareto_2d_alpha_05.csv
```

This file contains the Pareto-efficient configurations used for structural analysis.

---

## 4. Structural Pattern Extraction

Analyze recurring co-location patterns within different structural regimes.

Run:

```
python scripts/extract_structural_patterns.py
```

### Outputs

Stored in `data/processed/`:

- Heatmaps (images)
- Co-location probability matrices (CSV)
- Markdown report describing detected patterns

This step identifies stable structural patterns, such as frequently co-located service groups.

---

## 5. (Optional) Runtime Validation via K-Means Sampling

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
