---
name: serve-qwen38-27b
description: Serve Qwen3.8-27B (Qwen3.8-27B-FP8) as a persistent OpenAI-compatible vLLM endpoint on a RunPod GPU Pod. Use whenever the user says serve qwen38 27B, qwen3.8-27b, qwen38, start vLLM, RunPod Qwen, ayağa kaldır, endpoint'i aç, or wants the LangChain/LiteLLM base URL for this model. Do not use for DCS DeepLens 27B, JSL medical-llm-reasoning-27b, or Azure Foundry deploys.
---

# Serve Qwen3.8-27B on RunPod vLLM

Read `references/current-status.md` first. Then run the workflow below. Do not improvise a different GPU, image, parser, or template.

Repo (source of truth): `/Users/res/Projects/llm-deployment/qwen38-27b`  
GitHub: `https://github.com/resul-ai/qwen38-27b`

## Workflow — "serve qwen38 27B"

Copy this checklist and execute in order:

```
- [ ] 1. Probe GET /v1/models (browser User-Agent)
- [ ] 2. If down, resume existing pod — do not create a second pod
- [ ] 3. Wait until Application startup complete / /v1/models returns qwen3.8-27b
- [ ] 4. Run deploy/smoke_test.py (must include tool_calls)
- [ ] 5. Report base URL, model name, and any flag drift
```

From the repo:

```bash
cd /Users/res/Projects/llm-deployment/qwen38-27b
./deploy/serve.sh
```

`serve.sh` uses `deploy/pod.env`. API key defaults to `sk-$POD_ID`. Override with `VLLM_API_KEY`. To resume a stopped pod, `RUNPOD_API_KEY` must be in the environment (never commit it).

If the probe is already 200, skip resume. Still run the smoke test.

## Locked serving shape

Exact paste values: `references/pod-config.md`. Canonical start command: `deploy/docker-command.txt` and `deploy/runpod-start.sh`.

| Knob | Locked value | Why |
|---|---|---|
| Product | GPU **Pod**, not Serverless | Start command persists; stop/start re-runs `vllm serve` |
| GPU | RTX 6000 Ada **48GB** (~$0.84/hr). Fallback L40S 48GB | FP8 weights ~28GB. A4500 20GB / 4090 24GB cannot load it |
| Image | `vllm/vllm-openai:v0.27.1` | Qwen3.8 needs vLLM ≥0.17. Hub "vLLM Latest" `:latest` is unpinned |
| Checkpoint | `Qwen/Qwen3.8-27B-FP8` | NVFP4 is Blackwell-only |
| Docker command | **args after** image ENTRYPOINT `vllm serve` | Prefixing `vllm serve` double-serves |
| Tool parser | `--tool-call-parser qwen3_coder` | `hermes` returns empty `tool_calls` |
| Reasoning | `--reasoning-parser qwen3` | Chat template opens `<think>` |
| Thinking default | `--default-chat-template-kwargs '{"enable_thinking": false}'` | Without this, JSON/`content` lands in `message.reasoning` |
| Context cap | `--max-model-len 262144` | App cap 256k; paged KV, not a restart-per-request resize |

Hub template **vLLM Latest** still defaults to `Qwen/Qwen3-8B` + `--enforce-eager --max-model-len 8128`. Killing the vLLM PID restarts the **container** (docker-init is PID 1) and boots 8B again. Fix is Edit Pod image + docker command, not a wrapper script on the overlay.

## Probe details

RunPod HTTPS proxy returns Cloudflare **1010** to Python-urllib's default UA. Always send a Chrome UA (see `deploy/smoke_test.py`). curl is fine.

Success: `GET /v1/models` → `id: qwen3.8-27b`, `root: Qwen/Qwen3.8-27B-FP8`.  
Unauthenticated: 401. Key is `sk-$POD_ID` unless rotated.

Clients must pass `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` until the default-kwargs flag is actually on the running container. Snippets: `references/clients.md` and `examples/`.

## After serve

Report:

- `VLLM_BASE_URL=https://<POD_ID>-8000.proxy.runpod.net/v1`
- `VLLM_MODEL=qwen3.8-27b`
- Smoke: models / chat / **tool_calls** / json_object / stream / 2-concurrent
- Whether thinking-off is default on the container or still per-request

Do not print Jupyter passwords, `PUBLIC_KEY`, or account `RUNPOD_API_KEY` from container env.

## Persist

UI **Save as template** → `qwen38-27b-vllm` (see `deploy/pod.env` `TEMPLATE_NAME`). Volume disk at `/workspace` keeps `HF_HOME=/workspace/.huggingface`. Stop pod to stop GPU billing; volume billing continues.

## If flags or the checkpoint change

Update `deploy/docker-command.txt`, `deploy/runpod-start.sh`, `deploy/pod.env`, then `references/pod-config.md` and the snapshot in `references/current-status.md`. Bump the date. Never leave SKILL.md claiming a parser or image that is not what the pod runs.

## Do not

- Use Ampere A40/A6000 for this official FP8 (no native FP8) unless Ada/L40S is sold out — label unverified
- Use `--tool-call-parser hermes`
- Switch to Serverless
- `git push --force` this repo
- Commit `.env` or live API keys
