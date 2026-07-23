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
from datetime import datetime, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="팩트수색대", page_icon="🕵️", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 50% 0%, rgba(56,189,248,0.16), transparent 55%),
            repeating-linear-gradient(0deg, rgba(56,189,248,0.05) 0px, rgba(56,189,248,0.05) 1px, transparent 1px, transparent 56px),
            repeating-linear-gradient(90deg, rgba(56,189,248,0.05) 0px, rgba(56,189,248,0.05) 1px, transparent 1px, transparent 56px),
            linear-gradient(180deg, #060b16 0%, #0a1626 50%, #0b1a2c 100%);
        background-attachment: fixed;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(12, 27, 46, 0.55) !important;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(94, 234, 212, 0.28) !important;
        border-radius: 12px !important;
    }
    h1, h2, h3, h4 { color: #e6f1ff; }
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


col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("images/mascot-main.png")
with col_title:
    st.title("팩트수색대")
    st.caption("FACT SEARCH SQUAD · 교차검증 대시보드")

st.image("images/hero-team.png", use_container_width=True)
st.caption("A. 한결 · B. 진실 · C. 슬기 · D. 현탐 — 오늘도 출처를 찾으러 나선 수색대원들")

st.markdown(
    "하나의 키워드를 국내외 여러 공식 출처에 동시에 풀어놓고 찾아보 합니다. "
    "모르는 뉴스 용어는 사전으로 바로 찾아보고, 감이 안 잡히면 수색대원(챗봇)에게 물어보세요."
)

st.divider()

query = st.text_input("검증하고 싶은 키워드나 주장을 입력하세요", placeholder="예: 백신 부작용, 물가 상승률")
run = st.button("🔍 교차감정 실행", type="primary")

st.subheader("국내 출처")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        h1, h2 = st.columns([5, 1])
        h1.markdown("#### 🌐 GDELT Project")
        h2.image("images/char-gdelt-jinsil.png")
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
    with st.container(border=True):
        st.markdown("#### ✅ Google Fact Check")
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
    with st.container(border=True):
        h1, h2 = st.columns([5, 1])
        h1.markdown("#### 📊 KOSIS 통합검색")
        h2.image("images/char-kosis-seulgi.png")
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
    with st.container(border=True):
        h1, h2 = st.columns([5, 1])
        h1.markdown('#### 📰 정책브리핑 "사실은 이렇습니다"')
        h2.image("images/char-briefing-hangyeol.png")
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
with st.container(border=True):
    h1, h2 = st.columns([5, 1])
    h1.markdown("#### 📖 뉴스 용어 사전")
    h2.image("images/char-dict-hyeontam.png")
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
    with st.container(border=True):
        st.markdown("#### PolitiFact")
        st.caption("미국 팩트체크 전문 매체. 추후 연동 예정입니다.")
        st.link_button("politifact.com 바로가기", "https://www.politifact.com")
with fc2:
    with st.container(border=True):
        st.markdown("#### AFP Fact Check")
        st.caption("AFP 통신사 국제 팩트체크. 추후 연동 예정입니다.")
        st.link_button("factcheck.afp.com 바로가기", "https://factcheck.afp.com")

st.subheader("수색대원에게 물어보기")

face_cols = st.columns(8)
face_files = ["face-hangyeol.png", "face-jinsil.png", "face-seulgi.png", "face-hyeontam.png"]
for i, f in enumerate(face_files):
    with face_cols[i]:
        st.image(f"images/{f}")

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
