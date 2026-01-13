# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

COPY pyproject.toml requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# 이미지 메타데이터 (OCI 표준)
LABEL org.opencontainers.image.title="Zendesk MCP Server"
LABEL org.opencontainers.image.description="Zendesk 티켓 데이터를 활용하여 AI Agent가 고객 지원 관련 인사이트를 제공할 수 있도록 하는 MCP(Model Context Protocol) 서버"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Saltware"
LABEL org.opencontainers.image.source="https://github.com/saltware/zendesk-mcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy source code
COPY src ./src

# HTTP 포트 노출 (Streamable HTTP)
EXPOSE 8000

# 환경변수 기본값
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV PYTHONUNBUFFERED=1

# MCP 서버를 HTTP 모드로 실행
CMD ["python", "-m", "src"]
