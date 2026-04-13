"""
매일 아침 시황 분석 - 2단계 에이전트 구조
Agent 1: 웹 검색 → 핵심 데이터 JSON 추출
Agent 2: JSON 데이터 → 시황 분석 + 포트폴리오 추천
"""

import os
import sys
import json
import requests
import anthropic
from datetime import datetime, timezone, timedelta

# ────────────────────────────────────────────
# 설정
# ────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
NOW_KST = datetime.now(KST)
TODAY_STR = NOW_KST.strftime("%Y년 %m월 %d일")
WEEKDAY_KR = ["월", "화", "수", "목", "금"][NOW_KST.weekday()]

# ────────────────────────────────────────────
# Agent 1 프롬프트: 검색 → JSON 추출
# ────────────────────────────────────────────
AGENT1_PROMPT = f"""
오늘은 {TODAY_STR} ({WEEKDAY_KR}요일)이다.
아래 항목들을 웹 검색하여 핵심 수치만 추출하고, 반드시 JSON 형식으로만 응답하라.
설명, 해석, 마크다운 없이 순수 JSON만 출력할 것.

검색 항목:
1. 삼성전자 전일 종가, 오늘 현재가(또는 시초가), 등락률
2. 삼성전자 최근 3거래일 외국인 순매수/순매도 금액
3. 삼성전자 관련 24시간 이내 주요 뉴스 (호재/악재 각 1~2개)
4. 삼성전자 증권사 목표주가 및 투자의견 (3개 증권사)
5. S&P500, 다우존스, 나스닥 최근 종가 및 등락률 (날짜 명시)
6. VIX 현재 수치 및 전일 대비 변동
7. 미국 선물/프리마켓 현재 동향 및 수치
8. 미국 시장 주요 상승/하락 요인 (1~2개)
9. 금 현재 가격(달러/온스) 및 전일 대비 변동
10. 비트코인 및 이더리움 현재 가격 및 24시간 변동률, 주요 지지/저항선
11. 크립토 Fear & Greed Index 수치 및 단계명
12. 오늘/내일 주요 경제지표 발표 일정
13. 미국 10년물 국채 수익률 및 전일 대비 변동(bp)

출력 형식 (이 구조 그대로):
{{
  "date": "{TODAY_STR}",
  "weekday": "{WEEKDAY_KR}",
  "kospi": {{"price": null, "change_pct": null}},
  "samsung": {{
    "prev_close": null, "prev_close_date": null,
    "current": null, "change_pct": null,
    "foreign_net_3d": null,
    "news_positive": [], "news_negative": [],
    "analyst_targets": []
  }},
  "us_market": {{
    "date": null,
    "sp500": {{"price": null, "change_pct": null}},
    "dow": {{"price": null, "change_pct": null}},
    "nasdaq": {{"price": null, "change_pct": null}},
    "vix": {{"value": null, "change": null}},
    "futures": {{"sp500": null, "nasdaq": null}},
    "key_factors": []
  }},
  "gold": {{"price_usd": null, "change_pct": null, "key_factor": null}},
  "crypto": {{
    "bitcoin": {{"price": null, "change_24h": null, "support": null, "resistance": null}},
    "ethereum": {{"price": null, "change_24h": null, "support": null, "resistance": null}},
    "fear_greed": {{"value": null, "label": null}}
  }},
  "us10y_yield": {{"value": null, "change_bp": null}},
  "events": []
}}
"""

# ────────────────────────────────────────────
# Agent 2 프롬프트: JSON → 시황 분석
# ────────────────────────────────────────────
AGENT2_PROMPT_TEMPLATE = """
너는 한국 개인투자자를 위한 전문 시황 애널리스트다.

[중요 규칙]
- 외부 검색 금지, 입력된 데이터만 사용
- 데이터가 없으면 추정하지 말고 "데이터 없음" 명시
- 수치 단순 반복 금지, 데이터 해석과 인사이트에 집중
- 단정적 표현("반드시", "무조건", "확실히") 지양

[입력 데이터]
{JSON_DATA}

[분석 요구]

## [출력 형식]
제목: 📊 {TODAY_STR} ({WEEKDAY_KR}요일) 아침 시황 브리핑

**도입부**: 오늘 시장의 전체 톤을 2~3문장으로 요약 (리스크 온/오프, 핵심 테마, 전일 대비 분위기)

🔑 **오늘의 핵심 변수** (3~5개 번호 리스트)

🇰🇷 **코스피 / 삼성전자**
- 코스피 및 삼성전자 현황 해석
- 외국인 수급 동향이 주가에 미치는 영향 해석
- 주요 뉴스 호재/악재 정리
- 증권사 목표주가 및 투자의견

🇺🇸 **미국 주식시장**
- 주요 지수 현황 및 핵심 등락 요인 해석
- VIX 수준 해석 (공포/안도)
- 선물/프리마켓 동향 해석

🥇 **금 (Gold)**
- 현황 및 변동 요인 해석
- 구조적 전망 요인

₿ **비트코인 / 이더리움**
- 각 현황 및 기술적 지지/저항 해석
- Fear & Greed Index 해석

📋 **포트폴리오 종목별 추천**
아래 종목 각각에 대해 표 형식으로 작성:
종목 | 판단 | 이유 (2~3문장)

대상 종목:
- 삼성전자
- 미국 10년 국채 선물
- QQQ
- SCHD
- 비트코인
- 이더리움

판단 기준: 매수 / 분할 매수 / 보유 / 보유(관망) / 매도
확신도별 어조: 강한 확신 → "~가 유효합니다", 보통 → "~를 고려할 수 있습니다", 약한 → "~여부를 관찰할 필요가 있습니다"

📅 **오늘/내일 주요 이벤트**
(경제지표, 연준 이벤트, 실적 발표 등 구체적 일정)

⚠️ 본 분석은 참고 의견이며, 투자 판단은 본인 책임입니다. 저는 금융 전문가가 아닙니다.
"""

# ────────────────────────────────────────────
# Agent 1: 웹 검색 → JSON 데이터 수집
# ────────────────────────────────────────────
def run_agent1(client: anthropic.Anthropic) -> dict:
    print("🔍 [Agent 1] 웹 검색 및 데이터 수집 시작...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 7,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": AGENT1_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
    )

    # 텍스트 블록 추출
    text_parts = [
        block.text
        for block in response.content
        if hasattr(block, "text") and block.text
    ]
    raw_text = "\n".join(text_parts).strip()

    # JSON 파싱
    try:
        # 마크다운 코드블록 제거 후 파싱
        clean = raw_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        print(f"✅ [Agent 1] 데이터 수집 완료")
        return data
    except json.JSONDecodeError:
        print(f"⚠️ [Agent 1] JSON 파싱 실패, 원본 텍스트 사용")
        return {"raw": raw_text}


# ────────────────────────────────────────────
# Agent 2: JSON → 시황 분석
# ────────────────────────────────────────────
def run_agent2(client: anthropic.Anthropic, market_data: dict) -> str:
    print("📝 [Agent 2] 시황 분석 시작...")

    prompt = AGENT2_PROMPT_TEMPLATE.format(
        JSON_DATA=json.dumps(market_data, ensure_ascii=False, indent=2),
        TODAY_STR=TODAY_STR,
        WEEKDAY_KR=WEEKDAY_KR,
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text_parts = [
        block.text
        for block in response.content
        if hasattr(block, "text") and block.text
    ]
    result = "\n".join(text_parts).strip()

    if not result:
        raise ValueError("Agent 2로부터 응답을 받지 못했습니다.")

    print(f"✅ [Agent 2] 분석 완료 (총 {len(result)}자)")
    return result


# ────────────────────────────────────────────
# Telegram 전송
# ────────────────────────────────────────────
def split_text(text: str, max_len: int = 3800) -> list[str]:
    import re
    section_pattern = re.compile(r'(?=\n(?:📊|🇰🇷|🇺🇸|🥇|₿|📋|🔑|📅|⚠️))')
    sections = section_pattern.split(text)

    chunks = []
    current = ""

    for section in sections:
        if len(section) > max_len:
            for line in section.split("\n"):
                if len(current) + len(line) + 1 > max_len:
                    if current.strip():
                        chunks.append(current.strip())
                    current = line
                else:
                    current += "\n" + line
        elif len(current) + len(section) > max_len:
            if current.strip():
                chunks.append(current.strip())
            current = section
        else:
            current += section

    if current.strip():
        chunks.append(current.strip())

    return chunks


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    chunks = split_text(text)
    print(f"📤 Telegram 전송 시작 ({len(chunks)}개 메시지)...")

    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": True,
        }
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
        f"❌ 시황 브리핑 생성 실패\n\n"
        f"날짜: {TODAY_STR} ({WEEKDAY_KR}요일)\n"
        f"오류: {type(error).__name__}: {str(error)[:200]}"
    )
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg},
        timeout=15,
    )


# ────────────────────────────────────────────
# 메인
# ────────────────────────────────────────────
if __name__ == "__main__":
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        # Agent 1: 데이터 수집
        market_data = run_agent1(client)

        # Agent 2: 분석
        briefing = run_agent2(client, market_data)

        # Telegram 전송
        send_telegram(briefing)
        print("🎉 완료!")

    except Exception as e:
        print(f"💥 오류 발생: {e}", file=sys.stderr)
        send_error_notification(e)
        sys.exit(1)
