# Local Agent Stack Harness

This repo is a small test bed for local agent stacks. The first working path is:

```text
llama-server -> Qwen3.5 9B Q4_K_M GGUF -> OpenAI-compatible chat -> simple prompting
```

The stack is intentionally layered so you can swap one piece at a time:

| Layer | Default | Other slots |
| --- | --- | --- |
| Runtime | `llama-server` | `ollama`, `lm-studio` |
| Model | `qwen3.5-9b-q4_k_m` | smaller quant, local GGUF path |
| Prompt harness | `scripts/prompt.py` | curl, future tool-calling harness |
| Prompt | `prompts/simple.md` | `prompts/agentic-smoke.md` |

## Quick Start

Install llama.cpp:

```bash
make install
```

Copy the example environment if you want to edit defaults:

```bash
cp .env.example .env
```

Start the server:

```bash
make server
```

The first run will download/cache this exact GGUF from Hugging Face:

```text
https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-Q4_K_M.gguf
```

The harness uses `--model-url` rather than `--hf-repo` for the first text-only path because `llama-server -hf` may auto-download the model's vision projector when one is present.

In a second terminal, check health and send a prompt:

```bash
make health
make prompt
```

Or send your own prompt:

```bash
python3 scripts/prompt.py "What are three signs that a model is actually using a plan?"
```

## Raw API Check

```bash
curl http://127.0.0.1:8080/v1/models
```

```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5-9b-q4_k_m",
    "messages": [
      {"role": "system", "content": "You are concise."},
      {"role": "user", "content": "Give me a one sentence readiness test."}
    ],
    "temperature": 0.2,
    "max_tokens": 128
  }'
```

## Switching Models

The default uses an exact model URL:

```bash
LLAMA_MODEL_URL=https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-Q4_K_M.gguf make server
```

For a smaller comparison quant:

```bash
LLAMA_MODEL_ALIAS=qwen3.5-9b-iq4_xs \
LLAMA_MODEL_URL=https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-IQ4_XS.gguf \
make server
```

To use llama.cpp's Hugging Face repo shorthand instead:

```bash
LLAMA_MODEL_SOURCE=hf \
LLAMA_HF_REPO=bartowski/Qwen_Qwen3.5-9B-GGUF:Q4_K_M \
make server
```

For a local GGUF:

```bash
LLAMA_MODEL_SOURCE=path \
LLAMA_MODEL_PATH=/absolute/path/to/model.gguf \
LLAMA_MODEL_ALIAS=local-gguf \
make server
```

Then call the same alias:

```bash
python3 scripts/prompt.py --model local-gguf "Say hello."
```

## Tuning For This Mac

The defaults are conservative for a 16 GB Apple Silicon machine:

```text
LLAMA_CTX_SIZE=8192
LLAMA_N_GPU_LAYERS=auto
LLAMA_THREADS=8
LLAMA_PARALLEL=1
LLAMA_NO_MMPROJ=1
LLAMA_REASONING=off
MAX_TOKENS=512
THINKING=off
```

Reasoning is disabled at the server by default because many external agent harnesses expect assistant text in `message.content` and do not read `message.reasoning_content`. To inspect reasoning behavior, restart the server with reasoning enabled:

```bash
LLAMA_REASONING=on make server
python3 scripts/prompt.py --thinking on --max-tokens 1024 --raw "Plan a two-step tool-use test."
```

Increase context only after the baseline is stable. For agent tests, short context and reliable tool use are more useful than a huge context window.

## Next Test Layers

Start with simple prompting, then add these in order:

1. Structured JSON output.
2. A tiny local tool set: `list_dir`, `read_file`, `write_file`, `run_command`.
3. A loop that records action, observation, and final answer.
4. A second runtime comparison with Ollama or LM Studio using the same prompts.

The current config lives in `config/stack.json`.
