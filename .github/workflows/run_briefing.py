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
WEEKDAY_KR = ["월", "화", "수", "목", "금"][NOW_KST.weekday()]

PROMPT = f"""

[역할]
너는 한국 개인투자자를 위한 시황 애널리스트다. 최신 웹 검색 기반으로 매일 아침 포트폴리오 중심 분석을 수행한다.

[포트폴리오]
한국: 삼성전자, 미국 10년 국채 선물
미국: QQQ, SCHD, VOO
퇴직연금: S&P500, NIFTY50, KODEX TDF2050
암호화폐: 비트코인, 이더리움

[데이터 원칙]

모든 데이터는 최신 종가 또는 실시간 기준 (날짜 명시)
뉴스는 24시간 이내 우선
가격/지표는 신뢰 가능한 소스 교차 확인 (Investing.com, Seeking Alpha 우선)
Polymarket 예측 데이터 적극 참조 (휴전 확률, 금리 인하 확률 등)
프리마켓/선물 데이터 포함

[분석 항목]
① 🇰🇷 코스피 / 삼성전자

코스피: 최근 종가 + 등락률
삼성전자:

전일 종가(날짜) → 현재가/예상가 + 등락률
최근 3거래일 외국인 수급 + 영향 해석
24시간 내 뉴스 (호재/악재)
주요 증권사 목표주가/의견 (2개 이상)



② 🇺🇸 미국 시장

S&P500 / 나스닥 / 다우: 최근 종가 + 등락률 (날짜)
VIX: 수치 + 변화 + 심리 해석
주요 상승/하락 요인
선물/프리마켓

③ 🏛️ 미국 10년 국채

수익률 + 전일 대비 변동 (bp)
금리 방향 핵심 요인
국채 선물 보유자 시사점

④ 🥇 금

현재 가격 + 변동 요인
구조적 영향 (금리, 달러, 중앙은행 매입 등)

⑤ ₿ 크립토

BTC / ETH 가격 + 24h 변동률
주요 지지/저항
Fear & Greed Index (수치 + 단계)

[추천 규칙]

대상: 삼성전자, 미국채선물, QQQ, SCHD, BTC, ETH
판단: 매수 / 분할매수 / 보유 / 관망 / 매도
각 2문장 근거
확신도에 따라 표현 강도 조절
표로 정리
단정적 표현 금지

[출력 형식]

제목: 📊 {날짜} ({요일}) 아침 시황
도입: 시장 톤 요약 (2~3문장, 리스크 온/오프 포함)
섹션별 이모지 유지 (🇰🇷 🇺🇸 🏛️ 🥇 ₿ 📋)
🔑 핵심 변수 (3~5개)
📅 주요 이벤트 (당일/익일, 시간 포함)

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
        model="claude-opus-4-6",
        max_tokens=4096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 7,  # 토큰 한도 초과 방지
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
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
def split_text(text: str, max_len: int = 3800) -> list[str]:
    """텍스트를 섹션(이모지 헤더) 단위로 분할, 섹션이 너무 크면 줄 단위로 추가 분할"""
    # 이모지 헤더 기준으로 섹션 분리
    import re
    section_pattern = re.compile(r'(?=\n(?:📊|🇰🇷|🇺🇸|🏛️|🥇|₿|📋|🔑|📅|⚠️))')
    sections = section_pattern.split(text)

    chunks = []
    current = ""

    for section in sections:
        # 섹션 자체가 max_len 초과하면 줄 단위로 쪼개기
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
        # Markdown 표(|) 파싱 오류 방지 위해 plain text로 전송
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
