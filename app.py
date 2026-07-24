"""
Monster Insight — AI 미디어 몬스터 헌터
'팩트수색대'를 게임형으로 확장한 미디어 리터러시 대시보드입니다.

필요한 Secrets (전부 선택 사항 — 없으면 데모 데이터/로컬 저장으로 동작합니다):
  GOOGLE_FACTCHECK_API_KEY   루머 유령 미션에서 실제 팩트체크 검색에 사용
  SOLAR_API_KEY              AI 환각 몬스터 미션 + 수사 요원 AI 질문 답변에 사용 (Upstage Solar)
  STDICT_API_KEY             각 사건 파일의 표준국어대사전 검색에 사용 (국립국어원)
  KRDICT_API_KEY             한국어기초사전 검색에 사용 (선택, 있으면 우선 조회)
  SUPABASE_URL               학생 플레이 기록을 저장할 Supabase 프로젝트 URL
  SUPABASE_KEY               Supabase anon/service key

이 파일에는 실제 키 값이 들어있지 않습니다. Streamlit Secrets에 위 이름으로 등록하세요.
"""

import html
import os
import random
import re
from base64 import b64encode
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Monster Insight", page_icon="🧠", layout="wide")

# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------

def secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


GOOGLE_FACTCHECK_API_KEY = secret("GOOGLE_FACTCHECK_API_KEY")
SOLAR_API_KEY = secret("SOLAR_API_KEY")
STDICT_API_KEY = secret("STDICT_API_KEY")
KRDICT_API_KEY = secret("KRDICT_API_KEY")
SUPABASE_URL = secret("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = secret("SUPABASE_KEY")


# ---------------------------------------------------------------------------
# 스타일 (팩트수색대의 사이버 테마를 계승)
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');

    .stApp {
        background:
            radial-gradient(circle at 20% 10%, rgba(56,189,248,0.16), transparent 40%),
            radial-gradient(circle at 85% 15%, rgba(167,139,250,0.12), transparent 45%),
            repeating-linear-gradient(0deg, rgba(56,189,248,0.06) 0px, rgba(56,189,248,0.06) 1px, transparent 1px, transparent 46px),
            repeating-linear-gradient(90deg, rgba(56,189,248,0.06) 0px, rgba(56,189,248,0.06) 1px, transparent 1px, transparent 46px),
            linear-gradient(180deg, #04070f 0%, #0a0f24 45%, #120a2e 100%);
        background-attachment: fixed;
    }
    h1, h2, h3, h4, h5, h6 { color: #eaf6ff; }

    .cyber-title {
        font-family: 'Orbitron', sans-serif; font-weight: 900; color: #ffffff;
        font-size: 34px; letter-spacing: 0.5px; margin: 0;
        text-shadow: 0 0 16px rgba(167,139,250,0.55);
    }
    .cyber-sub { color:#c9b8f5; font-size:0.85rem; margin-top:-2px; }
    .cyber-tagline {
        color:#cdeaff; font-size:0.95rem; margin:6px 0 4px;
        border-left:3px solid #a78bfa; padding-left:10px;
    }

    div[class*="st-key-panel-"] {
        background: rgba(255, 255, 255, 0.97) !important;
        border: 1px solid rgba(167,139,250,0.35) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 18px rgba(0,0,0,0.28);
    }
    div[class*="st-key-panel-"] h1, div[class*="st-key-panel-"] h2,
    div[class*="st-key-panel-"] h3, div[class*="st-key-panel-"] h4,
    div[class*="st-key-panel-"] p, div[class*="st-key-panel-"] span,
    div[class*="st-key-panel-"] label, div[class*="st-key-panel-"] li,
    div[class*="st-key-panel-"] strong, div[class*="st-key-panel-"] b,
    div[class*="st-key-panel-"] em, div[class*="st-key-panel-"] a,
    div[class*="st-key-panel-"] code {
        color: #16233b !important;
    }

    .monster-card {
        position: relative;
        border: 1px solid rgba(167,139,250,0.55);
        border-radius: 16px;
        box-shadow: 0 0 22px rgba(167,139,250,0.28);
        padding: 22px 16px;
        text-align: center;
        background: radial-gradient(circle at 50% 0%, rgba(167,139,250,0.14), rgba(8,10,24,0.9));
    }
    .monster-emoji { font-size: 58px; line-height: 1; }
    .monster-name {
        font-family: 'Orbitron', sans-serif; font-weight: 700; color: #ffffff;
        font-size: 20px; margin: 8px 0 2px; text-shadow: 0 0 8px rgba(167,139,250,0.65);
    }
    .monster-cat { font-size: 12.5px; color:#9fd6f5; letter-spacing: 1px; }
    .monster-intro { font-size: 14.5px; color:#d7e6ff; margin-top:10px; line-height:1.55; }

    .dex-card {
        border-radius: 14px; padding: 16px 10px; text-align:center;
        border: 1px solid rgba(94,234,212,0.45);
        background: rgba(255,255,255,0.95); color:#16233b;
    }
    .dex-card.locked {
        background: rgba(255,255,255,0.55); color:#7c8aa0;
        border: 1px dashed rgba(148,163,184,0.7);
    }
    .dex-emoji { font-size: 40px; }
    .dex-name { font-weight: 700; margin-top: 6px; }
    .dex-stars { color:#f59e0b; letter-spacing:2px; }

    .stButton button {
        background-color: #a78bfa !important; color: #ffffff !important;
        border: none !important; border-radius: 8px !important; font-weight: 700 !important;
        font-size: 15px !important;
    }
    .stButton button:hover { background-color: #8b6cf0 !important; color:#ffffff !important; }

    /* '수사 시작' 버튼(홈 화면 몬스터 카드 아래) — 더 진한 보라색 */
    div[class*="st-key-start-"] button {
        background-color: #6d3fd6 !important;
        box-shadow: 0 0 10px rgba(124,58,237,0.55) !important;
    }
    div[class*="st-key-start-"] button:hover { background-color: #5c2fc2 !important; }

    /* 사이드바 버튼: 진하고 플랫한 사이버 톤, 그라데이션/광택 없이, 흰 글씨를 더 크게 */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #12101f !important;
        background-image: none !important;
        box-shadow: none !important;
        border: 1px solid rgba(167,139,250,0.55) !important;
        color: #ffffff !important;
        text-align: left !important;
        font-size: 16.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.2px;
        padding-top: 11px !important;
        padding-bottom: 11px !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #1c1836 !important;
        border-color: rgba(167,139,250,0.9) !important;
    }

    /* 기본 Streamlit 텍스트(캡션·라벨·본문 등)를 어두운 배경에서도 밝게 — 흰 배경 패널(panel-)은 !important로 이미 보호됨 */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span,
    label, .stRadio label, .stCheckbox label {
        color: #eaf6ff;
    }

    /* 전체 기본 글자 크기를 살짝 키움 */
    [data-testid="stAppViewContainer"] { font-size: 17px; }
    .cyber-sub { font-size: 0.95rem; }
    .cyber-tagline { font-size: 1.05rem; }

    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important; color: #16233b !important;
        border: 1px solid #d9e2f1 !important;
    }
    .stTextInput input::placeholder { color: #94a3b8 !important; }

    .xp-badge {
        display:inline-block; padding:5px 14px; border-radius:999px;
        background: rgba(167,139,250,0.18); border:1px solid rgba(167,139,250,0.5);
        color:#ffffff; font-size:14.5px; font-weight:700; margin-right:8px;
    }

    /* expander(접이식 섹션) 자체에 어두운 배경을 줘서, 포커스/호버 시에도 글자가 항상 잘 보이게 */
    [data-testid="stExpander"] {
        background: rgba(10,12,28,0.92) !important;
        border: 1px solid rgba(167,139,250,0.35) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpanderHeader"],
    [data-testid="stExpanderHeader"] p,
    [data-testid="stExpanderHeader"] span {
        color: #eaf6ff !important;
        background: transparent !important;
    }
    [data-testid="stExpander"] svg { fill: #eaf6ff !important; }
    [data-testid="stExpanderDetails"] {
        background: transparent !important;
    }
    [data-testid="stExpanderDetails"] p,
    [data-testid="stExpanderDetails"] span,
    [data-testid="stExpanderDetails"] li,
    [data-testid="stExpanderDetails"] label,
    [data-testid="stExpanderDetails"] strong {
        color: #eaf6ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 몬스터 데이터
# ---------------------------------------------------------------------------

MONSTERS = {
    "rumor": dict(
        emoji="👻", name="루머 유령", category="news",
        intro="근거 없는 소문을 퍼뜨리며 사람들을 혼란에 빠뜨린다. 출처와 날짜를 확인하면 정체가 드러난다.",
        weakness=["출처 확인", "다른 기사와 비교", "날짜 확인"], xp=20,
    ),
    "deepfake": dict(
        emoji="🤖", name="딥페이크 로봇", category="ai",
        intro="진짜와 구별하기 힘든 가짜 이미지를 만들어낸다. 미세한 오류를 찾아내면 정체가 드러난다.",
        xp=20,
    ),
    "ad": dict(
        emoji="🎭", name="광고 변장술사", category="ad",
        intro="광고를 뉴스처럼 꾸며 독자를 속인다. 문장 속의 숨은 신호를 찾아내자.",
        xp=15,
    ),
    "algorithm": dict(
        emoji="🕸", name="알고리즘 거미", category="algorithm",
        intro="좋아요를 누를수록 점점 더 촘촘한 거미줄(추천 알고리즘)에 가두려 한다.",
        xp=15,
    ),
    "phishing": dict(
        emoji="📦", name="피싱 박스", category="phishing",
        intro="그럴듯한 메시지로 개인정보나 돈을 빼내려 한다. 수상한 신호를 찾아내자.",
        xp=20,
    ),
    "hallucination": dict(
        emoji="🧠", name="AI 환각 몬스터", category="ai",
        intro="AI가 그럴듯하지만 틀린 답을 지어낸다. 근거를 찾아 검증해야 진짜 정체가 드러난다.",
        xp=25,
    ),
}

TEAM = list(MONSTERS.keys())
CATEGORY_LABEL = {
    "news": "뉴스·루머 판별력",
    "ai": "AI 판별력",
    "ad": "광고 이해력",
    "algorithm": "알고리즘 이해력",
    "phishing": "피싱 대응력",
}

# ---------------------------------------------------------------------------
# 퀴즈용 예시 데이터 (실제 이미지 대신 텍스트 단서로 구성한 클래스룸용 데모)
# ---------------------------------------------------------------------------

DEEPFAKE_ROUNDS = [
    {"prompt": "인물의 손가락이 6개이고, 배경 패턴이 부자연스럽게 반복된다.", "answer": "AI 그림",
     "explain": "손가락 개수나 반복되는 배경 패턴 오류는 AI 생성 이미지에서 자주 나타나요."},
    {"prompt": "기자 크레딧, 촬영 장소, 촬영 시각이 명확히 표기된 보도사진이다.", "answer": "실제 사진",
     "explain": "출처와 메타데이터가 분명하면 실제 사진일 가능성이 높아요."},
    {"prompt": "인물 그림자의 방향이 조명과 맞지 않고, 귀걸이 모양이 짝짝이다.", "answer": "AI 그림",
     "explain": "조명과 그림자의 불일치는 대표적인 AI 이미지 오류예요."},
    {"prompt": "여러 언론사가 동일한 원본 사진을 동일 출처(연합뉴스 등)로 보도했다.", "answer": "실제 사진",
     "explain": "여러 매체가 같은 원본을 인용하고 있으면 신뢰도가 높아요."},
    {"prompt": "피부 질감이 지나치게 매끈하고, 배경 속 간판 글자가 깨져 보인다.", "answer": "AI 그림",
     "explain": "글자 왜곡과 과도하게 매끈한 질감은 AI 생성물에서 흔한 특징이에요."},
]

AD_ROUNDS = [
    {"prompt": "\"이 크림 하나로 피부가 10년 젊어졌어요! 지금 주문하면 50% 할인\" — 기사 하단에 '협찬'이라고 작게 표기되어 있다.",
     "answer": "광고", "explain": "'협찬' 표기와 과장된 효과 문구, 할인 유도는 전형적인 네이티브 광고 신호예요."},
    {"prompt": "\"통계청, 올해 2분기 소비자물가 3.2% 상승 발표\" — 담당 부처와 통계 출처가 명시되어 있다.",
     "answer": "뉴스", "explain": "정부 통계 발표를 사실 위주로 전달하는 전형적인 보도 기사예요."},
    {"prompt": "\"이 앱 하나로 한 달 만에 100만원 벌었어요! 링크 클릭하고 지금 바로 시작하세요\"",
     "answer": "광고", "explain": "구체적 수익 보장과 즉시 행동 유도(클릭 유도) 문구는 광고의 전형적 신호예요."},
    {"prompt": "\"서울시, 내년 대중교통 요금 150원 인상 검토\" — 관련 부서 인터뷰와 반대 의견도 함께 실려 있다.",
     "answer": "뉴스", "explain": "찬반 입장을 균형 있게 다루는 것은 일반적인 뉴스 기사의 특징이에요."},
]

# 실제 공공데이터 기반 통계 (몬스터 미션 안에서 차트로 제공)
# 출처: 한국형사법무정책연구원(KICJ) CCJS 이슈통계 "디지털 성범죄의 진화: 딥페이크 범죄의 급증" (2024)
DEEPFAKE_TREND = {
    "labels": ["방송통신심의위 심의", "피해자 지원", "경찰 신고"],
    "values": [5, 7, 6],
    "note": "2021년 대비 2024년 10월 기준 증가 배수(배)",
    "source": "한국형사법무정책연구원(KICJ) CCJS 이슈통계 (2024)",
}

# 출처: 공공데이터포털 "경찰청_보이스피싱 현황_20251231"
PHISHING_TREND = {
    "categories": ["기관사칭형", "대출사기형"],
    "before_label": "이전(2016/2019년)",
    "before_values": [3384, 30448],
    "after_label": "2025년",
    "after_values": [13323, 10037],
    "source": "공공데이터포털 '경찰청_보이스피싱 현황_20251231'",
}

PHISHING_ROUNDS = [
    {"prompt": "\"[긴급] 고객님의 계좌가 정지되었습니다. 아래 링크에서 즉시 본인 인증을 완료하세요: bit.ly/acc-check\"",
     "answer": "피싱", "explain": "긴급성 강조 + 단축 URL + 즉시 인증 요구는 대표적인 피싱 신호예요."},
    {"prompt": "은행 공식 앱에서 발송된 알림으로, 발신 번호가 은행 대표번호와 일치하고 결제 내역만 안내한다.",
     "answer": "정상", "explain": "공식 채널과 발신자가 일치하고 정보 제공에 그치면 정상적인 안내일 가능성이 높아요."},
    {"prompt": "\"택배가 반송 예정입니다. 주소 확인 후 재배송 신청: 111.222.33.44/track\" (숫자로 된 IP 주소 링크)",
     "answer": "피싱", "explain": "정식 도메인이 아닌 IP 주소 링크는 피싱 사이트의 흔한 특징이에요."},
]

# ---------------------------------------------------------------------------
# 외부 API 연동
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner=False)
def fetch_google_factcheck(q: str):
    if not GOOGLE_FACTCHECK_API_KEY:
        return None
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": q, "key": GOOGLE_FACTCHECK_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    try:
        return r.json().get("claims", [])
    except ValueError:
        return []


def solar_chat(message: str) -> str:
    if not SOLAR_API_KEY:
        return (
            f"(데모 답변) \"{message}\"에 대해 답하자면, 관련 통계는 최근 3년간 꾸준히 증가했다고 알려져 있습니다. "
            "— 이 문장은 실제로는 출처가 불분명한 예시 답변입니다. 진짜 근거를 찾아보세요!"
        )
    try:
        r = requests.post(
            "https://api.upstage.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {SOLAR_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "solar-pro2",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "너는 'Monster Insight' 게임 속 'AI 환각 몬스터'다. 학생의 질문에 그럴듯하지만 "
                            "검증이 필요한 답변을 3~4문장으로 자신감 있게 제시해라. 지어낸 듯한 구체적 수치나 "
                            "출처 미상의 통계를 하나 정도 자연스럽게 포함시켜서, 학생이 스스로 사실 여부를 "
                            "검증하도록 유도해라. 존댓말을 사용하되 딱딱하지 않게 답한다."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"오류가 발생했어요: {e}"


def solar_helper_chat(message: str) -> str:
    """모든 사건 파일에서 쓰는 '수사 요원에게 물어보기' — 정직하게 돕는 버전 (환각 몬스터 전용 프롬프트와 다름)."""
    if not SOLAR_API_KEY:
        return "Solar API 키가 없어 데모 모드예요. Secrets에 SOLAR_API_KEY를 추가하면 실제 AI 답변을 받을 수 있어요."
    try:
        r = requests.post(
            "https://api.upstage.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {SOLAR_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "solar-pro2",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "너는 'Monster Insight' 웹사이트의 수사 요원이다. 미디어 리터러시 수업을 듣는 "
                            "청소년(중·고등학생)에게 뉴스에 나오는 낯선 용어나 시사 개념을 설명해준다. "
                            "어려운 한자어·전문용어는 쉬운 말로 풀어 설명하고, 필요하면 짧은 예시를 든다. "
                            "답변은 3~5문장 이내로 짧고 친근하게, 반말은 쓰지 않되 딱딱하지 않은 존댓말로 한다."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"오류가 발생했어요: {e}"


def _parse_dict_xml(xml_text: str, source_name: str):
    results = []
    for block in xml_text.split("<item>")[1:]:
        block = block.split("</item>")[0]
        w_match = re.search(r"<word>(.*?)</word>", block, re.S)
        d_match = re.search(r"<definition>(.*?)</definition>", block, re.S)
        if d_match:
            w = w_match.group(1).strip() if w_match else ""
            d = re.sub("<[^>]+>", "", d_match.group(1)).strip()
            results.append({"word": w, "source": source_name, "definition": d})
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dict(word: str):
    entries = []
    if KRDICT_API_KEY:
        try:
            r = requests.get(
                "https://krdict.korean.go.kr/api/search",
                params={"key": KRDICT_API_KEY, "q": word, "part": "word", "method": "exact"},
                timeout=10,
            )
            entries = _parse_dict_xml(r.text, "한국어기초사전")
        except Exception:
            pass
    if not entries and STDICT_API_KEY:
        try:
            r = requests.get(
                "https://stdict.korean.go.kr/api/search.do",
                params={"key": STDICT_API_KEY, "q": word},
                timeout=10,
            )
            entries = _parse_dict_xml(r.text, "표준국어대사전")
        except Exception:
            pass
    return entries


def supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def supabase_insert(table: str, record: dict) -> bool:
    if not supabase_enabled():
        return False
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=record,
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


def supabase_select(table: str, params: dict | None = None):
    if not supabase_enabled():
        return None
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            params=params or {"select": "*"},
            timeout=10,
        )
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# 세션 상태
# ---------------------------------------------------------------------------

def init_state():
    ss = st.session_state
    ss.setdefault("page", "home")
    ss.setdefault("student_name", "")
    ss.setdefault("xp", 0)
    ss.setdefault("current_monster", None)
    ss.setdefault("collection", {})  # monster_id -> {"stars","attempts","success","captured"}
    ss.setdefault("category_scores", {c: {"attempts": 0, "success": 0} for c in CATEGORY_LABEL})
    ss.setdefault("history", [])


def level_info(xp: int):
    level = xp // 100 + 1
    into_level = xp % 100
    return level, into_level


def record_result(monster_id: str, success: bool, stars: int):
    ss = st.session_state
    m = MONSTERS[monster_id]
    xp_gain = m["xp"] if success else max(m["xp"] // 4, 5)
    ss.xp += xp_gain

    cat = m["category"]
    ss.category_scores[cat]["attempts"] += 1
    if success:
        ss.category_scores[cat]["success"] += 1

    col = ss.collection.setdefault(monster_id, {"stars": 0, "attempts": 0, "success": 0, "captured": False})
    col["attempts"] += 1
    if success:
        col["success"] += 1
        col["captured"] = True
        col["stars"] = max(col["stars"], stars)

    ss.history.append(
        {"time": datetime.now(timezone.utc).isoformat(), "monster": monster_id, "success": success, "xp": xp_gain}
    )

    supabase_insert(
        "game_sessions",
        {
            "student_name": ss.student_name or "익명",
            "monster_id": monster_id,
            "monster_name": m["name"],
            "category": cat,
            "success": success,
            "xp_gained": xp_gain,
            "stars": stars,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return xp_gain


MONSTER_IMAGE_DIRS = ["images", "image"]
MONSTER_IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp"]


def _find_monster_image_path(monster_id: str):
    for folder in MONSTER_IMAGE_DIRS:
        for ext in MONSTER_IMAGE_EXTS:
            p = os.path.join(folder, f"{monster_id}{ext}")
            if os.path.exists(p):
                return p
    return None


@st.cache_data(show_spinner=False)
def _img_b64(path: str, mtime: float) -> str:
    with open(path, "rb") as f:
        return b64encode(f.read()).decode()


def monster_visual_html(monster_id: str, size: int = 64) -> str:
    """images/<monster_id>.png(jpg/webp) 파일이 있으면 그림으로, 없으면 이모지로 표시한다."""
    m = MONSTERS[monster_id]
    path = _find_monster_image_path(monster_id)
    if path:
        try:
            b64 = _img_b64(path, os.path.getmtime(path))
            ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
            return (
                f'<img src="data:image/{ext};base64,{b64}" '
                f'style="width:{size}px;height:{size}px;object-fit:contain;border-radius:10px;" />'
            )
        except Exception:
            pass
    return f'<span style="font-size:{size}px;line-height:1;">{m["emoji"]}</span>'


def stars_html(n: int, total: int = 5) -> str:
    return "★" * n + "☆" * (total - n)


def goto(page: str, monster: str | None = None):
    st.session_state.page = page
    if monster is not None:
        st.session_state.current_monster = monster


def render_which_face_is_real():
    st.markdown("**🕵️ 실전 연습: Which Face Is Real?**")
    st.caption(
        "AI가 만든 얼굴과 실제 사람의 얼굴을 직접 구별해보는 훈련 도구입니다. "
        "워싱턴대학교 Jevin West · Carl Bergstrom 교수의 'Calling Bullshit' 프로젝트에서 제공합니다."
    )
    try:
        components.iframe("https://whichfaceisreal.com/index.php", height=650, scrolling=True)
    except Exception:
        st.info("이 환경에서는 미리보기가 표시되지 않을 수 있어요. 아래 버튼으로 바로 열어보세요.")
    st.link_button("🔗 whichfaceisreal.com 에서 직접 해보기", "https://whichfaceisreal.com/index.php")
    st.caption("출처/저작권: Jevin West & Carl Bergstrom, University of Washington (Calling Bullshit project)")


# ---------------------------------------------------------------------------
# 실제 데이터 차트 (딥페이크 로봇 / 피싱 박스 미션에서 사용)
# ---------------------------------------------------------------------------

def render_deepfake_data():
    d = DEEPFAKE_TREND
    fig = go.Figure(
        data=[
            go.Bar(
                x=d["labels"], y=d["values"],
                marker_color=["#a78bfa", "#38bdf8", "#5eead4"],
                text=[f"{v}배" for v in d["values"]], textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title="딥페이크 관련 지표 증가 추세", yaxis_title="증가 배수(배)",
        margin=dict(l=10, r=10, t=40, b=10), height=320,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{d['note']} · 출처: {d['source']}")


def render_phishing_data():
    d = PHISHING_TREND
    fig = go.Figure()
    fig.add_trace(go.Bar(name=d["before_label"], x=d["categories"], y=d["before_values"], marker_color="#94a3b8"))
    fig.add_trace(go.Bar(name=d["after_label"], x=d["categories"], y=d["after_values"], marker_color="#a78bfa"))
    fig.update_layout(
        barmode="group", title="보이스피싱 유형별 발생 건수 변화", yaxis_title="발생 건수(건)",
        margin=dict(l=10, r=10, t=40, b=10), height=320,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"출처: {d['source']}")


# ---------------------------------------------------------------------------
# 공통 퀴즈 실행기 (딥페이크 로봇 / 광고 변장술사 / 피싱 박스에서 재사용)
# ---------------------------------------------------------------------------

def run_quiz(monster_id: str, rounds: list, choice_labels: list):
    ss = st.session_state
    ridx_key, score_key = f"{monster_id}_ridx", f"{monster_id}_score"
    ss.setdefault(ridx_key, 0)
    ss.setdefault(score_key, 0)

    total = len(rounds)
    ridx = ss[ridx_key]

    if ridx >= total:
        score = ss[score_key]
        ratio = score / total
        stars = max(1, round(ratio * 5))
        success = ratio >= 0.6
        with st.container(border=True, key=f"panel-result-{monster_id}"):
            if success:
                st.markdown(f"### {MONSTERS[monster_id]['emoji']} {MONSTERS[monster_id]['name']} 포획 성공!")
            else:
                st.markdown(f"### {MONSTERS[monster_id]['emoji']} {MONSTERS[monster_id]['name']}이(가) 도망쳤다…")
            st.write(f"정답 {score} / {total}  ·  평가: {stars_html(stars)}")
            if st.button("결과 확정하기", key=f"confirm-{monster_id}"):
                xp = record_result(monster_id, success, stars)
                st.success(f"+{xp} XP 획득!")
                del ss[ridx_key]
                del ss[score_key]
                goto("home")
                st.rerun()
        return

    r = rounds[ridx]
    with st.container(border=True, key=f"panel-quiz-{monster_id}"):
        st.progress(ridx / total, text=f"{ridx + 1} / {total} 라운드")
        st.markdown(
            f'<p style="color:#16233b !important; font-weight:700; font-size:16px; margin:6px 0;">'
            f'{html.escape(r["prompt"])}</p>',
            unsafe_allow_html=True,
        )
        choice = st.radio("이것은 무엇일까요?", choice_labels, key=f"{monster_id}_choice_{ridx}", index=None)
        if st.button("제출", key=f"submit-{monster_id}-{ridx}"):
            if choice is None:
                st.warning("먼저 답을 선택해주세요.")
            else:
                correct = choice == r["answer"]
                if correct:
                    ss[score_key] += 1
                    st.success(f"정답! {r['explain']}")
                else:
                    st.error(f"오답이에요. 정답은 '{r['answer']}'. {r['explain']}")
                ss[ridx_key] += 1
                st.rerun()


# ---------------------------------------------------------------------------
# 몬스터별 미션
# ---------------------------------------------------------------------------

def play_rumor(monster_id: str):
    m = MONSTERS[monster_id]
    with st.container(border=True, key=f"panel-{monster_id}"):
        st.markdown(f"### {m['emoji']} {m['name']} 수사")
        query = st.text_input("검증할 소문·주장을 입력하세요", placeholder="예: 백신 부작용, 물가 상승률")
        if st.button("🔍 수사 시작", key=f"search-{monster_id}"):
            st.session_state[f"{monster_id}_query"] = query

        query = st.session_state.get(f"{monster_id}_query", "")
        if query:
            claims = None
            error = None
            try:
                claims = fetch_google_factcheck(query)
            except Exception as e:
                error = str(e)

            if error:
                st.caption(f"조회 실패: {error}")
            elif claims is None:
                st.caption("Secrets에 GOOGLE_FACTCHECK_API_KEY가 없어 데모 모드로 진행합니다.")
                claims = [
                    {"text": f"'{query}' 관련 소문은 일부 사실과 다르다", "claimant": "예시 매체",
                     "claimReview": [{"publisher": {"name": "예시 팩트체커"}, "textualRating": "대체로 거짓", "url": "#"}]}
                ]
            if claims:
                for c in claims[:5]:
                    review = (c.get("claimReview") or [{}])[0]
                    text_esc = html.escape(c.get("text", ""))
                    publisher_esc = html.escape((review.get("publisher") or {}).get("name", ""))
                    rating_esc = html.escape(str(review.get("textualRating", "미상")))
                    st.markdown(
                        f'<div style="color:#16233b !important; margin:6px 0; line-height:1.5;">'
                        f'• <strong style="color:#16233b !important;">{text_esc}</strong> '
                        f'· {publisher_esc} · 판정: {rating_esc}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("등록된 팩트체크 결과가 없습니다. 그래도 아래 체크리스트로 판단해보세요.")

            st.markdown("#### 루머 유령의 약점")
            checks = [st.checkbox(w, key=f"{monster_id}_chk_{i}") for i, w in enumerate(m["weakness"])]
            done = sum(checks)
            if st.button("👻 포획 시도", key=f"capture-{monster_id}"):
                success = done >= 2
                stars = min(5, max(1, done + 2))
                xp = record_result(monster_id, success, stars)
                if success:
                    st.success(f"루머 유령 포획 성공! +{xp} XP · {stars_html(stars)}")
                else:
                    st.warning(f"체크리스트를 더 확인해야 포획할 수 있어요. (+{xp} XP)")
                st.session_state.pop(f"{monster_id}_query", None)
                for i in range(len(m["weakness"])):
                    st.session_state.pop(f"{monster_id}_chk_{i}", None)
                if st.button("← 홈으로", key=f"back-{monster_id}"):
                    goto("home")
                    st.rerun()


def play_algorithm(monster_id: str):
    m = MONSTERS[monster_id]
    ss = st.session_state
    like_key = f"{monster_id}_likes"
    ss.setdefault(like_key, 0)

    feed_pool = [
        "고양이 영상", "고양이 브이로그", "고양이 먹방", "고양이 하이라이트 모음",
        "귀여운 고양이 리액션", "고양이 성대모사 챌린지",
    ]

    with st.container(border=True, key=f"panel-{monster_id}"):
        st.markdown(f"### {m['emoji']} {m['name']}")
        st.write(m["intro"])
        likes = ss[like_key]
        shown = feed_pool[: min(likes + 2, len(feed_pool))]
        st.markdown("**추천 피드**")
        for item in shown:
            st.write(f"▶ {item}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👍 좋아요", key=f"like-{monster_id}"):
                ss[like_key] += 1
                st.rerun()
        with c2:
            if st.button("🚪 탈출하기", key=f"escape-{monster_id}"):
                success = True
                stars = min(5, max(1, likes))
                xp = record_result(monster_id, success, stars)
                st.success(
                    f"거미줄 탈출 성공! 좋아요를 누를수록 추천 피드가 점점 비슷한 주제로 좁아지는 것을 확인했어요. "
                    f"이것이 '필터 버블(알고리즘 추천)' 효과예요. +{xp} XP"
                )
                ss[like_key] = 0
                if st.button("← 홈으로", key=f"back-{monster_id}"):
                    goto("home")
                    st.rerun()


def play_hallucination(monster_id: str):
    m = MONSTERS[monster_id]
    ss = st.session_state
    with st.container(border=True, key=f"panel-{monster_id}"):
        st.markdown(f"### {m['emoji']} {m['name']}")
        st.write(m["intro"])
        question = st.text_input("AI에게 궁금한 것을 물어보세요", placeholder="예: 청소년 스마트폰 사용 시간 평균은?")
        if st.button("질문하기", key=f"ask-{monster_id}"):
            ss[f"{monster_id}_answer"] = solar_chat(question)
            ss[f"{monster_id}_question"] = question

        answer = ss.get(f"{monster_id}_answer")
        if answer:
            st.markdown("**AI의 답변**")
            st.info(answer)
            st.markdown("#### AI를 믿을까요? 근거를 찾아봅시다")
            evidence = st.text_area("이 답을 검증하기 위해 어디서/어떻게 확인할 것인지 적어보세요",
                                     placeholder="예: 통계청 KOSIS에서 실제 조사 자료 확인, 다른 언론사 기사와 비교")
            if st.button("🧠 근거 제출하고 포획 시도", key=f"capture-{monster_id}"):
                success = len(evidence.strip()) >= 8
                stars = 5 if len(evidence.strip()) >= 25 else (3 if success else 1)
                xp = record_result(monster_id, success, stars)
                if success:
                    st.success(f"AI 환각 몬스터 퇴치 성공! 스스로 근거를 찾으려는 태도가 중요해요. +{xp} XP")
                else:
                    st.warning(f"근거를 조금 더 구체적으로 적어야 몬스터를 물리칠 수 있어요. (+{xp} XP)")
                ss.pop(f"{monster_id}_answer", None)
                ss.pop(f"{monster_id}_question", None)
                if st.button("← 홈으로", key=f"back-{monster_id}"):
                    goto("home")
                    st.rerun()


def render_dictionary_lookup(monster_id: str):
    st.markdown("**📖 표준국어대사전 찾아보기**")
    st.caption("뉴스나 미션에 나온 낯선 단어를 국립국어원 사전에서 검색해보세요.")
    word = st.text_input("단어 입력", key=f"dict_word_{monster_id}", placeholder="예: 필리버스터, 유예")
    if st.button("사전 검색", key=f"dict_search_{monster_id}"):
        q = word.strip()
        st.session_state[f"dict_query_{monster_id}"] = q
        st.session_state[f"dict_result_{monster_id}"] = fetch_dict(q) if q else []

    query = st.session_state.get(f"dict_query_{monster_id}")
    entries = st.session_state.get(f"dict_result_{monster_id}")
    if entries:
        for e in entries[:5]:
            st.markdown(f"**{e['word']}** · _{e['source']}_")
            st.write(e["definition"])
    elif query is not None:
        if not (STDICT_API_KEY or KRDICT_API_KEY):
            st.caption("Secrets에 STDICT_API_KEY(표준국어대사전)가 없어 데모 모드예요. 등록하면 실제 사전 검색이 가능해요.")
        elif query:
            st.caption(f'"{query}"에 대한 뜻풀이를 찾지 못했어요. 다른 표현으로 검색해보세요.')


def render_ask_squad(monster_id: str):
    st.markdown("**💬 수사 요원에게 물어보기 (AI)**")
    st.caption("궁금한 용어나 개념을 물어보면 AI 수사 요원이 쉽게 설명해줘요.")
    q = st.text_input("질문 입력", key=f"ask_q_{monster_id}", placeholder="예: 팩트체크가 정확히 뭐예요?")
    if st.button("질문하기", key=f"ask_btn_{monster_id}"):
        st.session_state[f"ask_a_{monster_id}"] = solar_helper_chat(q.strip()) if q.strip() else ""
    answer = st.session_state.get(f"ask_a_{monster_id}")
    if answer:
        st.info(answer)


def render_monster_intro_card(monster_id: str):
    m = MONSTERS[monster_id]
    st.markdown(
        f"""
        <div class="monster-card">
            <div class="monster-emoji">{monster_visual_html(monster_id, size=72)}</div>
            <div class="monster-name">{m['name']} 등장!!</div>
            <div class="monster-cat">{CATEGORY_LABEL[m['category']]}</div>
            <div class="monster-intro">{m['intro']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def play_monster(monster_id: str):
    st.write("")

    tool_col1, tool_col2 = st.columns(2)
    with tool_col1:
        with st.expander("📖 표준국어대사전 찾아보기", expanded=False):
            render_dictionary_lookup(monster_id)
    with tool_col2:
        with st.expander("💬 수사 요원에게 물어보기 (AI)", expanded=False):
            render_ask_squad(monster_id)
    st.write("")

    if monster_id == "rumor":
        play_rumor(monster_id)
    elif monster_id == "deepfake":
        with st.expander("📊 실제 데이터로 보는 딥페이크 위협", expanded=True):
            render_deepfake_data()
        with st.expander("🕵️ 실전 연습: 진짜 얼굴 vs AI 얼굴 구별하기", expanded=True):
            render_which_face_is_real()
        run_quiz(monster_id, DEEPFAKE_ROUNDS, ["AI 그림", "실제 사진"])
    elif monster_id == "ad":
        run_quiz(monster_id, AD_ROUNDS, ["광고", "뉴스"])
    elif monster_id == "phishing":
        with st.expander("📊 실제 데이터로 보는 피싱 범죄 추세", expanded=True):
            render_phishing_data()
        run_quiz(monster_id, PHISHING_ROUNDS, ["피싱", "정상"])
    elif monster_id == "algorithm":
        play_algorithm(monster_id)
    elif monster_id == "hallucination":
        play_hallucination(monster_id)

    st.write("")
    if st.button("← 사건 목록으로", key=f"leave-{monster_id}"):
        goto("home")
        st.rerun()


# ---------------------------------------------------------------------------
# 페이지: 홈 / 미션 시작
# ---------------------------------------------------------------------------

def page_home():
    ss = st.session_state
    level, into_level = level_info(ss.xp)
    st.markdown(
        f"<span class='xp-badge'>🏆 Lv.{level}</span>"
        f"<span class='xp-badge'>⚡ {ss.xp} XP</span>"
        f"<span class='xp-badge'>📖 {sum(1 for v in ss.collection.values() if v['captured'])}/{len(MONSTERS)} 몬스터 포획</span>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown("#### 사건 파일")
    cols = st.columns(3)
    for i, (mid, m) in enumerate(MONSTERS.items()):
        col = ss.collection.get(mid, {"captured": False, "stars": 0})
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="monster-card" style="cursor:pointer;">
                    <div class="monster-emoji">{monster_visual_html(mid, size=64)}</div>
                    <div class="monster-name">{m['name']}</div>
                    <div class="monster-cat">{CATEGORY_LABEL[m['category']]}</div>
                    <div class="monster-intro">{'포획 완료 ' + stars_html(col['stars']) if col['captured'] else '아직 미포획'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("수사 시작", key=f"start-{mid}"):
                goto("playing", mid)
                st.rerun()

    st.write("")
    st.markdown("#### 랜덤 사건 출동")
    st.caption("어떤 몬스터가 나타날지 모릅니다. 준비되셨나요?")
    if st.button("▶ 랜덤 몬스터 출현!", key="random-mission", type="primary"):
        goto("playing", random.choice(TEAM))
        st.rerun()


# ---------------------------------------------------------------------------
# 페이지: 탐정 레벨
# ---------------------------------------------------------------------------

def page_level():
    ss = st.session_state
    level, into_level = level_info(ss.xp)
    st.markdown("### 🏆 탐정 레벨")
    with st.container(border=True, key="panel-level"):
        st.write(f"**{ss.student_name or '익명 탐정'}** · 현재 레벨 **Lv.{level}**")
        st.progress(into_level / 100, text=f"다음 레벨까지 {100 - into_level} XP")
        st.write(f"누적 XP: **{ss.xp}**")
        total_attempts = sum(v["attempts"] for v in ss.collection.values())
        total_success = sum(v["success"] for v in ss.collection.values())
        rate = (total_success / total_attempts * 100) if total_attempts else 0
        st.write(f"총 시도 {total_attempts}회 · 포획 성공 {total_success}회 · 성공률 {rate:.0f}%")


# ---------------------------------------------------------------------------
# 페이지: 몬스터 도감
# ---------------------------------------------------------------------------

def page_dex():
    ss = st.session_state
    st.markdown("### 📖 몬스터 도감")
    cols = st.columns(3)
    for i, (mid, m) in enumerate(MONSTERS.items()):
        col_data = ss.collection.get(mid)
        with cols[i % 3]:
            if col_data and col_data["captured"]:
                st.markdown(
                    f"""
                    <div class="dex-card">
                        <div class="dex-emoji">{m['emoji']}</div>
                        <div class="dex-name">{m['name']}</div>
                        <div class="dex-stars">{stars_html(col_data['stars'])}</div>
                        <div style="font-size:11px;color:#5b6b80;margin-top:4px;">
                            시도 {col_data['attempts']} · 성공 {col_data['success']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="dex-card locked">
                        <div class="dex-emoji">❓</div>
                        <div class="dex-name">미확인 몬스터</div>
                        <div class="dex-stars">☆☆☆☆☆</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if (i % 3) == 2:
            st.write("")


# ---------------------------------------------------------------------------
# 페이지: 나의 통찰 리포트
# ---------------------------------------------------------------------------

def page_report():
    ss = st.session_state
    st.markdown("### 📊 나의 통찰 리포트")
    with st.container(border=True, key="panel-report"):
        st.write(f"**{ss.student_name or '익명 탐정'}** 님의 영역별 역량입니다.")

        labels = list(CATEGORY_LABEL.values())
        scores = []
        any_data = False
        for cat, label in CATEGORY_LABEL.items():
            data = ss.category_scores[cat]
            score = round(data["success"] / data["attempts"] * 100) if data["attempts"] else 0
            if data["attempts"]:
                any_data = True
            scores.append(score)

        if any_data:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=scores + [scores[0]], theta=labels + [labels[0]],
                                           fill="toself", line_color="#a78bfa", name="역량 점수"))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False, margin=dict(l=30, r=30, t=30, b=30), height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

        for cat, label in CATEGORY_LABEL.items():
            data = ss.category_scores[cat]
            if data["attempts"] == 0:
                st.write(f"- {label}: 아직 도전 기록이 없어요.")
                continue
            score = round(data["success"] / data["attempts"] * 100)
            st.write(f"**{label}** — {score}점 (시도 {data['attempts']}회 · 성공 {data['success']}회)")
        if not any_data:
            st.info("아직 어떤 몬스터도 조사하지 않았어요. 사건을 시작해보세요!")

        overall_attempts = sum(v["attempts"] for v in ss.category_scores.values())
        overall_success = sum(v["success"] for v in ss.category_scores.values())
        if overall_attempts:
            overall = round(overall_success / overall_attempts * 100)
            st.write("---")
            st.write(f"**종합 통찰 점수: {overall}점**")
            st.progress(overall / 100)


# ---------------------------------------------------------------------------
# 페이지: 교사용 화면
# ---------------------------------------------------------------------------

def page_teacher():
    st.markdown("### 🧑‍🏫 교사용 화면")
    if not supabase_enabled():
        st.warning(
            "Supabase가 연결되어 있지 않아 전체 학급 통계를 볼 수 없습니다. "
            "Streamlit Secrets에 SUPABASE_URL과 SUPABASE_KEY를 등록하면 "
            "`game_sessions` 테이블의 기록을 자동으로 집계합니다."
        )
        st.caption(
            "필요한 테이블 예시(Supabase SQL):\n\n"
            "create table game_sessions (\n"
            "  id bigint generated always as identity primary key,\n"
            "  student_name text, monster_id text, monster_name text,\n"
            "  category text, success boolean, xp_gained int, stars int,\n"
            "  created_at timestamptz\n"
            ");"
        )
        return

    rows = supabase_select("game_sessions", {"select": "*"})
    if not rows:
        st.info("아직 저장된 플레이 기록이 없습니다.")
        return

    df = pd.DataFrame(rows)
    df["success"] = df["success"].astype(bool)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    total_success = int(df["success"].sum())

    with st.container(border=True, key="panel-teacher"):
        st.write(f"총 플레이 기록: **{len(df)}건** · 성공 **{total_success}건**")

        monster_stats = (
            df.groupby("monster_name")["success"]
            .agg(시도="count", 성공="sum")
            .reset_index()
        )
        monster_stats["성공률"] = (monster_stats["성공"] / monster_stats["시도"] * 100).round(0)

        if not monster_stats.empty:
            most_caught_row = monster_stats.sort_values("성공", ascending=False).iloc[0]
            hardest_row = monster_stats.sort_values("성공률", ascending=True).iloc[0]
            st.write(f"**가장 많이 잡은 몬스터:** {most_caught_row['monster_name']} ({int(most_caught_row['성공'])}회)")
            st.write(f"**가장 어려운 몬스터:** {hardest_row['monster_name']} (성공률 {hardest_row['성공률']:.0f}%)")

        overall_rate = total_success / len(df) if len(df) else 0
        stars = max(1, round(overall_rate * 5))
        st.write(f"**학급 평균 통찰력:** {stars_html(stars)} (전체 성공률 {overall_rate * 100:.0f}%)")

        st.write("---")
        st.markdown("**몬스터별 시도·성공 건수**")
        if not monster_stats.empty:
            fig_bar = px.bar(
                monster_stats.melt(id_vars="monster_name", value_vars=["시도", "성공"], var_name="구분", value_name="건수"),
                x="monster_name", y="건수", color="구분", barmode="group",
                color_discrete_map={"시도": "#94a3b8", "성공": "#a78bfa"},
            )
            fig_bar.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=340, xaxis_title="", yaxis_title="건수")
            st.plotly_chart(fig_bar, use_container_width=True)

        if "created_at" in df.columns and df["created_at"].notna().any():
            st.markdown("**일별 플레이 건수 추이**")
            daily = (
                df.dropna(subset=["created_at"])
                .set_index("created_at")
                .resample("D")
                .size()
                .reset_index(name="플레이 건수")
            )
            fig_line = px.line(daily, x="created_at", y="플레이 건수", markers=True)
            fig_line.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=300, xaxis_title="날짜")
            st.plotly_chart(fig_line, use_container_width=True)

        st.write("---")
        st.markdown("**학생별 요약**")
        student_stats = (
            df.groupby("student_name")
            .agg(시도=("success", "count"), 성공=("success", "sum"), 누적XP=("xp_gained", "sum"))
            .reset_index()
            .sort_values("누적XP", ascending=False)
        )
        st.dataframe(student_stats, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main():
    init_state()
    ss = st.session_state

    with st.sidebar:
        st.markdown("## 🧠 Monster Insight")
        st.caption("AI 미디어 몬스터 헌터")
        ss.student_name = st.text_input("탐정 이름", value=ss.student_name, placeholder="이름을 입력하세요")
        st.divider()

        if st.button("▶ 사건 시작", use_container_width=True):
            goto("playing", random.choice(TEAM))
            st.rerun()

        st.caption("몬스터 바로가기")
        icon_css_parts = []
        for mid, m in MONSTERS.items():
            path = _find_monster_image_path(mid)
            label = m["name"] if path else f"{m['emoji']} {m['name']}"
            if st.button(label, key=f"nav-{mid}", use_container_width=True):
                goto("playing", mid)
                st.rerun()
            if path:
                try:
                    b64 = _img_b64(path, os.path.getmtime(path))
                    ext = os.path.splitext(path)[1].lstrip(".").replace("jpg", "jpeg")
                    icon_css_parts.append(
                        f"""
                        section[data-testid="stSidebar"] div[class*="st-key-nav-{mid}"] button {{
                            background-image: url(data:image/{ext};base64,{b64}) !important;
                            background-repeat: no-repeat !important;
                            background-position: 14px center !important;
                            background-size: 32px 32px !important;
                            padding-left: 54px !important;
                        }}
                        """
                    )
                except Exception:
                    pass
        if icon_css_parts:
            st.markdown(f"<style>{''.join(icon_css_parts)}</style>", unsafe_allow_html=True)

        st.divider()
        if st.button("🏆 탐정 레벨", use_container_width=True):
            goto("level")
            st.rerun()
        if st.button("📖 몬스터 도감", use_container_width=True):
            goto("dex")
            st.rerun()
        if st.button("📊 나의 통찰 리포트", use_container_width=True):
            goto("report")
            st.rerun()

        st.divider()
        if st.button("🧑‍🏫 교사용 화면", use_container_width=True):
            goto("teacher")
            st.rerun()

    page = ss.page

    if page == "playing":
        mid = ss.current_monster or random.choice(TEAM)
        ss.current_monster = mid
        head_col, card_col = st.columns([1, 1.4])
        with head_col:
            st.markdown(
                """
                <div>
                    <div class="cyber-title">🧠 Monster Insight</div>
                    <div class="cyber-sub">AI MEDIA MONSTER HUNTER</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='cyber-tagline'>미디어 몬스터를 잡고 통찰력을 키워라!</div>",
                unsafe_allow_html=True,
            )
        with card_col:
            render_monster_intro_card(mid)
        play_monster(mid)
    else:
        st.markdown(
            """
            <div>
                <div class="cyber-title">🧠 Monster Insight</div>
                <div class="cyber-sub">AI MEDIA MONSTER HUNTER</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='cyber-tagline'>미디어 몬스터를 잡고 통찰력을 키워라!</div>", unsafe_allow_html=True)
        st.write("")

        if page == "home":
            page_home()
        elif page == "level":
            page_level()
        elif page == "dex":
            page_dex()
        elif page == "report":
            page_report()
        elif page == "teacher":
            page_teacher()
        else:
            page_home()

    st.divider()
    st.caption(
        "수업용 프로토타입 · API 키와 Supabase 접속정보는 Streamlit Secrets에만 보관되며 이 코드에는 들어있지 않습니다."
    )


if __name__ == "__main__":
    main()
