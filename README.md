# Zendesk MCP Server

Zendesk 티켓 데이터를 활용하여 AI Agent가 고객 지원 관련 인사이트를 제공할 수 있도록 하는 MCP(Model Context Protocol) 서버입니다.

## 🚀 주요 기능

| 도구 | 설명 |
|------|------|
| `search_tickets_by_tag` | 서비스 분류 태그 기반 티켓 검색 및 고객사별 집계 |
| `search_tickets_with_keywords` | 키워드 기반 티켓 검색 (태그 없는 과거 티켓용) |
| `search_tickets` | 자유 검색어로 티켓 검색 |
| `get_ticket_details` | 특정 티켓의 상세 정보 조회 |
| `get_top_agents` | 기간 내 가장 많은 티켓을 해결한 담당자 조회 |
| `get_service_trends` | 서비스별 문의 빈도 분석 |

## 📋 사전 요구사항

- Docker
- Zendesk 계정 및 API 토큰

## ⚡ 빠른 시작

### Docker 실행

```bash
docker run -d \
  --name zendesk-mcp \
  -p 8000:8000 \
  -e ZENDESK_SUBDOMAIN=your-subdomain \
  -e ZENDESK_EMAIL=your-email@example.com \
  -e ZENDESK_API_TOKEN=your-api-token \
  public.ecr.aws/saltware/zendesk-mcp:latest
```

### 환경변수

| 변수 | 설명 | 필수 |
|------|------|:----:|
| `ZENDESK_SUBDOMAIN` | Zendesk 서브도메인 | ✅ |
| `ZENDESK_EMAIL` | API 사용자 이메일 | ✅ |
| `ZENDESK_API_TOKEN` | API 토큰 | ✅ |
| `MCP_TRANSPORT` | 전송 방식 (`http`/`stdio`) | - |
| `MCP_HOST` | 서버 호스트 (기본값: `0.0.0.0`) | - |
| `MCP_PORT` | 서버 포트 (기본값: `8000`) | - |

## 🔌 클라이언트 연결

### Claude Desktop / Cursor

`mcp.json` 또는 `mcp_settings.json`에 추가:

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ZENDESK_SUBDOMAIN=your-subdomain",
        "-e", "ZENDESK_EMAIL=your-email@example.com",
        "-e", "ZENDESK_API_TOKEN=your-api-token",
        "public.ecr.aws/saltware/zendesk-mcp:latest"
      ]
    }
  }
}
```

### HTTP 모드 연결

서버를 HTTP 모드로 실행 후:

```json
{
  "mcpServers": {
    "zendesk": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## 💬 사용 예시

AI Agent에게 다음과 같이 질문할 수 있습니다:

- "최근 90일간 모니터링 관련 문의가 많은 고객사를 찾아줘"
- "Datadog, Prometheus, 관제 키워드로 관심 고객사를 검색해줘"
- "이번 달 티켓 해결 실적이 가장 좋은 담당자는 누구야?"
- "최근 서비스별 문의 트렌드를 분석해줘"

## 📖 도구 상세

### search_tickets_by_tag

서비스 분류 태그 기반으로 티켓을 검색하고 고객사별로 집계합니다.

**파라미터:**
- `service_tag` (필수): 검색할 서비스 분류 태그
- `period_days` (기본값: 365): 검색 기간 (일)

### search_tickets_with_keywords

키워드 기반으로 티켓을 검색하고 고객사별로 집계합니다. 서비스 태그가 없는 과거 티켓 검색에 유용합니다.

**파라미터:**
- `keywords` (필수): 검색할 키워드 목록
- `period_days` (기본값: 365): 검색 기간 (일)

### search_tickets

자유 검색어로 티켓을 검색합니다.

**파라미터:**
- `query` (필수): 검색 쿼리
- `status`: 티켓 상태 필터 (open, pending, hold, solved, closed)
- `period_days`: 검색 기간 (일)
- `limit` (기본값: 50): 반환할 최대 티켓 수

### get_ticket_details

특정 티켓의 상세 정보를 조회합니다.

**파라미터:**
- `ticket_id` (필수): Zendesk 티켓 ID

### get_top_agents

기간 내 가장 많은 티켓을 해결한 담당자를 조회합니다.

**파라미터:**
- `period_days` (기본값: 30): 검색 기간 (일)
- `limit` (기본값: 10): 반환할 담당자 수

### get_service_trends

서비스별 문의 빈도를 분석합니다.

**파라미터:**
- `period_days` (기본값: 90): 검색 기간 (일)
- `limit` (기본값: 10): 반환할 서비스 수

## 📚 추가 문서

- [개발 및 배포 가이드](DEVELOPMENT.md) - 로컬 개발, Docker 빌드, 배포 방법

## 📄 라이선스

MIT License
