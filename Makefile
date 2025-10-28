.PHONY: help lint format test build-image build-all compose-up compose-down clean

IMAGE_PREFIX ?= $(shell basename `git rev-parse --show-toplevel` 2>/dev/null || echo myrepo)
TAG ?= latest

help:
	@echo "Targets:"
	@echo "  make lint          # run black/flake8/isort checks"
	@echo "  make format        # run black/isort to format code"
	@echo "  make test          # run pytest"
	@echo "  make build-image NAME=<finnhub|spark>  # build docker image locally"
	@echo "  make build-all     # build both images"
	@echo "  make compose-up    # start local stack (docker-compose)"
	@echo "  make compose-down  # stop local stack"

lint:
	flake8 . --max-line-length=120 || true
	isort --check-only --recursive . || true
	black --check .

format:
	isort .
	black .

test:
	pytest -q

build-image:
ifdef NAME
ifeq ($(NAME),finnhub)
	docker build -t $(IMAGE_PREFIX)-finnhub:$(TAG) -f finnhub_producer/Dockerfile finnhub_producer
else ifeq ($(NAME),spark)
	docker build -t $(IMAGE_PREFIX)-spark:$(TAG) -f spark_processor/Dockerfile spark_processor
else
	@echo "Unknown NAME. Use NAME=finnhub or NAME=spark"
	exit 1
endif
else
	@echo "Please provide NAME=finnhub or NAME=spark"
	exit 1
endif

build-all:
	docker build -t $(IMAGE_PREFIX)-finnhub:$(TAG) -f finnhub_producer/Dockerfile finnhub_producer
	docker build -t $(IMAGE_PREFIX)-spark:$(TAG) -f spark_processor/Dockerfile spark_processor

compose-up:
	docker-compose up -d --build

compose-down:
	docker-compose down -v

clean:
	rm -rf __pycache__ .pytest_cache
