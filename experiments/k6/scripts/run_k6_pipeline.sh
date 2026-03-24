#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${K6_DIR}/../.." && pwd)"

RUN_ONCE_SCRIPT="${SCRIPT_DIR}/run_k6_once.sh"

# Adjust these paths to match your repository structure
DEPLOYMENTS_DIR="${REPO_ROOT}/experiments/deployments/kmeans_validation"
LATENCY_FILE="${REPO_ROOT}/experiments/chaos-mesh/networkchaos.yaml"

# Example configs; replace with yours
CONFIGS=(
  "ad-checkout-currency-email-main-payment-productcat-recommendation_cart_shipping"
  "ad-currency-email-main-payment-productcat_cart-checkout-recommendation-shipping"
  "ad-email_cart_checkout-currency-main-productcat_payment-shipping_recommendation"
  "ad-checkout-payment_cart-main-productcat-shipping_currency_email-recommendation"
  "ad-main-productcat_cart-checkout-email-shipping_currency-payment_recommendation"
  "ad_cart-shipping_checkout-currency-email_main-payment-productcat_recommendation"
  "ad-cart-currency-main_checkout_email-shipping_payment-productcat_recommendation"
  "ad-currency-main-payment_cart-checkout-recommendation-shipping_email_productcat"
  "ad-checkout-email_cart-productcat_currency-main-payment_recommendation-shipping"
  "ad-checkout-email-main-recommendation-shipping_cart_currency_payment-productcat"
  "ad-email-main-payment-shipping_cart-checkout_currency_productcat-recommendation"
  "ad-main_cart_checkout-currency-payment-shipping_email-productcat_recommendation"
  "ad-main-shipping_cart-payment_checkout_currency-recommendation_email_productcat"
  "ad_cart_checkout_currency_email_main-shipping_payment_productcat_recommendation"
  "ad-recommendation_cart-checkout_currency-productcat-shipping_email-payment_main"
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

  kubectl apply -k "${CONFIG_PATH}"
  sleep 10

  for LAT in "${LATENCIES[@]}"; do
    echo "Running test for config=${CONFIG}, latency=${LAT}"

    if [ "${LAT}" != "0ms" ]; then
      sed -i "s/latency: .*/latency: '${LAT}'/" "${LATENCY_FILE}"
      kubectl apply -f "${LATENCY_FILE}"
      sleep 5
    fi

    bash "${RUN_ONCE_SCRIPT}" "${CONFIG}"

    if [ "${LAT}" != "0ms" ]; then
      kubectl delete -f "${LATENCY_FILE}" --ignore-not-found=true
    fi
  done

  echo "Deleting configuration: ${CONFIG}"
  kubectl delete -k "${CONFIG_PATH}" --ignore-not-found=true

  echo "Waiting for stabilization..."
  sleep 20
done

echo "========================================"
echo "Pipeline completed"
echo "========================================"