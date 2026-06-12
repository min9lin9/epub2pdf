# syntax=docker/dockerfile:1

FROM python:3.10-slim

# Install WeasyPrint system dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libpangoft2-1.0-0 \
        shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e '.[weasyprint]'

# Run as non-root user.
RUN useradd -m epub2pdf
USER epub2pdf

WORKDIR /workspace

ENTRYPOINT ["epub2pdf"]
CMD ["--help"]
