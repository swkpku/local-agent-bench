.PHONY: help install list-models server pull-model health prompt doctor setup-agents setup-pi pi setup-qwen-agent qwen-agent

help:
	@echo "Local agent stack test harness"
	@echo
	@echo "Server + model:"
	@echo "  make install            Install llama.cpp with Homebrew"
	@echo "  make list-models        List servable models from config/stack.json"
	@echo "  make server             Start llama-server with the configured GGUF"
	@echo "  make server MODEL=<key> Start with a model from the registry"
	@echo "  make pull-model         Download the GGUF into the cache (no serving)"
	@echo "  make health             Check llama-server health"
	@echo "  make prompt             Send a simple prompt"
	@echo
	@echo "Agents (need a running server):"
	@echo "  make setup-agents       Set up both pi and Qwen-Agent"
	@echo "  make setup-pi           Install pi and register the local model"
	@echo "  make pi                 Run pi on the local model (interactive)"
	@echo "  make pi MODEL=<key>     Run pi against a model from the registry"
	@echo "  make setup-qwen-agent   Create venv and install Qwen-Agent"
	@echo "  make qwen-agent         Run the Qwen-Agent example on the local model"
	@echo
	@echo "  make doctor             Check local prerequisites"

install:
	brew install llama.cpp

list-models:
	@python3 scripts/models.py list

server:
	MODEL="$(MODEL)" ./scripts/start_llama_server.sh

pull-model:
	MODEL="$(MODEL)" ./scripts/pull_model.sh

health:
	python3 scripts/healthcheck.py

prompt:
	python3 scripts/prompt.py "Give me a three-step plan to test whether a local model can behave agentically."

setup-agents: setup-pi setup-qwen-agent

setup-pi:
	./scripts/setup_pi.sh

pi:
	MODEL="$(MODEL)" ./scripts/run_pi.sh

setup-qwen-agent:
	./scripts/setup_qwen_agent.sh

qwen-agent:
	./scripts/run_qwen_agent.sh

doctor:
	./scripts/doctor.sh
