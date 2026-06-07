#!/usr/bin/env python3
"""Run a Qwen-Agent Assistant against the local llama-server model.

Usage:
    python agents/qwen_agent/run.py "your question here"

Environment (sensible defaults for this repo's llama-server):
    QWEN_BASE_URL  OpenAI-compatible base URL (default http://127.0.0.1:8080/v1)
    QWEN_MODEL     model id / server alias    (default qwen3.5-9b-q4_k_m)
    QWEN_API_KEY   placeholder for local use  (default EMPTY)

A tiny, dependency-free `calculator` tool is registered so this is a real
agent demo (function calling), not just a chat passthrough.
"""

import ast
import json
import operator
import os
import sys

try:
    from qwen_agent.agents import Assistant
    from qwen_agent.tools.base import BaseTool, register_tool
except ImportError as exc:  # pragma: no cover - setup guidance
    sys.exit(
        "qwen-agent is not installed in this environment.\n"
        "Set it up with: make setup-qwen-agent\n"
        f"(import error: {exc})"
    )


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


@register_tool("calculator")
class Calculator(BaseTool):
    description = "Evaluate a basic arithmetic expression and return the numeric result."
    parameters = [
        {
            "name": "expression",
            "type": "string",
            "description": 'Arithmetic expression, e.g. "12 * (3 + 4)"',
            "required": True,
        }
    ]

    def call(self, params, **kwargs) -> str:
        args = json.loads(params) if isinstance(params, str) else params
        return str(_safe_eval(ast.parse(args["expression"], mode="eval")))


def main() -> int:
    base_url = os.environ.get("QWEN_BASE_URL") or (
        f"http://{os.environ.get('LLAMA_HOST', '127.0.0.1')}"
        f":{os.environ.get('LLAMA_PORT', '8080')}/v1"
    )
    llm_cfg = {
        "model": os.environ.get("QWEN_MODEL", "qwen3.5-9b-q4_k_m"),
        "model_server": base_url,
        "api_key": os.environ.get("QWEN_API_KEY", "EMPTY"),
        "generate_cfg": {"top_p": 0.8, "temperature": 0.2},
    }

    query = " ".join(sys.argv[1:]).strip() or (
        "What is 19 * 23? Use the calculator tool, then give the result in a sentence."
    )

    bot = Assistant(
        llm=llm_cfg,
        system_message="You are a concise local agent. Use tools when they help.",
        function_list=["calculator"],
    )

    print(f"[model] {llm_cfg['model']} @ {llm_cfg['model_server']}")
    print(f"[user]  {query}\n")

    responses = []
    for responses in bot.run(messages=[{"role": "user", "content": query}]):
        pass

    for msg in responses:
        role = msg.get("role", "?")
        call = msg.get("function_call")
        if call:
            print(f"[tool-call] {call.get('name')}({call.get('arguments')})")
        content = (msg.get("content") or "").strip()
        if content:
            print(f"[{role}] {content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
