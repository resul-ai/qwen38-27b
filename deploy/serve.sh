#!/usr/bin/env bash
# Bring Qwen3.8-27B vLLM up (or confirm it is already serving) and smoke-test it.
# Requires: curl, python3. Optional: RUNPOD_API_KEY to resume a stopped pod.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/deploy/pod.env"

export VLLM_BASE_URL="${VLLM_BASE_URL:-https://${POD_ID}-8000.proxy.runpod.net/v1}"
export VLLM_API_KEY="${VLLM_API_KEY:-sk-${POD_ID}}"
export VLLM_MODEL="${VLLM_MODEL:-$SERVED_MODEL}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

ready() {
  curl -fsS -m 15 \
    -H "Authorization: Bearer ${VLLM_API_KEY}" \
    -H "User-Agent: ${UA}" \
    -H "Accept: application/json" \
    "${VLLM_BASE_URL}/models" >/dev/null
}

if ready; then
  echo "already serving ${VLLM_BASE_URL}"
else
  if [[ -z "${RUNPOD_API_KEY:-}" ]]; then
    echo "endpoint down and RUNPOD_API_KEY unset — start pod ${POD_ID} in the RunPod UI" >&2
    echo "image: ${IMAGE}" >&2
    echo "docker command: $(cat "$ROOT/deploy/docker-command.txt")" >&2
    exit 2
  fi
  echo "resuming pod ${POD_ID}"
  curl -fsS -m 30 \
    -H "content-type: application/json" \
    --url "https://api.runpod.io/graphql?api_key=${RUNPOD_API_KEY}" \
    --data "{\"query\":\"mutation { podResume(input: { podId: \\\"${POD_ID}\\\", gpuCount: 1 }) { id desiredStatus } }\"}"
  echo
  echo "waiting for vLLM (first boot after download can take several minutes)"
  for _ in $(seq 1 60); do
    if ready; then
      echo "serving ${VLLM_BASE_URL}"
      break
    fi
    sleep 10
  done
  ready || { echo "timed out waiting for ${VLLM_BASE_URL}" >&2; exit 3; }
fi

exec python3 "$ROOT/deploy/smoke_test.py"
