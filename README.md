# 📊 매일 아침 시황 브리핑 — Telegram 자동화

매일 오전 10시 KST, Claude AI가 최신 시황을 분석하여 Telegram으로 자동 전송합니다.

## 📁 파일 구조

```
your-repo/
├── .github/
│   └── workflows/
│       └── market-briefing.yml   ← GitHub Actions 워크플로우
├── run_briefing.py               ← 메인 실행 스크립트
└── README.md
```

---

## 🤖 동작 방식 (2단계 에이전트)

```
Agent 1 (검색 전문)           Agent 2 (분석 전문)
─────────────────             ─────────────────
웹 검색 최대 7회              외부 검색 없음
핵심 수치 추출           →    JSON 데이터만 사용
JSON으로 정리                 시황 분석 + 포트폴리오 추천 생성
```

### 분석 항목
- 🇰🇷 코스피 / 삼성전자 (외국인 수급, 뉴스, 증권사 의견)
- 🇺🇸 미국 주식시장 (S&P500, 다우, 나스닥, VIX, 선물)
- 🥇 금 (Gold)
- ₿ 비트코인

### 포트폴리오 추천 종목
삼성전자, 미국 10년 국채 선물, QQQ, SCHD, 비트코인

---

## 🚀 설정 단계

### Step 1: Telegram 봇 만들기

1. Telegram에서 **@BotFather** 검색 후 채팅 시작
2. `/newbot` 명령어 입력 → 봇 이름 및 username 설정
3. 발급된 **API Token** 복사
   - 예: `7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: 내 Chat ID 확인

1. 만든 봇에게 `/start` 메시지 전송
2. 아래 URL 브라우저에서 접속 (토큰 교체):
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. 응답 JSON에서 `"chat"` → `"id"` 값 복사

### Step 3: Anthropic API Key 발급

1. https://console.anthropic.com 접속
2. **API Keys** → **Create Key** → 키 복사

### Step 4: GitHub Secrets 등록

리포지토리 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `TELEGRAM_BOT_TOKEN` | BotFather 토큰 |
| `TELEGRAM_CHAT_ID` | Chat ID 숫자 |

### Step 5: 파일 업로드 확인

- `run_briefing.py` → 리포지토리 **루트**에 위치
- `market-briefing.yml` → `.github/workflows/` 폴더 안에 위치
- `README.md` → 리포지토리 **루트**에 위치 (스케줄 활성화에 필요)

---

## ⏰ 실행 스케줄

```yaml
cron: '0 1 * * 1-5'
```

| KST 시각 | UTC 시각 | 요일 |
|---------|---------|------|
| 매일 오전 10:00 | 당일 01:00 | 월~금 |

> cron 표현식 도구: https://crontab.guru

---

## 🔧 수동 실행

**Actions 탭 → 📊 Daily Market Briefing → Run workflow**

---

## 💰 예상 비용 (월 기준)

| 항목 | 비용 |
|------|------|
| Claude API (Sonnet 4.6, 2단계 에이전트) | 약 $1~2/월 |
| Telegram Bot | **무료** |
| GitHub Actions | **무료** (월 2,000분 무료) |

---

## ❓ 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `AuthenticationError` | API 키 오류 | Secrets에서 ANTHROPIC_API_KEY 재확인 |
| `rate_limit_error` | 토큰 한도 초과 | run_briefing.py에서 max_uses 줄이기 |
| Telegram 404 | 봇 토큰 오류 | BotFather에서 토큰 재발급 후 Secret 업데이트 |
| 메시지 미수신 | 봇 미시작 | Telegram에서 봇에게 `/start` 전송 |
| 스케줄 미실행 | README.md 루트 미위치 또는 브랜치 문제 | README.md를 루트로 이동, main 브랜치 확인 |
