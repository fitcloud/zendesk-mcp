"""
Zendesk API Client

Zendesk API v2와 통신하는 비동기 HTTP 클라이언트
"""

import os
from typing import Any

import httpx


class ZendeskClient:
    """Zendesk API v2 클라이언트"""

    # 요청 회사 커스텀 필드 ID
    COMPANY_FIELD_ID = "360028549453"

    def __init__(self):
        self.subdomain = os.getenv("ZENDESK_SUBDOMAIN")
        self.email = os.getenv("ZENDESK_EMAIL")
        self.api_token = os.getenv("ZENDESK_API_TOKEN")
        self.oauth_access_token = os.getenv("ZENDESK_OAUTH_ACCESS_TOKEN")

        # OAuth 액세스 토큰이 있으면 우선 사용, 없으면 API 토큰 사용
        self.use_oauth = bool(self.oauth_access_token)

        if not self.use_oauth and not all([self.subdomain, self.email, self.api_token]):
            raise ValueError(
                "Missing Zendesk credentials. "
                "Please set ZENDESK_OAUTH_ACCESS_TOKEN or "
                "(ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, and ZENDESK_API_TOKEN)."
            )

        if not self.subdomain:
            raise ValueError(
                "Missing Zendesk subdomain. Please set ZENDESK_SUBDOMAIN."
            )

        self.base_url = f"https://{self.subdomain}.zendesk.com/api/v2"

    def _get_auth(self) -> tuple[str, str] | None:
        """API Token 인증 정보 반환 (OAuth 사용 시 None)"""
        if self.use_oauth:
            return None
        return (f"{self.email}/token", self.api_token)

    def _get_headers(self) -> dict[str, str]:
        """요청 헤더 반환 (OAuth 사용 시 Bearer 토큰 포함)"""
        if self.use_oauth:
            return {"Authorization": f"Bearer {self.oauth_access_token}"}
        return {}

    async def search_tickets(self, query: str) -> list[dict[str, Any]]:
        """
        티켓 검색 API 호출

        Args:
            query: Zendesk 검색 쿼리 문자열

        Returns:
            검색된 티켓 목록
        """
        all_results = []
        url = f"{self.base_url}/search.json"
        params = {"query": query}

        async with httpx.AsyncClient() as client:
            while url:
                response = await client.get(
                    url,
                    params=params if "search.json" in url else None,
                    auth=self._get_auth(),
                    headers=self._get_headers(),
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                all_results.extend(data.get("results", []))

                # 페이지네이션 처리
                url = data.get("next_page")
                params = None  # next_page URL에는 이미 파라미터가 포함됨

        return all_results

    async def get_ticket(self, ticket_id: int) -> dict[str, Any]:
        """
        티켓 상세 조회

        Args:
            ticket_id: Zendesk 티켓 ID

        Returns:
            티켓 상세 정보
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}.json",
                auth=self._get_auth(),
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("ticket", {})

    async def get_user(self, user_id: int) -> dict[str, Any]:
        """
        사용자 정보 조회

        Args:
            user_id: Zendesk 사용자 ID

        Returns:
            사용자 정보
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}.json",
                auth=self._get_auth(),
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("user", {})

    async def get_users_batch(self, user_ids: list[int]) -> dict[int, dict[str, Any]]:
        """
        여러 사용자 정보 일괄 조회

        Args:
            user_ids: 사용자 ID 목록

        Returns:
            {user_id: user_info} 형태의 딕셔너리
        """
        if not user_ids:
            return {}

        # 중복 제거
        unique_ids = list(set(user_ids))
        ids_param = ",".join(str(uid) for uid in unique_ids)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/show_many.json",
                params={"ids": ids_param},
                auth=self._get_auth(),
                headers=self._get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            users = data.get("users", [])
            return {user["id"]: user for user in users}

    def extract_company_name(self, ticket: dict[str, Any]) -> str:
        """
        티켓에서 요청 회사명 추출

        Args:
            ticket: 티켓 정보

        Returns:
            회사명 (없으면 "Unknown")
        """
        custom_fields = ticket.get("custom_fields", [])
        for field in custom_fields:
            if str(field.get("id")) == self.COMPANY_FIELD_ID:
                return field.get("value") or "Unknown"
        return "Unknown"

    def extract_tags(self, ticket: dict[str, Any]) -> list[str]:
        """
        티켓에서 태그 목록 추출

        Args:
            ticket: 티켓 정보

        Returns:
            태그 목록
        """
        return ticket.get("tags", [])
