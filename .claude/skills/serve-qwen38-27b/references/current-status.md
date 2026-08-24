# Current status

*Last updated: 2026-08-25*

| Field | Value |
|---|---|
| Pod name / ID | `qwen38-27b` / `x8vxt1ym241m5r` |
| GPU | RTX 6000 Ada 48GB, Secure Cloud |
| Image | `vllm/vllm-openai:v0.27.1` |
| Checkpoint | `Qwen/Qwen3.8-27B-FP8` (~29GB under `/workspace/.huggingface`) |
| Served name | `qwen3.8-27b` |
| Public API | `https://x8vxt1ym241m5r-8000.proxy.runpod.net/v1` |
| API key convention | `sk-$RUNPOD_POD_ID` → `sk-x8vxt1ym241m5r` |
| `max_model_len` | 262144 |
| Storage | Volume disk 80GB at `/workspace` (no network volume on this pod) |
| Template saved | **Not yet** — operator still needs UI Save as template `qwen38-27b-vllm` |
| Thinking-off as container default | **Not yet** — Edit Pod omitted quoted `--default-chat-template-kwargs`; clients must send `chat_template_kwargs.enable_thinking=false` |
| Stop/start cache reuse | Unverified (weights already on volume; do not stop the pod just to test) |

## Smoke evidence (2026-08-25)

`python deploy/smoke_test.py` → **PASS**

- models: `qwen3.8-27b`
- chat: `pong`
- tool_calls: `get_weather` `{"city": "Paris"}`, `finish_reason=tool_calls`
- json_object: `{"name":"Alice","age":30}` in `content` (only with thinking off)
- stream: `1, 2, 3`
- concurrent: two in-flight completions both `stop`

Without thinking-off, `response_format=json_object` put JSON in `message.reasoning` and `content=null`.

## Known traps

- Hub vLLM Latest CMD is still `Qwen/Qwen3-8B`. Overlay wrappers die on restart.
- SSH to `ssh.runpod.io` ignores remote command args and opens an interactive root shell at `/vllm-workspace`. Cursor SSH has no PTY; use `ssh -tt` / `pty.fork()` if you must inspect the box. Prefer the HTTPS API.
- Python urllib without a browser UA → Cloudflare 1010.
- Do not kill the vLLM process to "restart flags" — the container comes back on the Hub 8B command.
