#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <config_name>"
  exit 1
fi

CONFIG_NAME="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

K6_SCRIPT="${K6_DIR}/scenarios/online-boutique-user-flow.js"
RESULTS_DIR="${K6_DIR}/results/${CONFIG_NAME}"

mkdir -p "${RESULTS_DIR}"

LATENCY="$(kubectl describe networkchaos network-emulation 2>/dev/null | grep 'Latency:' | head -n 1 | awk '{print $2}')"
LATENCY="${LATENCY:-0ms}"

ENDPOINT="$(kubectl get svc -o json | jq -r '
  .items[]
  | select(.metadata.name | startswith("boutique"))
  | (.status.loadBalancer.ingress[0].ip // .status.loadBalancer.ingress[0].hostname // empty)
' | head -n 1)"

if [ -z "${ENDPOINT}" ]; then
  echo "Error: could not find the service endpoint."
  exit 1
fi

HOST="http://${ENDPOINT}"
OUTFILE="${RESULTS_DIR}/${CONFIG_NAME}-${LATENCY}-3000.json"

echo "Host: ${HOST}"
echo "Output: ${OUTFILE}"

k6 run \
  --env BASE_URL="${HOST}" \
  --env OUTPUT="${OUTFILE}" \
  --env VUS=3000 \
  --env DURATION=4m \
  "${K6_SCRIPT}"