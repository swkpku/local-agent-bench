#!/usr/bin/env python3
"""List and resolve servable models from config/stack.json.

Used by the Makefile / start scripts so you can pick a model by its registry
key instead of pasting GGUF URLs:

    python3 scripts/models.py list
    python3 scripts/models.py resolve gemma-4-12b-qat   # emits shell exports

`resolve` prints model-identity assignments (alias/source/url/repo/path) that the
caller should `eval` to OVERRIDE any prior value, plus sampling defaults written
with `:=` so an explicit env/.env value still wins.
"""

import json
import os
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_config() -> dict:
    config_path = ROOT / os.environ.get("LOCALAI_CONFIG", "config/stack.json")
    with config_path.open() as fh:
        return json.load(fh)


def servable(models: dict) -> dict:
    return {k: m for k, m in models.items() if m.get("runtime") == "llama-server"}


def shorten(text: str, width: int = 58) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def cmd_list(config: dict) -> int:
    models = servable(config["models"])
    active = config.get("active", {}).get("model")
    if not models:
        print("No llama-server models in config.", file=sys.stderr)
        return 1

    key_w = max(len(k) for k in models)
    quant_w = max(len(str(m.get("quant", "-"))) for m in models.values())

    print("Servable models (config/stack.json) — pick with: make server MODEL=<key>\n")
    header = f"  {'KEY'.ljust(key_w)}  {'QUANT'.ljust(quant_w)}  SRC   STATUS       NOTE"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for key, m in models.items():
        mark = "*" if key == active else " "
        quant = str(m.get("quant", "-")).ljust(quant_w)
        src = str(m.get("source", "-")).ljust(4)
        status = str(m.get("status", "default")).ljust(11)
        note = shorten(m.get("notes", ""))
        print(f"{mark} {key.ljust(key_w)}  {quant}  {src}  {status}  {note}")
    print("\n  * = active default in config/stack.json")
    return 0


def cmd_resolve(config: dict, key: str) -> int:
    models = config["models"]
    avail = servable(models)
    if key not in avail:
        print(
            f"Unknown model '{key}'. Servable keys: {', '.join(avail)}",
            file=sys.stderr,
        )
        return 2

    m = models[key]
    q = shlex.quote
    lines = [
        f"LLAMA_MODEL_ALIAS={q(m.get('api_model', key))}",
        f"LLAMA_MODEL_SOURCE={q(m.get('source', 'url'))}",
    ]
    source = m.get("source", "url")
    if source == "url":
        lines.append(f"LLAMA_MODEL_URL={q(m['model_url'])}")
    elif source == "hf":
        lines.append(f"LLAMA_HF_REPO={q(m['hf_repo'])}")
    elif source == "path":
        lines.append(f"LLAMA_MODEL_PATH={q(m.get('model_path', ''))}")

    # Context + sampling defaults: registry value unless env/.env already set one.
    for var, field in (
        ("LLAMA_CTX_SIZE", "ctx_size"),
        ("LLAMA_TEMP", "temperature"),
        ("LLAMA_TOP_P", "top_p"),
        ("LLAMA_TOP_K", "top_k"),
    ):
        if field in m:
            lines.append(f': "${{{var}:={m[field]}}}"')

    exports = (
        "LLAMA_MODEL_ALIAS LLAMA_MODEL_SOURCE LLAMA_MODEL_URL LLAMA_HF_REPO "
        "LLAMA_MODEL_PATH LLAMA_CTX_SIZE LLAMA_TEMP LLAMA_TOP_P LLAMA_TOP_K"
    )
    lines.append(f"export {exports}")
    print("\n".join(lines))
    return 0


def main() -> int:
    config = load_config()
    args = sys.argv[1:]
    if not args or args[0] in ("list", "ls"):
        return cmd_list(config)
    if args[0] in ("resolve", "get") and len(args) == 2:
        return cmd_resolve(config, args[1])
    print(
        "Usage: models.py list | models.py resolve <key>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
