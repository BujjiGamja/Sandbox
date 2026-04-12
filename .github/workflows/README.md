# 📊 매일 아침 시황 브리핑 — Telegram 자동화 설정 가이드

## 📁 파일 구조

```
your-repo/
├── .github/
│   └── workflows/
│       └── market-briefing.yml   ← GitHub Actions 워크플로우
├── scripts/
│   └── run_briefing.py           ← 메인 실행 스크립트
└── README.md
```

---

## 🚀 설정 단계

### Step 1: Telegram 봇 만들기

1. Telegram에서 **@BotFather** 검색 후 채팅 시작
2. `/newbot` 명령어 입력
3. 봇 이름 입력 (예: `My Market Briefing`)
4. 봇 username 입력 (예: `my_market_bot`) — 반드시 `bot`으로 끝나야 함
5. 발급된 **HTTP API Token** 복사해두기
   - 예: `7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: 내 Chat ID 확인하기

1. 방금 만든 봇에게 아무 메시지나 보내기 (예: `/start`)
2. 브라우저에서 아래 URL 접속 (토큰 교체):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. 응답 JSON에서 `"chat"` → `"id"` 값 복사
   - 예: `123456789`

### Step 3: Anthropic API Key 발급

1. https://console.anthropic.com 접속
2. **API Keys** 메뉴 → **Create Key**
3. 생성된 키 복사 (sk-ant-api03-xxxxx...)

### Step 4: GitHub 리포지토리에 Secrets 등록

GitHub 리포지토리 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름         | 값                              |
|--------------------|---------------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic API 키               |
| `TELEGRAM_BOT_TOKEN` | BotFather에서 받은 토큰         |
| `TELEGRAM_CHAT_ID`   | Step 2에서 확인한 Chat ID       |

### Step 5: GitHub Actions 활성화 확인

- 리포지토리 → **Actions** 탭 → Actions가 활성화되어 있는지 확인
- 비활성화 상태라면 **"I understand my workflows, go ahead and enable them"** 버튼 클릭

---

## ⏰ 실행 스케줄

```yaml
cron: '0 1 * * 1-5'
```

| KST 시각 | UTC 시각 | 요일 |
|---------|---------|------|
| 매일 오전 10:00 | 당일 01:00 | 월~금 |

> 필요시 `market-briefing.yml`의 cron 표현식을 수정하세요.
> - 오전 9시로 변경: `'0 0 * * 1-5'`
> - cron 표현식 도구: https://crontab.guru

---

## 🔧 수동 실행 방법

GitHub Actions 탭 → **📊 Daily Market Briefing** → **Run workflow** 버튼

---

## 💰 예상 비용 (월 기준)

| 항목 | 비용 |
|------|------|
| Claude API (sonnet, ~4K 토큰/일) | 약 $3~6/월 |
| Telegram Bot | **무료** |
| GitHub Actions | **무료** (월 2,000분 무료) |

---

## ❓ 자주 발생하는 오류

| 오류 메시지 | 원인 | 해결 |
|-----------|------|------|
| `AuthenticationError` | API 키 오류 | Secrets에서 ANTHROPIC_API_KEY 재확인 |
| `Forbidden` | Chat ID 오류 | 봇에게 먼저 메시지를 보낸 뒤 재시도 |
| 메시지 미수신 | Bot 미시작 | Telegram에서 봇에게 `/start` 전송 |
| `Bad Request: can't parse entities` | Markdown 파싱 오류 | 스크립트가 자동으로 plain text로 재시도 |
