"""
Monster Insight — AI 미디어 몬스터 헌터
'팩트수색대'를 게임형으로 확장한 미디어 리터러시 대시보드입니다.

필요한 Secrets (전부 선택 사항 — 없으면 데모 데이터/로컬 저장으로 동작합니다):
  GOOGLE_FACTCHECK_API_KEY   루머 유령 미션에서 실제 팩트체크 검색에 사용
  SOLAR_API_KEY              AI 환각 몬스터 미션에서 실제 AI 답변 생성에 사용 (Upstage Solar)
  SUPABASE_URL               학생 플레이 기록을 저장할 Supabase 프로젝트 URL
  SUPABASE_KEY               Supabase anon/service key

이 파일에는 실제 키 값이 들어있지 않습니다. Streamlit Secrets에 위 이름으로 등록하세요.
"""

import random
from datetime import datetime, timezone

import requests
import streamlit as st

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
    h1, h2, h3 { color: #eaf6ff; }

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
    div[class*="st-key-panel-"] label, div[class*="st-key-panel-"] li {
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
    .monster-emoji { font-size: 54px; line-height: 1; }
    .monster-name {
        font-family: 'Orbitron', sans-serif; font-weight: 700; color: #ffffff;
        font-size: 18px; margin: 8px 0 2px; text-shadow: 0 0 8px rgba(167,139,250,0.65);
    }
    .monster-cat { font-size: 11px; color:#9fd6f5; letter-spacing: 1px; }
    .monster-intro { font-size: 13px; color:#d7e6ff; margin-top:10px; line-height:1.5; }

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
    }
    .stButton button:hover { background-color: #8b6cf0 !important; color:#ffffff !important; }

    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important; color: #16233b !important;
        border: 1px solid #d9e2f1 !important;
    }
    .stTextInput input::placeholder { color: #94a3b8 !important; }

    .xp-badge {
        display:inline-block; padding:4px 12px; border-radius:999px;
        background: rgba(167,139,250,0.18); border:1px solid rgba(167,139,250,0.5);
        color:#e9defe; font-size:13px; font-weight:700; margin-right:8px;
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


def stars_html(n: int, total: int = 5) -> str:
    return "★" * n + "☆" * (total - n)


def goto(page: str, monster: str | None = None):
    st.session_state.page = page
    if monster is not None:
        st.session_state.current_monster = monster


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
        st.markdown(f"**{r['prompt']}**")
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
                    st.markdown(f"- **{c.get('text', '')}** · {(review.get('publisher') or {}).get('name', '')} "
                                f"· 판정: {review.get('textualRating', '미상')}")
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


def play_monster(monster_id: str):
    m = MONSTERS[monster_id]
    st.markdown(
        f"""
        <div class="monster-card">
            <div class="monster-emoji">{m['emoji']}</div>
            <div class="monster-name">{m['name']} 등장!!</div>
            <div class="monster-cat">{CATEGORY_LABEL[m['category']]}</div>
            <div class="monster-intro">{m['intro']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    if monster_id == "rumor":
        play_rumor(monster_id)
    elif monster_id == "deepfake":
        run_quiz(monster_id, DEEPFAKE_ROUNDS, ["AI 그림", "실제 사진"])
    elif monster_id == "ad":
        run_quiz(monster_id, AD_ROUNDS, ["광고", "뉴스"])
    elif monster_id == "phishing":
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
                    <div class="monster-emoji">{m['emoji']}</div>
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
        any_data = False
        for cat, label in CATEGORY_LABEL.items():
            data = ss.category_scores[cat]
            if data["attempts"] == 0:
                st.write(f"- {label}: 아직 도전 기록이 없어요.")
                continue
            any_data = True
            score = round(data["success"] / data["attempts"] * 100)
            st.write(f"**{label}** — {score}점 (시도 {data['attempts']}회 · 성공 {data['success']}회)")
            st.progress(score / 100)
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

    monster_counts = {}
    monster_attempts = {}
    monster_success = {}
    total_success = 0
    for row in rows:
        mid = row.get("monster_id", "?")
        name = row.get("monster_name", mid)
        monster_attempts[name] = monster_attempts.get(name, 0) + 1
        if row.get("success"):
            monster_counts[name] = monster_counts.get(name, 0) + 1
            monster_success[name] = monster_success.get(name, 0) + 1
            total_success += 1

    with st.container(border=True, key="panel-teacher"):
        st.write(f"총 플레이 기록: **{len(rows)}건** · 성공 **{total_success}건**")

        if monster_counts:
            most_caught = max(monster_counts, key=monster_counts.get)
            st.write(f"**가장 많이 잡은 몬스터:** {most_caught} ({monster_counts[most_caught]}회)")

        difficulty = {
            name: (monster_success.get(name, 0) / att)
            for name, att in monster_attempts.items()
            if att > 0
        }
        if difficulty:
            hardest = min(difficulty, key=difficulty.get)
            st.write(f"**가장 어려운 몬스터:** {hardest} (성공률 {difficulty[hardest] * 100:.0f}%)")

        overall_rate = total_success / len(rows) if rows else 0
        stars = max(1, round(overall_rate * 5))
        st.write(f"**학급 평균 통찰력:** {stars_html(stars)} (전체 성공률 {overall_rate * 100:.0f}%)")

        st.write("---")
        st.markdown("**학생별 요약**")
        by_student = {}
        for row in rows:
            name = row.get("student_name", "익명")
            s = by_student.setdefault(name, {"attempts": 0, "success": 0, "xp": 0})
            s["attempts"] += 1
            s["xp"] += row.get("xp_gained", 0) or 0
            if row.get("success"):
                s["success"] += 1
        for name, s in sorted(by_student.items(), key=lambda kv: -kv[1]["xp"]):
            st.write(f"- {name}: 시도 {s['attempts']}회 · 성공 {s['success']}회 · 누적 XP {s['xp']}")


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
        for mid, m in MONSTERS.items():
            if st.button(f"{m['emoji']} {m['name']}", key=f"nav-{mid}", use_container_width=True):
                goto("playing", mid)
                st.rerun()

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

    page = ss.page
    if page == "home":
        page_home()
    elif page == "playing":
        mid = ss.current_monster or random.choice(TEAM)
        ss.current_monster = mid
        play_monster(mid)
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
