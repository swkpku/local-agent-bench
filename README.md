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

## Run Agents on the Local Model

Once the server is up (`make server`), point an agent framework at the local
OpenAI-compatible endpoint. Two are wired in — see [`agents/README.md`](agents/README.md).

### pi (CLI coding agent)

```bash
make setup-pi                    # install pi + register the local models
make pi                          # interactive TUI on qwen3.5-9b-q4_k_m
make pi MODEL=gemma-4-12b-qat    # same picker as the server
```

```bash
# one-shot, non-interactive:
scripts/run_pi.sh -p "Summarize this repo in 3 bullets."
```

`setup-pi` merges a `localai` provider into `~/.pi/agent/models.json` (existing
providers are preserved, with a timestamped backup); it registers every model in
the provider template (`agents/pi/models.json`). `make pi MODEL=<key>` selects one
by its `config/stack.json` key — **point it at the same model `make server` is
currently serving**, since pi only talks to whatever the server has loaded. If you
set up pi before a model was added, re-run `make setup-pi` to register it.

### Qwen-Agent (Python framework)

```bash
make setup-qwen-agent                          # create .venv, install qwen-agent
make qwen-agent                                # demo query (with a calculator tool)
scripts/run_qwen_agent.sh "What is 19*23?"     # custom query
```

Both use the same model alias (`qwen3.5-9b-q4_k_m`) and endpoint
(`http://127.0.0.1:8080/v1`); override via `.env` (see `.env.example`).

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

### Pick from the registry (easiest)

Models live in `config/stack.json`. List them:

```bash
make list-models
```

```text
  KEY                QUANT       SRC   STATUS       NOTE
* qwen3.5-9b-q4_k_m  Q4_K_M      url   default      Default 16 GB Mac baseline…
  gemma-4-12b-qat    UD-Q4_K_XL  url   alternative  Gemma 4 QAT (near-bf16)…
  gemma-4-e4b-qat    UD-Q4_K_XL  url   alternative  Lighter Gemma 4 QAT…
```

Then choose one by key — it resolves the URL and the model's recommended sampling
for you:

```bash
make server MODEL=gemma-4-12b-qat      # serve Gemma 4 12B QAT
make pull-model MODEL=gemma-4-12b-qat  # just download it first
```

`MODEL=` overrides any model pinned in `.env`. To query it, point the client at
the same alias: `python3 scripts/prompt.py --model gemma-4-12b-qat "…"`.

### Set vars manually

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

**About the Gemma 4 QAT entries:** `gemma-4-12b-qat` and `gemma-4-e4b-qat` are
quantization-aware-trained (near-bf16 quality; native system role + function
calling) and use Unsloth's Dynamic 2.0 `UD-Q4_K_XL`, which is both higher-accuracy
*and* smaller than Google's plain Q4_0 (Unsloth found Q4_0 degrades quality despite
being larger). The dense **12B** (~6.7 GB, 256K ctx) is the best Gemma fit for a
16 GB Mac; **E4B** (~4.2 GB, effective 4.5B) trades quality for snappier turns and
more KV headroom. Both carry Gemma's documented sampling (temp 1.0 / top_p 0.95 /
top_k 64) and a **64K default context** in the registry — the picker applies these
automatically (Gemma 4's sliding-window attention keeps 64K KV at ~2.4 GB, which
fits a 16 GB Mac under the default Metal wired-memory limit). Lower the temp for
more deterministic tool calls. Override context per run, e.g.
`LLAMA_CTX_SIZE=32768 make server MODEL=gemma-4-12b-qat`; 128K needs raising
`iogpu.wired_limit_mb` and re-prefills slowly each turn (no prefix caching).
Google's official plain-Q4_0 GGUFs (`google/gemma-4-12B-it-qat-q4_0-gguf`, `…E4B…`)
are a fallback. The 26B-A4B (~14 GB) and 31B (~18 GB) QAT variants exist but exceed
the usable budget on a 16 GB machine.

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

The defaults are an **agentic profile** for a 16 GB Apple Silicon machine — a 128K
context with q8_0 KV cache + flash attention to hold memory down, performance-core
threads, and low-temperature sampling for reliable tool calls:

```text
LLAMA_CTX_SIZE=131072
LLAMA_N_GPU_LAYERS=auto
LLAMA_THREADS=4
LLAMA_PARALLEL=1
LLAMA_FLASH_ATTN=on
LLAMA_CACHE_TYPE_K=q8_0
LLAMA_CACHE_TYPE_V=q8_0
LLAMA_UBATCH=1024
LLAMA_TEMP=0.2
LLAMA_TOP_P=0.8
LLAMA_TOP_K=20
LLAMA_REASONING=off
```

Reasoning is disabled at the server by default because many external agent harnesses expect assistant text in `message.content` and do not read `message.reasoning_content`. To inspect reasoning behavior, restart the server with reasoning enabled:

```bash
LLAMA_REASONING=on make server
python3 scripts/prompt.py --thinking on --max-tokens 1024 --raw "Plan a two-step tool-use test."
```

The default is a **128K** window (`131072`, ~8 GB RAM on a 16 GB box thanks to this hybrid model's cheap KV). It still can't reuse a cached prefix, so a full context re-prefills *every turn* and takes minutes — treat 128K as headroom, not an everyday setting. For snappy interactive turns, set `LLAMA_CTX_SIZE` to `16384`–`32768`.

## Next Test Layers

Start with simple prompting, then add these in order:

1. Structured JSON output.
2. A tiny local tool set: `list_dir`, `read_file`, `write_file`, `run_command`.
3. A loop that records action, observation, and final answer.
4. A second runtime comparison with Ollama or LM Studio using the same prompts.

The current config lives in `config/stack.json`.
