"""LangChain ChatOpenAI against the RunPod vLLM proxy.

  export VLLM_BASE_URL=https://<POD_ID>-8000.proxy.runpod.net/v1
  export VLLM_API_KEY=sk-<POD_ID>
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url=os.environ["VLLM_BASE_URL"],
    api_key=os.environ["VLLM_API_KEY"],
    model=os.environ.get("VLLM_MODEL", "qwen3.8-27b"),
    streaming=True,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

if __name__ == "__main__":
    print(llm.invoke("Reply with exactly: pong").content)
