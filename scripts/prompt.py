#!/usr/bin/env python3
"""Minimal OpenAI-compatible chat client for local runtimes."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config() -> dict:
    config_path = ROOT / os.environ.get("LOCALAI_CONFIG", "config/stack.json")
    with config_path.open() as fh:
        return json.load(fh)


def read_text(path: str) -> str:
    target = Path(path)
    if not target.is_absolute():
        target = ROOT / target
    return target.read_text().strip()


def post_json(url: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}:\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Could not reach {url}. Start the server with: make server\n{exc}"
        ) from exc


def main() -> int:
    load_env_file(ROOT / ".env")
    config = load_config()
    active = config["active"]
    runtime = config["runtimes"][active["runtime"]]
    model = config["models"][active["model"]]
    prompt_config = config["prompts"][active["prompt"]]

    parser = argparse.ArgumentParser(description="Send a prompt to a local model.")
    parser.add_argument("prompt", nargs="*", help="Prompt text. Reads default prompt if omitted.")
    parser.add_argument("--system", help="Override the configured system prompt.")
    parser.add_argument("--prompt-file", help="Read user prompt from a file.")
    parser.add_argument("--base-url", default=os.environ.get("LLAMA_BASE_URL", runtime["base_url"]))
    parser.add_argument("--model", default=os.environ.get("LLAMA_MODEL_ALIAS", model["api_model"]))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("TEMPERATURE", model["temperature"])))
    parser.add_argument("--top-p", type=float, default=float(os.environ.get("TOP_P", model["top_p"])))
    parser.add_argument("--max-tokens", type=int, default=int(os.environ.get("MAX_TOKENS", model["max_tokens"])))
    parser.add_argument(
        "--thinking",
        choices=("off", "on", "auto"),
        default=os.environ.get("THINKING", model.get("thinking", "off")),
        help="Qwen-style reasoning mode. Default is off for simple prompting.",
    )
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--raw", action="store_true", help="Print raw JSON response.")
    args = parser.parse_args()

    if args.prompt_file:
        user_prompt = read_text(args.prompt_file)
    elif args.prompt:
        user_prompt = " ".join(args.prompt)
    else:
        user_prompt = read_text(os.environ.get("LOCALAI_PROMPT", prompt_config["path"]))

    system_prompt = args.system or prompt_config["system"]
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "stream": False,
    }
    if args.thinking != "auto":
        payload["chat_template_kwargs"] = {"enable_thinking": args.thinking == "on"}

    url = args.base_url.rstrip("/") + "/chat/completions"
    data = post_json(url, payload, args.timeout)
    if args.raw:
        print(json.dumps(data, indent=2))
        return 0

    try:
        message = data["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        if not content and message.get("reasoning_content"):
            raise SystemExit(
                "Model returned only reasoning_content. Retry with the default --thinking off "
                "or raise --max-tokens if you intentionally enabled thinking."
            )
        print(content)
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(json.dumps(data, indent=2)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
