"""OpenAI SDK against the RunPod vLLM proxy.

  export VLLM_BASE_URL=https://<POD_ID>-8000.proxy.runpod.net/v1
  export VLLM_API_KEY=sk-<POD_ID>
"""

from __future__ import annotations

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.environ["VLLM_BASE_URL"],
    api_key=os.environ["VLLM_API_KEY"],
)

# Keep thinking off so tool/JSON answers land in message.content, not reasoning.
CHAT_KWARGS = {"chat_template_kwargs": {"enable_thinking": False}}


def chat(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=os.environ.get("VLLM_MODEL", "qwen3.8-27b"),
        messages=[{"role": "user", "content": prompt}],
        extra_body=CHAT_KWARGS,
    )
    return resp.choices[0].message.content or ""


if __name__ == "__main__":
    print(chat("Reply with exactly: pong"))
