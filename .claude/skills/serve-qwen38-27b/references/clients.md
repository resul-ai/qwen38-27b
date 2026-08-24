# Client snippets

*Last updated: 2026-08-25*

Env:

```bash
export VLLM_BASE_URL=https://x8vxt1ym241m5r-8000.proxy.runpod.net/v1
export VLLM_API_KEY=sk-$POD_ID   # see deploy/pod.env
export VLLM_MODEL=qwen3.8-27b
```

Always send thinking off until the container default is confirmed:

```python
extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
```

## OpenAI SDK

See `examples/openai_client.py`.

```python
from openai import OpenAI
client = OpenAI(base_url=os.environ["VLLM_BASE_URL"], api_key=os.environ["VLLM_API_KEY"])
client.chat.completions.create(
    model="qwen3.8-27b",
    messages=[{"role": "user", "content": "..."}],
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

## LangChain

See `examples/langchain_client.py`.

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    base_url=os.environ["VLLM_BASE_URL"],
    api_key=os.environ["VLLM_API_KEY"],
    model="qwen3.8-27b",
    streaming=True,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

## LiteLLM

See `examples/litellm_client.py`. Model id `openai/qwen3.8-27b`, `api_base` the same `/v1` URL.
