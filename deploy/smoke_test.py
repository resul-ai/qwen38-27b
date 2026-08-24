#!/usr/bin/env python3
"""Smoke tests against a live vLLM OpenAI-compatible endpoint.

RunPod's HTTPS proxy returns Cloudflare 1010 if the User-Agent looks like
Python-urllib. Always send a browser UA.

Usage:
  export VLLM_BASE_URL=https://<POD_ID>-8000.proxy.runpod.net/v1
  export VLLM_API_KEY=sk-<POD_ID>
  python deploy/smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT_S = 90


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"missing env {name}")
    return value


def request(base_url: str, api_key: str, path: str, body: dict | None = None) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="GET" if body is None else "POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        raise SystemExit(f"HTTP {exc.code} {path}: {payload[:500]}") from exc


def _stream_chat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int = 32,
) -> list[str]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0,
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": UA,
            "Accept": "text/event-stream",
        },
    )
    chunks: list[str] = []
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        for raw in resp:
            line = raw.decode(errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            delta = json.loads(payload)["choices"][0].get("delta") or {}
            piece = delta.get("content")
            if piece:
                chunks.append(piece)
    return chunks


def chat(base_url: str, api_key: str, model: str, **extra) -> dict:
    payload = {
        "model": model,
        "messages": extra.pop("messages"),
        "max_tokens": extra.pop("max_tokens", 64),
        "temperature": extra.pop("temperature", 0),
        "chat_template_kwargs": extra.pop(
            "chat_template_kwargs", {"enable_thinking": False}
        ),
    }
    payload.update(extra)
    return request(base_url, api_key, "/chat/completions", payload)


def main() -> int:
    base_url = _env("VLLM_BASE_URL")
    api_key = _env("VLLM_API_KEY")
    model = os.environ.get("VLLM_MODEL", "qwen3.8-27b")
    failures: list[str] = []

    models = request(base_url, api_key, "/models")
    ids = [item["id"] for item in models.get("data", [])]
    print("models:", ids)
    if model not in ids:
        failures.append(f"served model {model!r} not in {ids}")

    ping = chat(
        base_url,
        api_key,
        model,
        messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        max_tokens=16,
    )
    ping_content = (ping["choices"][0]["message"].get("content") or "").strip()
    print("chat:", repr(ping_content))
    if "pong" not in ping_content.lower():
        failures.append(f"chat content missing pong: {ping_content!r}")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    tool_resp = chat(
        base_url,
        api_key,
        model,
        messages=[{"role": "user", "content": "What is the weather in Paris?"}],
        tools=tools,
        tool_choice="auto",
        max_tokens=128,
    )
    message = tool_resp["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    print("tool_calls:", json.dumps(calls, indent=2)[:800])
    if not calls or calls[0].get("function", {}).get("name") != "get_weather":
        failures.append(f"expected get_weather tool call, got {calls!r}")

    json_resp = chat(
        base_url,
        api_key,
        model,
        messages=[
            {
                "role": "user",
                "content": "Return JSON with keys name and age for Alice, 30.",
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=64,
    )
    json_content = json_resp["choices"][0]["message"].get("content") or ""
    print("json:", json_content)
    try:
        parsed = json.loads(json_content)
        if parsed.get("name") != "Alice":
            failures.append(f"json missing Alice: {parsed}")
    except json.JSONDecodeError:
        failures.append(
            f"json_object landed outside content: {json_resp['choices'][0]['message']}"
        )

    stream_chunks = _stream_chat(
        base_url,
        api_key,
        model,
        messages=[{"role": "user", "content": "Count 1 2 3"}],
        max_tokens=32,
    )
    stream_text = "".join(stream_chunks)
    print("stream:", repr(stream_text[:80]))
    if not stream_chunks:
        failures.append("stream produced no content deltas")

    def one(i: int) -> tuple[int, str]:
        resp = chat(
            base_url,
            api_key,
            model,
            messages=[{"role": "user", "content": f"Say only {i}"}],
            max_tokens=8,
        )
        return i, (resp["choices"][0]["message"].get("content") or "").strip()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(one, i) for i in (1, 2)]
        results = [fut.result() for fut in as_completed(futs)]
    print("concurrent:", results)
    got = {content for _, content in results}
    if not {"1", "2"} <= got and not all(str(i) in content for i, content in results):
        failures.append(f"concurrent mismatch: {results}")

    if failures:
        print("FAIL")
        for item in failures:
            print("-", item)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
