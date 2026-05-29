version =
IMAGE_NAME ?= gitporter

install:
	pip install -e .

docker-build:
	docker build -t $(IMAGE_NAME):latest -f deploy/docker/Dockerfile .

docker-run:
	docker run --rm \
		-v $(CURDIR)/config.yml:/app/config.yml:ro \
		-v $(CURDIR)/.gitporter:/app/.gitporter \
		$(IMAGE_NAME):latest

docker-up:
	docker compose -f deploy/docker/docker-compose.yml up --build --remove-orphans

publish:
	@if [ -z "$(version)" ]; then \
		echo "Please set version, e.g., make publish version=0.1.0"; \
		exit 1; \
	fi

	rm -rf dist
	uv version $(version)
	uv build
	uv publish
