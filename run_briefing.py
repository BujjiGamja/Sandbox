"""
매일 아침 시황 분석을 Claude API로 생성하여 Telegram으로 전송하는 스크립트
"""

import os
import sys
import requests
import anthropic
from datetime import datetime, timezone, timedelta

# ────────────────────────────────────────────
# 설정
# ────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
NOW_KST = datetime.now(KST)
TODAY_STR = NOW_KST.strftime("%Y년 %m월 %d일")
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"][NOW_KST.weekday()]

PROMPT = f"""
너는 한국 개인투자자를 위한 전문 시황 애널리스트야. 매일 아침 최신 웹 검색을 기반으로 아래 포트폴리오에 맞춘 시황 분석을 수행해줘.

---

## [내 포트폴리오]
- 한국주식: 삼성전자, 미국 10년 국채 선물
- 미국주식: QQQ, SCHD, VOO
- 퇴직연금: S&P500, 미국배당다우존스, NIFTY50, KODEX TDF 2050 액티브 적격
- 암호화폐: 비트코인, 이더리움 (다른 코인은 제외)

---

## [분석 규칙]

### 전체 톤 요약 (도입부)
- 분석 시작 전, 2~3문장으로 오늘 시장의 전체 톤을 요약해줘
- 리스크 온/오프 여부, 글로벌 핵심 테마, 전일 대비 분위기 변화를 포함

### 1. 코스피 / 삼성전자 🇰🇷
- 코스피 지수 현재가 (또는 최근 종가), 전일 대비 등락률
- 삼성전자: 전일 종가(날짜 명시) + 오늘 현재가(또는 프리마켓 예상가) 반드시 병기, 등락률 포함
- 삼성전자 최근 3거래일 외국인 누적 순매수/순매도 동향: 금액 또는 수량 단위로 검색하여 제시. 외국인 수급 방향이 주가에 미치는 영향을 해석할 것
- 삼성전자 관련 최신 뉴스 (24시간 이내), 호재, 악재 각각 정리
- 주요 증권사 목표주가 및 투자의견 (최소 2개 이상 증권사)

### 2. 미국 주식시장 🇺🇸
- S&P 500, 다우존스, 나스닥 — 가장 최근 마감일 종가 및 등락률 (날짜 명시 필수)
- VIX(변동성 지수): 현재 수치 및 전일 대비 증감(포인트, %) 반드시 포함. 시장 공포/안도 수준을 해석할 것
- 주요 상승/하락 요인
- 선물/프리마켓 동향 (반드시 검색 후 수치 제시)

### 3. 미국 10년 국채 🏛️
- 10년물 수익률 현재 수준 및 전일 대비 변동폭 (bp 단위)
- 금리 방향에 영향을 미치는 핵심 요인 (인플레, 연준 정책, 지정학)
- 국채 선물 보유자 관점에서의 시사점

### 4. 금 (Gold) 🥇
- 현재 금 가격 (달러/온스)
- 전일 대비 변동 및 주요 변동 요인
- 중장기 전망에 영향을 주는 구조적 요인 (중앙은행 매입, 달러 방향 등)

### 5. 비트코인 / 이더리움 ₿
- 비트코인, 이더리움 각각의 현재 가격
- 24시간 변동률
- 주요 기술적 지지/저항선 (구체적 가격 수준 명시)
- 크립토 Fear & Greed Index 수치를 반드시 검색하여 포함 (수치 + 단계명)
- 다른 암호화폐는 분석하지 말 것

### 6. 포트폴리오 종목별 매수/매도 추천 📋
- 위 포트폴리오의 모든 종목에 대해 각각 판단 제시
- 판단 기준: 매수 / 분할 매수 / 보유 / 보유(관망) / 매도
- 각 종목별로 판단 이유를 2~3문장으로 상세히 서술
- 종목별 확신도에 따라 어조의 강도를 차별화: 강한 확신 → "~가 유효합니다", 보통 → "~를 고려할 수 있습니다", 약한 → "~여부를 관찰할 필요가 있습니다"
- 표 형식으로 정리 (종목 | 판단 | 이유)
- 단정적 표현("반드시", "무조건", "확실히")은 지양

---

## [참조 소스 우선순위]
Investing.com, Bloomberg, Seeking Alpha를 비중있게 우선 참조.
Polymarket도 중요 참조 소스로 활용: 지정학 이벤트, 금리 인하 확률, 선거 등 시장 심리를 반영하는 예측 시장 데이터를 적극 참조할 것.
CNBC, Reuters, 한경, 연합뉴스 등도 보조 참조.

---

## [데이터 정확성 규칙]
- 가격 데이터는 반드시 최신 종가 또는 실시간 데이터를 교차 확인할 것
- 반드시 가장 최근 마감된 거래일의 종가를 기준으로 분석할 것 (날짜 명시 필수)
- 선물/프리마켓 데이터도 반드시 검색 후 제시할 것
- 출처가 불분명하거나 검증 불가능한 수치는 사용하지 말 것
- 뉴스 신선도 규칙: 분석 시점 기준 24시간 이내의 뉴스만 우선 참조할 것
- 삼성전자 가격 표시 규칙: 반드시 ①전일 종가(날짜 명시)와 ②오늘 현재가(또는 장 시작 전이면 프리마켓/예상 시초가)를 함께 표시할 것

---

## [출력 형식]
- 제목: 📊 {TODAY_STR} ({WEEKDAY_KR}요일) 아침 시황 브리핑
- 도입부: 전체 시장 톤 요약 (2~3문장)
- 각 항목에 이모지 헤더 사용 (🇰🇷, 🇺🇸, 🏛️, 🥇, ₿, 📋)
- 🔑 오늘의 핵심 변수 섹션: 당일 시장에 가장 큰 영향을 줄 3~5개 이벤트/변수를 번호 리스트로 정리
- 📅 오늘/내일 주요 이벤트 섹션: 경제지표 발표, 연준 이벤트, 주요 기업 실적 발표 등 구체적 일정과 시간을 명시
- 포트폴리오 추천은 반드시 표 형식으로
- 마지막에 "⚠️ 본 분석은 참고 의견이며, 투자 판단은 본인 책임입니다. 저는 금융 전문가가 아닙니다."를 반드시 포함

---

지금 최신 정보를 웹 검색한 뒤, 오늘의 시황 분석을 시작해줘.
"""

# ────────────────────────────────────────────
# Claude API 호출 (웹 검색 포함)
# ────────────────────────────────────────────
def get_market_briefing() -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("🔍 Claude API 호출 중 (웹 검색 포함)...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 15,  # 충분한 검색 횟수 허용
            }
        ],
        messages=[{"role": "user", "content": PROMPT}],
    )

    # 텍스트 블록만 추출
    text_parts = [
        block.text
        for block in response.content
        if hasattr(block, "text") and block.text
    ]
    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError("Claude로부터 텍스트 응답을 받지 못했습니다.")

    print(f"✅ 브리핑 생성 완료 (총 {len(full_text)}자)")
    return full_text


# ────────────────────────────────────────────
# Telegram 전송 (4096자 초과 시 분할 전송)
# ────────────────────────────────────────────
def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    MAX_LEN = 4000  # Telegram 메시지 최대 길이 (여유 있게 설정)

    # 긴 텍스트를 줄 단위로 분할
    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > MAX_LEN:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk += "\n" + line
    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"📤 Telegram 전송 시작 ({len(chunks)}개 메시지)...")
    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        resp = requests.post(url, json=payload, timeout=15)

        if not resp.ok:
            # Markdown 파싱 오류 시 plain text 재시도
            payload["parse_mode"] = ""
            resp = requests.post(url, json=payload, timeout=15)

        if not resp.ok:
            print(f"❌ 메시지 {i}/{len(chunks)} 전송 실패: {resp.text}")
        else:
            print(f"✅ 메시지 {i}/{len(chunks)} 전송 완료")


# ────────────────────────────────────────────
# 실패 시 Telegram 오류 알림
# ────────────────────────────────────────────
def send_error_notification(error: Exception) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    msg = (
        f"❌ *시황 브리핑 생성 실패*\n\n"
        f"날짜: {TODAY_STR} ({WEEKDAY_KR}요일)\n"
        f"오류: `{type(error).__name__}: {str(error)[:200]}`"
    )
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
        timeout=15,
    )


# ────────────────────────────────────────────
# 메인
# ────────────────────────────────────────────
if __name__ == "__main__":
    try:
        briefing = get_market_briefing()
        send_telegram(briefing)
        print("🎉 완료!")
    except Exception as e:
        print(f"💥 오류 발생: {e}", file=sys.stderr)
        send_error_notification(e)
        sys.exit(1)
