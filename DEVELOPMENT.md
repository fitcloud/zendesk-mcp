# Development Guide

Zendesk MCP Server 개발 및 배포 가이드입니다.

## 📋 목차

- [로컬 개발 환경](#로컬-개발-환경)
- [Docker 이미지 빌드](#docker-이미지-빌드)
- [Docker Hub 배포](#docker-hub-배포)
- [AWS ECR Public 배포](#aws-ecr-public-배포)
- [프로젝트 구조](#프로젝트-구조)
- [검색 제외 조건 수정](#검색-제외-조건-수정)

## 💻 로컬 개발 환경

### 요구사항

- Python 3.11+
- Zendesk 계정 및 API 토큰

### 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/fitcloud/zendesk-mcp.git
cd zendesk-mcp

# 가상환경 설정
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 Zendesk 자격 증명 입력

# 서버 실행
python -m src
```

### Docker Compose로 개발

```bash
# .env 파일 생성
cp .env.example .env
# .env 파일에 Zendesk 자격 증명 설정

# 서비스 시작
docker compose up -d

# 로그 확인
docker compose logs -f

# 서비스 중지
docker compose down
```

## 🐳 Docker 이미지 빌드

### 단일 플랫폼 빌드 (로컬 테스트용)

```bash
# 이미지 빌드
docker build -t zendesk-mcp:latest .

# 로컬 테스트
docker run -d \
  --name zendesk-mcp-test \
  -p 8000:8000 \
  -e ZENDESK_SUBDOMAIN=your-subdomain \
  -e ZENDESK_EMAIL=your-email@example.com \
  -e ZENDESK_API_TOKEN=your-api-token \
  zendesk-mcp:latest

# 테스트 후 정리
docker stop zendesk-mcp-test && docker rm zendesk-mcp-test
```

### 멀티플랫폼 빌드 (linux/amd64, linux/arm64)

멀티플랫폼 이미지는 `docker buildx`를 사용하며, **빌드와 푸시를 동시에** 수행해야 합니다.

```bash
# buildx 빌더 생성 (최초 1회)
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap

# 멀티플랫폼 빌드 + 푸시 (반드시 --push 옵션 필요)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry/zendesk-mcp:latest \
  -t your-registry/zendesk-mcp:1.0.0 \
  --push .
```

> ⚠️ **중요**: `docker buildx`로 빌드한 멀티플랫폼 이미지는 로컬에 저장되지 않습니다.
> 따라서 `--push` 옵션으로 빌드와 푸시를 한번에 수행해야 합니다.

## 📦 Docker Hub 배포

```bash
# Docker Hub 로그인
docker login

# 멀티플랫폼 빌드 + 푸시
docker buildx build --platform linux/amd64,linux/arm64 \
  -t saltware/zendesk-mcp:latest \
  -t saltware/zendesk-mcp:1.0.0 \
  --push .
```

## ☁️ AWS ECR Public 배포

### 레포지토리 생성 (최초 1회)

```bash
aws ecr-public create-repository \
  --repository-name zendesk-mcp \
  --region us-east-1
```

### 이미지 푸시 (멀티플랫폼)

```bash
# ECR Public 로그인
aws ecr-public get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin public.ecr.aws/saltware

# 멀티플랫폼 빌드 + 푸시
docker buildx build --platform linux/amd64,linux/arm64 \
  -t public.ecr.aws/saltware/zendesk-mcp:latest \
  -t public.ecr.aws/saltware/zendesk-mcp:1.0.0 \
  --push \
  --no-cache .
```

### 기존 이미지 삭제

```bash
# 특정 태그 이미지 삭제
aws ecr-public batch-delete-image \
  --repository-name zendesk-mcp \
  --region us-east-1 \
  --image-ids imageTag=1.0.0

# 여러 태그 삭제
aws ecr-public batch-delete-image \
  --repository-name zendesk-mcp \
  --region us-east-1 \
  --image-ids imageTag=1.0.0 imageTag=1.0.1
```

### 카탈로그 데이터 업데이트

ECR Public Gallery의 설명을 업데이트하려면:

```bash
# catalog-data.json 사용
aws ecr-public put-repository-catalog-data \
  --repository-name zendesk-mcp \
  --catalog-data file://catalog-data.json \
  --region us-east-1
```

또는 description.md 파일을 사용하여:

```bash
aws ecr-public put-repository-catalog-data \
  --repository-name zendesk-mcp \
  --catalog-data "aboutText=$(cat description.md)" \
  --region us-east-1
```

## 📁 프로젝트 구조

```
zendesk-mcp/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # 진입점
│   ├── server.py             # MCP 서버 설정
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_tickets.py
│   │   ├── search_tickets_by_tag.py
│   │   ├── search_tickets_with_keywords.py
│   │   ├── get_ticket_details.py
│   │   ├── get_top_agents.py
│   │   └── get_service_trends.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── zendesk_client.py  # Zendesk API 클라이언트
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic 모델
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py
│       └── query_filters.py   # 검색 제외 조건 정의
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
├── catalog-data.json          # ECR 카탈로그 데이터
├── description.md             # ECR 설명 (Markdown)
├── DEVELOPMENT.md             # 개발 가이드 (이 문서)
└── README.md                  # 사용자 가이드
```

## 🔧 검색 제외 조건 수정

모든 검색 도구에서 특정 티켓을 제외하려면 `src/utils/query_filters.py`를 수정합니다:

```python
# 제외할 CC 이메일 목록
EXCLUDED_CC_EMAILS = [
    "alarm@saltware.co.kr",
    # 추가 이메일...
]

# 제외할 태그 목록
EXCLUDED_TAGS = [
    "matrixtalk",
    "proactive-phd",
    # 추가 태그...
]
```

## 🔧 환경변수

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `ZENDESK_SUBDOMAIN` | Zendesk 서브도메인 | ✅ | - |
| `ZENDESK_EMAIL` | API 사용자 이메일 | ✅ | - |
| `ZENDESK_API_TOKEN` | API 토큰 | ✅ | - |
| `MCP_TRANSPORT` | 전송 방식 (http/stdio) | - | stdio |
| `MCP_HOST` | 서버 호스트 | - | 0.0.0.0 |
| `MCP_PORT` | 서버 포트 | - | 8000 |

## 📄 라이선스

MIT License
