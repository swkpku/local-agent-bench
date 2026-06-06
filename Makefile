.PHONY: help install server health prompt doctor

help:
	@echo "Local agent stack test harness"
	@echo
	@echo "Targets:"
	@echo "  make install   Install llama.cpp with Homebrew"
	@echo "  make server    Start llama-server with the configured GGUF"
	@echo "  make health    Check llama-server health"
	@echo "  make prompt    Send a simple prompt"
	@echo "  make doctor    Check local prerequisites"

install:
	brew install llama.cpp

server:
	./scripts/start_llama_server.sh

health:
	python3 scripts/healthcheck.py

prompt:
	python3 scripts/prompt.py "Give me a three-step plan to test whether a local model can behave agentically."

doctor:
	./scripts/doctor.sh

