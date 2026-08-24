"""LiteLLM against the RunPod vLLM proxy.

  export VLLM_BASE_URL=https://<POD_ID>-8000.proxy.runpod.net/v1
  export VLLM_API_KEY=sk-<POD_ID>
"""

from __future__ import annotations

import os

import litellm

if __name__ == "__main__":
    resp = litellm.completion(
        model=f"openai/{os.environ.get('VLLM_MODEL', 'qwen3.8-27b')}",
        api_base=os.environ["VLLM_BASE_URL"],
        api_key=os.environ["VLLM_API_KEY"],
        messages=[{"role": "user", "content": "Reply with exactly: pong"}],
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    print(resp.choices[0].message.content)
