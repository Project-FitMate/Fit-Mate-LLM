# Fit-Mate-LLM

FitMate AI 서비스. Next.js 백엔드가 호출하는 내부 HTTP API.

- `POST /recommend` — 사용자 사진 + 선택 정보 → LLM이 네이버 검색 쿼리 생성 → 네이버 쇼핑 검색 결과 반환
- `POST /fitting` — 사용자 사진 + 선택한 옷 이미지 → Gemini 이미지 합성으로 가상 피팅 결과 생성
- `GET /health`

## 실행

```bash
uv sync
cp .env.example .env  # 키 채움
uv run uvicorn app.main:app --reload
```

## 인증

모든 비공개 엔드포인트는 `X-API-Key: $API_KEY` 헤더 필요.

## 프롬프트 교체

`app/prompts/*.yaml`에 system/user 분리된 템플릿 추가 후, 요청 본문의 `prompt_template` 필드에 확장자 제외 파일명 전달 (예: `"query_v2"`).

## 테스트

```bash
uv run pytest                       # 단위/모킹 테스트
uv run pytest -m integration        # .env의 실제 키로 외부 API 호출
```
