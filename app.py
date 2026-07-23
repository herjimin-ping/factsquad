"""
팩트수색대 — Streamlit 버전
API 키는 전부 st.secrets 에서만 읽어옵니다. 이 파일에는 실제 키 값이 없습니다.

필요한 시크릿 이름:
  GOOGLE_FACTCHECK_API_KEY
  KOSIS_API_KEY
  POLICY_SERVICE_KEY
  SOLAR_API_KEY
  KRDICT_API_KEY
  STDICT_API_KEY
"""

import re
from base64 import b64encode
from datetime import datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="팩트수색대", page_icon="🕵️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');

    .stApp {
        background:
            radial-gradient(circle at 20% 10%, rgba(56,189,248,0.16), transparent 40%),
            radial-gradient(circle at 85% 15%, rgba(94,234,212,0.10), transparent 45%),
            repeating-linear-gradient(0deg, rgba(56,189,248,0.07) 0px, rgba(56,189,248,0.07) 1px, transparent 1px, transparent 46px),
            repeating-linear-gradient(90deg, rgba(56,189,248,0.07) 0px, rgba(56,189,248,0.07) 1px, transparent 1px, transparent 46px),
            linear-gradient(180deg, #04070f 0%, #071527 45%, #0a1b30 100%);
        background-attachment: fixed;
    }

    h1, h2, h3 { color: #eaf6ff; }
    .cyber-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        color: #ffffff;
        font-size: 34px;
        letter-spacing: 0.5px;
        margin: 0;
        text-shadow: 0 0 16px rgba(56,189,248,0.55);
    }
    .cyber-sub { color:#9fd6f5; font-size:0.85rem; margin-top:-2px; }
    .cyber-tagline {
        color:#cdeaff; font-size:0.95rem; margin:6px 0 4px;
        border-left:3px solid #38bdf8; padding-left:10px;
    }
    .char-name { text-align:center; font-weight:700; color:#5eead4; margin-top:6px; }
    .char-role { text-align:center; font-size:0.78rem; color:#bcd3e8; line-height:1.4; padding:0 6px; }

    .holo-card {
        position: relative;
        aspect-ratio: 3 / 4;
        border: 1px solid rgba(94,234,212,0.55);
        border-radius: 14px;
        box-shadow: 0 0 22px rgba(56,189,248,0.30);
        overflow: hidden;
    }
    .holo-card img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        border: none;
        box-shadow: none;
    }
    .holo-topline {
        position: absolute;
        top: 0; left: 0; right: 0;
        font-family: 'Orbitron', sans-serif;
        font-size: 9px;
        letter-spacing: 1px;
        color: #eafffb;
        display: flex;
        justify-content: space-between;
        padding: 8px 10px;
        background: linear-gradient(180deg, rgba(4,10,20,0.75), transparent);
        z-index: 2;
    }
    .holo-caption {
        position: absolute;
        left: 0; right: 0; bottom: 0;
        padding: 24px 10px 8px;
        background: linear-gradient(180deg, transparent, rgba(4,10,20,0.92) 55%);
        z-index: 2;
    }

    .avatar-circle {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        border: 2px solid #38bdf8;
        background-color: #0b172a;
        overflow: hidden;
        display: inline-block;
    }
    .avatar-circle img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
        display: block;
    }
    .holo-name {
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        color: #ffffff;
        font-size: 15px;
        text-align: center;
        text-shadow: 0 0 8px rgba(56,189,248,0.65);
        margin: 4px 0 0;
    }
    .holo-role {
        font-size: 10.5px;
        color: #9fd6f5;
        text-align: center;
        line-height: 1.35;
        margin-top: 3px;
        padding: 0 4px;
    }
    .holo-bottomline {
        font-family: 'Orbitron', sans-serif;
        font-size: 8px;
        letter-spacing: 1px;
        color: #38bdf8;
        text-align: right;
        margin-top: 5px;
        opacity: 0.8;
    }

    /* 카드(container border=True, key="card-...") — 흰색 유리 패널, 확실하게 먹히는 key 기반 선택자 */
    div[class*="st-key-card-"] {
        background: rgba(255, 255, 255, 0.97) !important;
        border: 1px solid rgba(56,189,248,0.35) !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25);
    }
    div[class*="st-key-card-"] h1,
    div[class*="st-key-card-"] h2,
    div[class*="st-key-card-"] h3,
    div[class*="st-key-card-"] h4,
    div[class*="st-key-card-"] p,
    div[class*="st-key-card-"] span,
    div[class*="st-key-card-"] label {
        color: #16233b !important;
    }
    .card-title {
        font-size: 15px;
        font-weight: 700;
        color: #16233b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
    }

    /* 해외 출처 카드 — 국내(흰색)와 구분되는 호박색 톤 */
    .foreign-card {
        background: rgba(255, 247, 230, 0.96);
        border: 1px solid rgba(245, 158, 11, 0.55);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25);
        height: 100%;
    }
    .foreign-card h4 { color:#7c4a03; margin:0 0 6px; font-size:16px; }
    .foreign-card p { color:#8a5a12; font-size:13px; margin:0 0 12px; }
    .foreign-card a.btn {
        display:inline-block; padding:8px 14px; border:1px solid #f59e0b;
        color:#b45309; border-radius:8px; text-decoration:none;
        font-size:13px; font-weight:700; background: rgba(245,158,11,0.08);
    }

    /* 검색창 등 입력창은 항상 흰색으로 */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #16233b !important;
        border: 1px solid #d9e2f1 !important;
    }
    .stTextInput input::placeholder { color: #94a3b8 !important; }

    /* 헤더: 마스코트 + 제목을 가깝게 붙이기 */
    .brand-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .brand-row img { width: 64px; height: 64px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(key: str) -> str:
    return st.secrets.get(key, "")


GOOGLE_FACTCHECK_API_KEY = secret("GOOGLE_FACTCHECK_API_KEY")
KOSIS_API_KEY = secret("KOSIS_API_KEY")
POLICY_SERVICE_KEY = secret("POLICY_SERVICE_KEY")
SOLAR_API_KEY = secret("SOLAR_API_KEY")
KRDICT_API_KEY = secret("KRDICT_API_KEY")
STDICT_API_KEY = secret("STDICT_API_KEY")


@st.cache_data(ttl=300, show_spinner=False)
def fetch_gdelt(q: str):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {"query": q, "mode": "artlist", "maxrecords": 8, "format": "json", "sort": "hybridrel"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("articles", [])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_google_factcheck(q: str):
    if not GOOGLE_FACTCHECK_API_KEY:
        return None
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": q, "key": GOOGLE_FACTCHECK_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("claims", [])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_kosis(q: str):
    if not KOSIS_API_KEY:
        return None
    url = "https://kosis.kr/openapi/statisticsSearch.do"
    params = {
        "method": "getList",
        "apiKey": KOSIS_API_KEY,
        "searchNm": q,
        "format": "json",
        "resultCount": 8,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    return data.get("SearchInfo", data.get("searchInfo", []))


@st.cache_data(ttl=300, show_spinner=False)
def fetch_briefing(keyword: str):
    if not POLICY_SERVICE_KEY:
        return None
    end = datetime.utcnow()
    start = end - timedelta(days=2)
    url = "http://apis.data.go.kr/1371000/policyNewsService/policyNewsList"
    params = {
        "serviceKey": POLICY_SERVICE_KEY,
        "startDate": start.strftime("%Y%m%d"),
        "endDate": end.strftime("%Y%m%d"),
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    xml = r.text

    def field(block: str, tag: str) -> str:
        m = re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", block, re.S)
        return m.group(1).strip() if m else ""

    items = []
    for block in xml.split("<NewsItem>")[1:]:
        if field(block, "GroupingCode") != "fact":
            continue
        title = field(block, "Title")
        contents = re.sub("<[^>]+>", " ", field(block, "DataContents"))
        if keyword and keyword.lower() not in title.lower() and keyword.lower() not in contents.lower():
            continue
        items.append({
            "title": title,
            "minister": field(block, "MinisterCode"),
            "date": field(block, "ApproveDate"),
            "url": field(block, "OriginalUrl"),
        })
    return items


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dict(word: str):
    entries = []
    if KRDICT_API_KEY:
        try:
            r = requests.get(
                "https://krdict.korean.go.kr/api/search",
                params={
                    "key": KRDICT_API_KEY, "q": word, "translated": "n",
                    "part": "word", "method": "exact", "type_search": "search", "req_type": "json",
                },
                timeout=10,
            )
            data = r.json()
            for it in data.get("channel", {}).get("item", []):
                d = (it.get("sense") or {}).get("definition")
                if d:
                    entries.append({"word": it.get("word"), "source": "한국어기초사전", "definition": d})
        except Exception:
            pass
    if not entries and STDICT_API_KEY:
        try:
            r = requests.get(
                "https://stdict.korean.go.kr/api/search.do",
                params={"key": STDICT_API_KEY, "q": word, "req_type": "json"},
                timeout=10,
            )
            data = r.json()
            for it in data.get("channel", {}).get("item", []):
                d = (it.get("sense") or {}).get("definition")
                if d:
                    entries.append({"word": it.get("word"), "source": "표준국어대사전", "definition": d})
        except Exception:
            pass
    return entries


def img_b64(path: str) -> str:
    with open(path, "rb") as f:
        return b64encode(f.read()).decode()


def holo_card(img_path: str, unit_no: str, name: str, role_line: str, meaning: str):
    b64 = img_b64(img_path)
    st.markdown(
        f"""
        <div class="holo-card">
            <img src="data:image/png;base64,{b64}">
            <div class="holo-topline"><span>UNIT.{unit_no}</span><span>● ACTIVE</span></div>
            <div class="holo-caption">
                <div class="holo-name">{name}</div>
                <div class="holo-role">{role_line}<br>{meaning}</div>
                <div class="holo-bottomline">SCAN // OK</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def avatar_badge(img_path: str) -> str:
    b64 = img_b64(img_path)
    return f'<div class="avatar-circle"><img src="data:image/png;base64,{b64}"></div>'


def foreign_card(name: str, desc: str, url: str, link_text: str) -> str:
    return f"""
    <div class="foreign-card">
        <h4>{name}</h4>
        <p>{desc}</p>
        <a class="btn" href="{url}" target="_blank">{link_text} →</a>
    </div>
    """


def solar_chat(message: str) -> str:
    if not SOLAR_API_KEY:
        return "Solar API 키가 설정되지 않았어요. Streamlit Secrets에 SOLAR_API_KEY를 추가해주세요."
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
                            '너는 "팩트수색대" 웹사이트의 수색대원이다. 미디어 리터러시 수업을 듣는 '
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


st.markdown(
    f"""
    <div class="brand-row">
        <img src="data:image/png;base64,{img_b64('images/mascot-main.png')}">
        <div>
            <div class="cyber-title">팩트수색대</div>
            <div class="cyber-sub">FACT SEARCH SQUAD</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='cyber-tagline'>AI 시대의 뉴스·정보 교차검증 대시보드</div>",
    unsafe_allow_html=True,
)

st.write("")

hc1, hc2, hc3, hc4 = st.columns(4)
with hc1:
    holo_card("images/char-briefing-hangyeol.png", "01", "한결 대원", "리더 / 기록", "변함없이 '한결'같은 마음으로 진실을 지킨다")
with hc2:
    holo_card("images/char-gdelt-jinsil.png", "02", "진실 대원", "정보 수집", "정보 속에 숨겨진 진짜 '진실'을 찾아낸다")
with hc3:
    holo_card("images/char-kosis-seulgi.png", "03", "슬기 대원", "데이터 분석", "데이터를 '슬기'롭게 분석해 핵심을 짚어낸다")
with hc4:
    holo_card("images/char-dict-hyeontam.png", "04", "현탐 대원", "현장 조사", "'현장'을 철저히 '탐구'하고 증거를 포착한다")

st.write("")

query = st.text_input(
    "검증하고 싶은 키워드나 주장을 입력하세요",
    placeholder="예: 백신 부작용, 물가 상승률",
    label_visibility="collapsed",
)
run = st.button("🔍 교차검증 실행", type="primary")

st.divider()

st.subheader("국내 출처")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True, key="card-gdelt"):
        ch1, ch2 = st.columns([5, 1])
        ch1.markdown("<p class='card-title'>🌐 GDELT Project</p>", unsafe_allow_html=True)
        ch2.markdown(avatar_badge("images/avatar-jinsil.png"), unsafe_allow_html=True)
        if run and query:
            try:
                arts = fetch_gdelt(query)
                if arts:
                    for a in arts[:8]:
                        st.markdown(f"**[{a.get('title','')}]({a.get('url','#')})**")
                        st.caption(f"{a.get('domain','')} · {a.get('seendate','')} · {a.get('language','')}")
                else:
                    st.caption("일치하는 기사를 찾지 못했습니다. 영어 키워드로 시도해보세요.")
            except Exception as e:
                st.caption(f"조회 실패: {e}")
        else:
            st.caption("검색을 실행하면 여기에 결과가 표시됩니다.")

with col2:
    with st.container(border=True, key="card-google"):
        ch1, ch2 = st.columns([5, 1])
        ch1.markdown("<p class='card-title'>✅ Google Fact Check</p>", unsafe_allow_html=True)
        ch2.markdown(avatar_badge("images/avatar-hyeontam.png"), unsafe_allow_html=True)
        if run and query:
            claims = fetch_google_factcheck(query)
            if claims is None:
                st.caption("Streamlit Secrets에 GOOGLE_FACTCHECK_API_KEY를 추가하면 조회됩니다.")
            elif claims:
                for c in claims[:8]:
                    review = (c.get("claimReview") or [{}])[0]
                    st.markdown(f"**[{c.get('text','')}]({review.get('url','#')})**")
                    st.caption(f"{c.get('claimant','출처 미상')} · {(review.get('publisher') or {}).get('name','')}")
                    if review.get("textualRating"):
                        st.caption(f"판정: {review['textualRating']}")
            else:
                st.caption("등록된 팩트체크 결과가 없습니다.")
        else:
            st.caption("검색을 실행하면 여기에 결과가 표시됩니다.")

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True, key="card-kosis"):
        ch1, ch2 = st.columns([5, 1])
        ch1.markdown("<p class='card-title'>📊 KOSIS 통합검색</p>", unsafe_allow_html=True)
        ch2.markdown(avatar_badge("images/avatar-seulgi.png"), unsafe_allow_html=True)
        if run and query:
            items = fetch_kosis(query)
            if items is None:
                st.caption("Streamlit Secrets에 KOSIS_API_KEY를 추가하면 조회됩니다.")
            elif items:
                for it in items[:8]:
                    link = it.get("LINK_URL") or it.get("TBL_VIEW_URL") or "#"
                    st.markdown(f"**[{it.get('TBL_NM','')}]({link})**")
                    st.caption(f"{it.get('ORG_NM','')} · {it.get('STRT_PRD_DE','')}~{it.get('END_PRD_DE','')}")
            else:
                st.caption("일치하는 통계표를 찾지 못했습니다.")
        else:
            st.caption("검색을 실행하면 여기에 결과가 표시됩니다.")

with col4:
    with st.container(border=True, key="card-briefing"):
        ch1, ch2 = st.columns([5, 1])
        ch1.markdown('<p class="card-title">📰 정책브리핑 "사실은 이렇습니다"</p>', unsafe_allow_html=True)
        ch2.markdown(avatar_badge("images/avatar-hangyeol.png"), unsafe_allow_html=True)
        if run and query:
            items = fetch_briefing(query)
            if items is None:
                st.caption("Streamlit Secrets에 POLICY_SERVICE_KEY를 추가하면 조회됩니다.")
            elif items:
                for it in items[:8]:
                    st.markdown(f"**[{it['title']}]({it['url'] or '#'})**")
                    st.caption(f"{it['minister']} · {it['date']}")
            else:
                st.caption('최근 3일 내 일치하는 "사실은 이렇습니다" 게시물이 없습니다.')
        else:
            st.caption("검색을 실행하면 여기에 결과가 표시됩니다.")

st.subheader("용어 사전 — 이 단어, 무슨 뜻?")
with st.container(border=True, key="card-dict"):
    ch1, ch2 = st.columns([5, 1])
    ch1.markdown("<p class='card-title'>📖 뉴스 용어 사전</p>", unsafe_allow_html=True)
    ch2.markdown(avatar_badge("images/avatar-jinsil.png"), unsafe_allow_html=True)
    word = st.text_input("뉴스에서 본 낯선 단어를 입력", placeholder="예: 필리버스터, 유예", key="dict_word")
    if st.button("찾기"):
        if word:
            entries = fetch_dict(word)
            if entries:
                for e in entries[:5]:
                    st.markdown(f"**{e['word']}** · _{e['source']}_")
                    st.write(e["definition"])
            else:
                st.caption(f'"{word}"에 대한 뜻풀이를 찾지 못했습니다. 수색대원(챗봇)에게 물어보세요.')

st.subheader("해외 출처 (연동 예정)")
fc1, fc2 = st.columns(2)
with fc1:
    st.markdown(
        foreign_card("PolitiFact", "미국 팩트체크 전문 매체. 추후 연동 예정입니다.", "https://www.politifact.com", "politifact.com 바로가기"),
        unsafe_allow_html=True,
    )
with fc2:
    st.markdown(
        foreign_card("AFP Fact Check", "AFP 통신사 국제 팩트체크. 추후 연동 예정입니다.", "https://factcheck.afp.com", "factcheck.afp.com 바로가기"),
        unsafe_allow_html=True,
    )

st.subheader("수색대원에게 물어보기")

with st.container(border=True, key="card-chat"):
    face_cols = st.columns(8)
    face_files = ["avatar-hangyeol.png", "avatar-jinsil.png", "avatar-seulgi.png", "avatar-hyeontam.png"]
    for i, f in enumerate(face_files):
        with face_cols[i]:
            st.markdown(avatar_badge(f"images/{f}"), unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, text in st.session_state.chat_history:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.write(text)

    user_msg = st.chat_input("예: 이 기사에 나온 '컨틴전시 플랜'이 뭐야?")
    if user_msg:
        st.session_state.chat_history.append(("user", user_msg))
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("생각 중…"):
                reply = solar_chat(user_msg)
            st.write(reply)
        st.session_state.chat_history.append(("assistant", reply))

st.divider()
st.caption("수업용 프로토타입 · 모든 API 키는 Streamlit Secrets에만 보관되며 이 코드에는 들어있지 않습니다.")
