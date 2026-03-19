#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${K6_DIR}/../.." && pwd)"

RUN_ONCE_SCRIPT="${SCRIPT_DIR}/run_k6_once.sh"

# Adjust these paths to match your repository structure
DEPLOYMENTS_DIR="${REPO_ROOT}/deployments/distributions"
LATENCY_FILE="${REPO_ROOT}/infra/chaos-mesh/network-latency.yaml"

# Example configs; replace with yours
CONFIGS=(
  "colocated"
)

LATENCIES=(
  "0ms"
  "100ms"
  "200ms"
)

for CONFIG in "${CONFIGS[@]}"; do
  echo "========================================"
  echo "Applying configuration: ${CONFIG}"
  echo "========================================"

  CONFIG_PATH="${DEPLOYMENTS_DIR}/${CONFIG}"

  if [ ! -d "${CONFIG_PATH}" ]; then
    echo "Error: configuration directory not found: ${CONFIG_PATH}"
    exit 1
  fi

  kubectl apply -f "${CONFIG_PATH}"
  sleep 10

  for LAT in "${LATENCIES[@]}"; do
    echo "Running test for config=${CONFIG}, latency=${LAT}"

    if [ "${LAT}" != "0ms" ]; then
      sed -i "s/latency: .*/latency: '${LAT}'/" "${LATENCY_FILE}"
      kubectl apply -f "${LATENCY_FILE}"
      sleep 5
    fi

    "${RUN_ONCE_SCRIPT}" "${CONFIG}"

    if [ "${LAT}" != "0ms" ]; then
      kubectl delete -f "${LATENCY_FILE}" --ignore-not-found=true
    fi
  done

  echo "Deleting configuration: ${CONFIG}"
  kubectl delete -f "${CONFIG_PATH}" --ignore-not-found=true

  echo "Waiting for stabilization..."
  sleep 20
done

echo "========================================"
echo "Pipeline completed"
echo "========================================"