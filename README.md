# Fit-Mate-LLM

FitMate AI 서비스. NestJS 백엔드(`Fit-Mate-SERVER`)가 호출하는 내부 HTTP API.

## 엔드포인트

- `GET /outfit?part=&minPrice=&maxPrice=` — `OutfitPart` + 가격대로 LLM이 네이버 쇼핑 검색 쿼리 생성 → 결과를 `OutfitItem[]` 으로 반환
  - `part`: `FULL | TOP | BOTTOM | OUTER | DRESS | SHOES | HAT`
  - 응답 아이템: `{ image, brand, name, price, link }`
- `POST /fitting` — `{ userImage, outfitImage }` (base64) → Gemini 이미지 합성 → `{ image }` (base64)
  - 이미지 mime type은 base64 매직 바이트로 자동 감지 (PNG/JPEG/WEBP)
  - 60초 타임아웃 (`FITTING_TIMEOUT_SECONDS`)
- `GET /health`

백엔드와의 통신은 인증 없음. 신뢰된 내부망 전제.

## 실행

```bash
uv sync
cp .env.example .env  # 키 채움
uv run uvicorn app.main:app --reload
```

백엔드 측 `AI_MODEL_URL`에 본 서버 주소(`http://host:8000`)를 지정하면 통합 완료.

## 프롬프트 교체

`app/prompts/*.yaml`에 system/user 분리된 템플릿 파일을 두고 코드에서 이름으로 로드한다. 현재 사용 중인 템플릿:

- `query_default.yaml` — `/outfit`의 검색 쿼리 생성
- `fitting_default.yaml` — `/fitting`의 이미지 합성

실험적으로 교체하려면 파일을 추가하고 `services/*.py`의 `load(...)` 호출 인자를 바꾸면 된다.

## 테스트

```bash
uv run pytest                       # 단위/모킹 테스트
uv run pytest -m integration        # .env의 실제 키로 외부 API 호출
```
