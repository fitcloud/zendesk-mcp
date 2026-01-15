"""
검색 쿼리 필터 유틸리티

공통으로 적용되는 티켓 제외 조건 정의
"""

# 검색에서 제외할 조건들
EXCLUDED_CC_EMAILS = ["alarm@saltware.co.kr"]
EXCLUDED_TAGS = ["matrixtalk", "proactive-phd"]
EXCLUDED_COMPANIES = ["솔트웨어"]

# 제목에 포함된 경우 제외할 문자열 (쿼리 단에서 필터링)
EXCLUDED_SUBJECT_KEYWORDS = ["PHD_"]

# 요청 회사 커스텀 필드 ID
COMPANY_FIELD_ID = "360028549453"


def get_exclusion_query() -> str:
    """
    검색 쿼리에 추가할 제외 조건 문자열을 반환합니다.

    제외 조건:
    - 특정 이메일이 참조(CC)에 포함된 티켓
    - 특정 태그가 설정된 티켓
    - 특정 요청 회사의 티켓
    - 특정 문자열이 제목에 포함된 티켓

    Returns:
        Zendesk 검색 쿼리에 추가할 제외 조건 문자열
    """
    exclusions = []

    # CC 이메일 제외
    for email in EXCLUDED_CC_EMAILS:
        exclusions.append(f"-cc:{email}")

    # 태그 제외
    for tag in EXCLUDED_TAGS:
        exclusions.append(f"-tags:{tag}")

    # 요청 회사 제외
    for company in EXCLUDED_COMPANIES:
        exclusions.append(f"-custom_field_{COMPANY_FIELD_ID}:{company}")

    # 제목 키워드 제외
    for keyword in EXCLUDED_SUBJECT_KEYWORDS:
        exclusions.append(f"-subject:{keyword}")

    return " ".join(exclusions)
