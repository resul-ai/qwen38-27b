# RunPod Edit Pod — current paste values

*Last updated: 2026-08-25*

Image ENTRYPOINT is `vllm serve`. **Docker Command is only the args.** Pasting `vllm serve ...` double-starts.

## Fields

| Field | Value |
|---|---|
| Pod name | `qwen38-27b` |
| Image | `vllm/vllm-openai:v0.27.1` |
| Expose HTTP | `8000` → `https://{POD_ID}-8000.proxy.runpod.net/v1` |
| GPU | 1× RTX 6000 Ada 48GB On-Demand. Fallback: L40S 48GB |
| Jupyter | off |
| SSH | on |
| Volume | `/workspace` (this pod: 80GB volume disk) |
| Env | `HF_HOME=/workspace/.huggingface` |
| Env | `VLLM_CACHE_ROOT=/workspace/vllm_cache` |
| Env | `VLLM_API_KEY=sk-$RUNPOD_POD_ID` (or explicit `sk-<pod-id>`) |

## Docker Command (one line)

Source file in repo: `deploy/docker-command.txt`

```
Qwen/Qwen3.8-27B-FP8 --host 0.0.0.0 --port 8000 --served-model-name qwen3.8-27b --api-key sk-$RUNPOD_POD_ID --language-model-only --tensor-parallel-size 1 --max-model-len 262144 --gpu-memory-utilization 0.90 --max-num-seqs 8 --max-num-batched-tokens 8192 --kv-cache-dtype fp8 --enable-prefix-caching --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 --default-chat-template-kwargs '{"enable_thinking": false}' --structured-outputs-config.backend xgrammar --structured-outputs-config.enable_in_reasoning true
```

If the Edit textbox eats single quotes around the JSON kwargs, set thinking off per request (`references/clients.md`) and try the kwargs without nested quotes as in `deploy/docker-command.txt`.

`deploy/runpod-start.sh` is the same flags with `exec vllm serve` for a shell/SSH start. Do not use it as the Docker Command while the image entrypoint is already `vllm serve`.

## Resume a stopped pod (API)

```bash
curl --request POST \
  --header 'content-type: application/json' \
  --url "https://api.runpod.io/graphql?api_key=${RUNPOD_API_KEY}" \
  --data '{"query":"mutation { podResume(input: { podId: \"x8vxt1ym241m5r\", gpuCount: 1 }) { id desiredStatus } }"}'
```

Prefer `./deploy/serve.sh` which wraps this and waits for `/v1/models`.

Logs tab: **Container**, not System. Ready line: `Application startup complete.`

## SSH (inspection only)

```
ssh x8vxt1ym241m5r-64410bfe@ssh.runpod.io -i ~/.ssh/id_rsa
```

Gateway ignores a remote command string. Do not rely on SSH to start vLLM.
