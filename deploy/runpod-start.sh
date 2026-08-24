#!/usr/bin/env bash
# RunPod Docker Command for image vllm/vllm-openai:v0.27.1
# The image ENTRYPOINT is already `vllm serve`. Paste only the args below
# into Edit Pod → Docker Command (no `vllm serve` prefix).
#
# Required env on the pod:
#   HF_HOME=/workspace/.huggingface
#   VLLM_API_KEY=sk-<pod-id>
# Optional:
#   VLLM_CACHE_ROOT=/workspace/vllm_cache
#   HUGGING_FACE_HUB_TOKEN=...
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen3.8-27B-FP8}"
SERVED_NAME="${SERVED_NAME:-qwen3.8-27b}"
API_KEY="${VLLM_API_KEY:?set VLLM_API_KEY}"

exec vllm serve "$MODEL" \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name "$SERVED_NAME" \
  --api-key "$API_KEY" \
  --language-model-only \
  --tensor-parallel-size 1 \
  --max-model-len 262144 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 8 \
  --max-num-batched-tokens 8192 \
  --kv-cache-dtype fp8 \
  --enable-prefix-caching \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --default-chat-template-kwargs '{"enable_thinking": false}' \
  --structured-outputs-config.backend xgrammar \
  --structured-outputs-config.enable_in_reasoning true
