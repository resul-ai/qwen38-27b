# qwen38-27b

Persistent OpenAI-compatible **vLLM** endpoint for **Qwen3.8-27B-FP8** on a RunPod GPU Pod (RTX 6000 Ada 48GB). Built for LangChain / LiteLLM agents: tool calling, streaming, JSON, 256k-capped paged KV.

Repo: [github.com/resul-ai/qwen38-27b](https://github.com/resul-ai/qwen38-27b)

## Live endpoint

| | |
|---|---|
| Base URL | `https://x8vxt1ym241m5r-8000.proxy.runpod.net/v1` |
| Model | `qwen3.8-27b` |
| Image | `vllm/vllm-openai:v0.27.1` |
| Checkpoint | `Qwen/Qwen3.8-27B-FP8` |
| Context cap | 262144 |

Copy `.env.example` to `.env`. Do not commit `.env`. API key convention is `sk-<pod-id>`.

## Serve (agent)

Claude/Cursor skill: `.claude/skills/serve-qwen38-27b`. Trigger: **serve qwen38 27B**.

```bash
./deploy/serve.sh
```

That probes the proxy, resumes the pod if `RUNPOD_API_KEY` is set, then runs `deploy/smoke_test.py` (chat, **tool_calls**, JSON, stream, two concurrent).

## Clients

Until thinking-off is the container default, every request needs:

```python
extra_body={"chat_template_kwargs": {"enable_thinking": False}}
```

Otherwise JSON can land in `message.reasoning`. See `examples/`.

## Docker Command

Image ENTRYPOINT is already `vllm serve`. Paste **args only** from `deploy/docker-command.txt`. Full flags + why: `.claude/skills/serve-qwen38-27b/references/pod-config.md`. Tool parser must be `qwen3_coder` (`hermes` returns empty `tool_calls`).
