import streamlit as st
import streamlit.components.v1 as stc
import json, copy, time, re, base64
from pathlib import Path

# ── 로고 이미지 로드 ──
_LOGO_PATH = Path(__file__).parent / "aible_campus_logo.png"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode()
_LOGO_IMG = f'<img src="data:image/png;base64,{_LOGO_B64}" style="height:28px;vertical-align:middle;margin-right:6px">'

st.set_page_config(
    page_title="에이블캠퍼스 전략 대시보드",
    page_icon="🅰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Streamlit 기본 상단 요소 숨기기 */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
footer { display: none !important; }

.main .block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:90%; margin:0 auto; }
div[data-testid="stVerticalBlock"] > div:not([data-testid="stHorizontalBlock"]) { gap: 0; }
div[data-testid="stHorizontalBlock"] { gap: 12px !important; }
.element-container { margin-bottom: 0 !important; }
.edit-actions .stButton button {
    padding: 2px 9px !important; font-size: 13px !important;
    height: 26px !important; min-height: 26px !important;
    line-height: 1 !important; border-radius: 4px !important;
}
.stMarkdown p { margin-bottom: 0; }
.edit-actions div[data-baseweb="select"] > div:first-child {
    min-height: 26px !important; height: 26px !important;
    padding-top: 0 !important; padding-bottom: 0 !important;
    font-size: 13px !important;
}
details summary { font-size: 16px !important; font-weight: 600; }
div[data-testid="stButton"] button,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
.stButton > button,
.stButton > button p,
.stButton > button span,
button[data-testid*="baseButton"] p,
button[data-testid*="baseButton"] span,
button[data-testid*="baseButton"] {
    font-size: 13px !important;
}
[data-item-id] { transition: opacity 0.15s, box-shadow 0.15s; position: relative; box-sizing: border-box; max-width: 100%; }
div[data-testid="stColumn"] { min-width: 0; }
[data-item-id]:hover { box-shadow: 0 0 0 2px rgba(7,76,186,0.2); cursor: grab; overflow: visible !important; z-index: 100; }
[data-item-id]:hover .ec-tip { display: block !important; }
/* 집중 과제 체크리스트 */
div[data-testid="stCheckbox"] label p,
div[data-testid="stCheckbox"] label span {
    color: #1A1A1A !important;
    font-size: 17px !important;
}
div[data-testid="stCheckbox"] {
    background: #F5F7FA;
    border-radius: 6px;
    padding: 6px 10px;
    margin-bottom: 3px;
    border-left: 2px solid #D0D8E8;
}
div[data-testid="stCheckbox"]:has(input:checked) {
    background: #EBF0FF;
    border-left: 2px solid #074CBA;
}
</style>
""", unsafe_allow_html=True)

# ── 상수 ─────────────────────────────────────────────────────────────────────
ROLES   = ["영업", "마케팅", "교육운영", "강의자료", "교육설계"]
TIMINGS = ["단기", "중장기"]

ROLE_CFG = {
    "영업":     {"main": "#D4822A", "prio": "#FFF3E0", "dim": "#F5DCC0"},
    "마케팅":   {"main": "#3A7BD5", "prio": "#E3F0FF", "dim": "#C8DEFE"},
    "교육운영": {"main": "#2E9E5E", "prio": "#E6F7ED", "dim": "#C0E8D0"},
    "강의자료": {"main": "#7B4FB0", "prio": "#F0E8FA", "dim": "#DCC8F0"},
    "미정":     {"main": "#C05070", "prio": "#FCE4EC", "dim": "#F0C0D0"},
    "교육설계": {"main": "#C84030", "prio": "#FFEBE8", "dim": "#F5CCC8"},
}

ROLE_TO_PERSON = {
    "영업":     "김보현",
    "마케팅":   "백수경",
    "강의자료": "남동현",
    "교육운영": "박지원",
    "교육설계": "이기혁",
    "미정":     "미정",
}
PERSON_ORDER = ["김보현", "백수경", "남동현", "박지원", "이기혁"]
T_CLR = {"단기": "#C89520", "중장기": "#2E9E5E"}

COL_META = {
    "vm":      {"title": "비전·미션",  "sub": "",                          "color": "#2D89FF", "dark_text": False},
    "s1":      {"title": "전략 1",    "sub": "조직 역량 강화",              "color": "#D6E8FF", "dark_text": True},
    "s2":      {"title": "전략 2",    "sub": "시장 확장",                   "color": "#C4DEFF", "dark_text": True},
    "s3":      {"title": "전략 3",    "sub": "교육 서비스 체계화",           "color": "#B0D4FF", "dark_text": True},
    "backlog": {"title": "백로그",    "sub": "",                           "color": "#E0E4EA", "dark_text": True},
}
COL_ORDER = ["s1", "s2", "s3"]
DATA_PATH = Path(__file__).parent / "dashboard_data.json"

# ── 초기 데이터 (dashboard_data.json 과 동기화) ──────────────────────────────
INITIAL_DATA: dict = {
    "vision":  "기업들이 일하는 방식을 AI 중심으로 재편한다",
    "mission": "기업이 AI를 스스로 활용할 수 있는 조직이 되기 위한 지식과 인프라를 제공한다",
    "columns": {
        "vm":      [],
        "s1":      ["vm1","s1e","s3a","vm2","vm5","s1d","s1b","vm6","s1h","vm7","s1j","s1k","s3l"],
        "s2":      ["s3b","s3i","s3d","vm3","s2e","s2d","s2f","s3e","s1f","s2a","s2b","s3k"],
        "s3":      ["lkh1","s3c","s1i","s1g","s3f","s3g","s3j","s3h","vm8"],
        "backlog": [],
    },
    "items": {
        "lkh1":{"id":"lkh1","role":"교육설계","timing":"단기", "text":"대표프로그램 기획",                      "isPrio":True, "notes":"", "ax":False},
        "vm1": {"id":"vm1","role":"강의자료","timing":"단기",  "text":"① 강의 스토리라인 기획 AX",             "isPrio":True, "notes":"- 실제 강의 기획에 반복 사용 가능한 수준으로 MVP 완성 및 고도화\n- 논리적 연결성/난이도 조절/슬라이드별 기획으로의 연결 (제목, 핵심 메시지, 의도 포함)\n- 산출물 품질 향상: 테스트케이스/루브릭/체크리스트 수립 및 피드백 루프 반영", "ax":True},
        "vm2": {"id":"vm2","role":"영업",    "timing":"단기",  "text":"④ 이메일 회신 자동 초안 생성 (AX)",      "isPrio":False,"notes":"- 요구사항 기반 1차 회신 자동화\n- 교육 유형별 템플릿 고도화\n→ 대응 속도 안정화, 전략 판단 시간 확보", "ax":True},
        "vm3": {"id":"vm3","role":"교육운영","timing":"단기",  "text":"사업계획서 작성 체계 수립",               "isPrio":True, "notes":"- 심사기준 어필 포인트 매칭 (통과/미통과 제안서 비교 분석, 강점 체계화)\n- 회사 정보 DB 참조하기", "ax":True},
        "vm5": {"id":"vm5","role":"영업",    "timing":"단기",  "text":"① 문의 분류 자동화 (AX)",               "isPrio":False,"notes":"- 임원교육 / 전사교육 / Copilot / AX 컨설팅 등 자동 태깅\n- 산업 / 기업 규모 / 반복 가능성 기준 세분화\n→ 전략 우선순위 판단 시간 단축, 집중 딜 선별", "ax":True},
        "vm6": {"id":"vm6","role":"강의자료","timing":"단기",  "text":"③ 에이블 구성원 AI 활용 능력 향상 지원",  "isPrio":True, "notes":"- Claude Code/업무 활용 패턴 템플릿화\n- 내부 온보딩 문서/워크숍 형태로 확산"},
        "vm7": {"id":"vm7","role":"강의자료","timing":"중장기","text":"① AX 도구 허브/플랫폼화",                "isPrio":False,"notes":"- 흩어진 AX 기능을 '한 곳에서 접근/사용' 가능하도록 통합\n- 프롬프트/스킬 고도화 체계 정착 (버전관리 등)"},
        "vm8": {"id":"vm8","role":"교육운영","timing":"중장기","text":"운영 데이터 기반 성과 분석 자동화",       "isPrio":False,"notes":""},
        "s1b": {"id":"s1b","role":"교육운영","timing":"단기",  "text":"운영 레퍼런스 아카이브 구축",            "isPrio":True, "notes":""},
        "s1d": {"id":"s1d","role":"영업",    "timing":"단기",  "text":"③ 과거 영업 자료 SOT (AX)",             "isPrio":False,"notes":"- 산업/키워드 기반 제안서 자동 추천\n- 성공 사례 DB화\n→ 제안 준비 시간 단축, 반복 작업 최소화", "ax":True},
        "s1e": {"id":"s1e","role":"강의자료","timing":"단기",  "text":"② 제안서 기획/작성 파이프라인 AX",       "isPrio":False,"notes":"- 제안서 구조 템플릿화, 레퍼런스 기반 재사용, 유사 과제/고객군 매칭 아이디어 정리\n- 요구사항 입력 폼 기반으로 기획/슬라이드 초안 생성 워크플로우 초안 설계\n- 단기 목표: '제안서 기획 + 초안 설계' 수준으로 제작", "ax":True},
        "s1f": {"id":"s1f","role":"교육운영","timing":"단기",  "text":"타사 B2G 벤치마킹 정리",                "isPrio":False,"notes":""},
        "s1g": {"id":"s1g","role":"교육운영","timing":"단기",  "text":"AI 리터러시 이러닝 콘텐츠 개발",         "isPrio":False,"notes":""},
        "s1h": {"id":"s1h","role":"강의자료","timing":"중장기","text":"② 강의자료 제작 파이프라인 AX 고도화",   "isPrio":True, "notes":"- 스토리라인 기획 → 슬라이드별 기획 → 슬라이드 초안 → 스크립트 생성까지 단계별 모듈 확장\n- 생성 결과물을 반복 사용 가능한 자산(데이터/템플릿/톤)으로 축적\n- 피드백을 구조화하여 프롬프트/톤에 지속 반영 (실험/생각 루프)\n- AX 도구 적용 과정에서 필요한 자료 제작/검수/피드백 반영 지원\n- 기존 제안서/강의 레퍼런스 아카이빙 및 데이터화 (AI Friendly)\n", "ax":True},
        "s1i": {"id":"s1i","role":"교육운영","timing":"단기",  "text":"교육 프로그램 개발",                     "isPrio":False,"notes":"- 채용 공고 및 직무 기술서 수집/분석  → 업종별 AI 교육 수요 트렌드 분석 [AX]", "ax":True},
        "s1j": {"id":"s1j","role":"강의자료","timing":"중장기","text":"④ 마케팅/영업/운영 AX 확장",            "isPrio":False,"notes":"- 각 조직에서 반복되는 업무를 발굴\n- AX 적용 (우선순위/효과 기준 정해 단계적 확대)"},
        "s1k": {"id":"s1k","role":"강의자료","timing":"중장기","text":"⑤ 업무지원 소프트웨어 확장 E2E",         "isPrio":False,"notes":"- 영업/제안 → 커리큘럼 설계 → 운영 실행까지 이어지는 업무 흐름을 AI로 보조하는 내부 소프트웨어 방향 정립\n- 권한/보안/로그/품질 기준 포함한 운영 가능한 체계로 발전"},
        "s2a": {"id":"s2a","role":"마케팅",  "timing":"중장기","text":"B2G 전용 브랜드 에셋 제작",             "isPrio":True, "notes":"- 마케팅 이벤트 기획/운영  (사전설명회, 수료식 등)\n- 제작사 네트워크 구축 (수료키트/웰컴팩/굿즈 포함)\n- 모집 홍보 콘텐츠 제작, 홍보 후 문의 사후관리\n- 수료생 ↔ 파트너사 매칭 사례 확보, 수료생 인터뷰\n", "ax":False},
        "s2b": {"id":"s2b","role":"마케팅",  "timing":"중장기","text":"B2G 홍보처 리스트업 & 채널 개설",        "isPrio":False,"notes":"- B2B: 공공기업\n- B2G: 주요 대학 취업지원센터 및 학과 연락처, IT/개발 커뮤니티\n", "ax":False},
        "s2d": {"id":"s2d","role":"마케팅",  "timing":"단기",  "text":"브랜드 채널 콘텐츠 제작 및 배포",        "isPrio":True, "notes":""},
        "s2e": {"id":"s2e","role":"마케팅",  "timing":"단기",  "text":"B2B/B2G 통합 브랜드 포지셔닝 전략",      "isPrio":True, "notes":""},
        "s2f": {"id":"s2f","role":"교육운영","timing":"단기",  "text":"해커톤 정규 모델화 (외부 확장)",          "isPrio":True, "notes":""},
        "s3a": {"id":"s3a","role":"영업",    "timing":"단기",  "text":"⑤ 커리큘럼/제안서 기획 초안 생성",      "isPrio":True, "notes":"- 스토리라인 템플릿 고정, 산업별/직급별/직군별 사례 모듈화\n→ 아이디에이션 + 기획 최소화, 완전 자동화 목표", "ax":True},
        "s3b": {"id":"s3b","role":"영업",    "timing":"단기",  "text":"⑥ 영업 대시보드 1차 구축 (HubSpot)",    "isPrio":True, "notes":"- 영업 단계 ↔ 리드 ↔ 고객(담당자) 연동 관리\n- 딜 단계/진행사항/특이사항 히스토리 정리\n- 제안서·커리큘럼·견적서 자료 관리, 예상 매출 관리", "ax":True},
        "s3c": {"id":"s3c","role":"교육운영","timing":"단기",  "text":"전담 PM 역할 확립 (이슈 대응 SOP)",      "isPrio":True, "notes":"단계별 수행물 관리", "ax":False},
        "s3d": {"id":"s3d","role":"영업",    "timing":"단기",  "text":"② 가치 판단 체계화 (딜 점수화)",         "isPrio":True, "notes":"- 딜 점수화 모델 도입 (예상매출 / 업셀 가능성 / 전략적 가치 / 브랜드 레퍼런스)\n- 이전 딜 drop/cut/fail 데이터 분석 → 기준 명확화\n→ 일정 점수 미달 시 Drop 또는 최소 대응", "ax":False},
        "s3e": {"id":"s3e","role":"교육운영","timing":"단기",  "text":"사업 공고 모니터링 체계화 (AX)",         "isPrio":False,"notes":""},
        "s3f": {"id":"s3f","role":"교육운영","timing":"단기",  "text":"B2G 운영 SOP 제작",                     "isPrio":False,"notes":"- 홍보-모집-선발-성과-결과 단계별 체크리스트\n- 운영데이터 입력 → 중간/완료/교육보고서 자동 생성 [AX]\n- 운영 프로그램 기획 표준화 [OT / 네트워킹 / 수료식 ..]\n", "ax":False},
        "s3g": {"id":"s3g","role":"교육운영","timing":"단기",  "text":"교육/행사 운영 매뉴얼화",                "isPrio":False,"notes":"- 물품 발주/세팅/현장/결과 가이드 제작\n- 필요 물품/업체 리스트 자동 생성 [AX]", "ax":False},
        "s3h": {"id":"s3h","role":"교육운영","timing":"중장기","text":"행정처리 가이드 정비",                   "isPrio":False,"notes":"- 증빙/훈련장려금/사업비 관리 표준화", "ax":False},
        "s3i": {"id":"s3i","role":"영업",    "timing":"단기",  "text":"⑦ 고객 유형별 타겟 리스트 구축",         "isPrio":True, "notes":"- 대기업 (반복 교육 + 예산 확보) 집중 공략\n- 파트너십 확대", "ax":False},
        "s3j": {"id":"s3j","role":"영업",    "timing":"중장기","text":"⑧ 프로젝트 이후 관계 유지 전략",         "isPrio":False,"notes":"- 목표: '편하게 질문할 수 있는 회사' 이미지 구축\n- 정기 인사이트 공유, 경영진 대상 소규모 세션 운영", "ax":False},
        "s3k": {"id":"s3k","role":"영업",    "timing":"중장기","text":"⑨ 영업 대시보드 고도화 (맞춤 CRM)",      "isPrio":False,"notes":"- 영업 전 단계 AX 기능 고도화 (제안서·커리큘럼·견적서 자료 관리)\n- 아웃바운드 고객 발굴 자동화\n→ 적은 리소스로 많은 리드 확보 + 대응", "ax":True},
        "s3l": {"id":"s3l","role":"교육운영","timing":"중장기","text":"내부 운영안정성 확보",                   "isPrio":False,"notes":""},
    },
    "col_meta": {
        "s1": {"title":"전략 1: 조직 역량 강화", "sub":"[우리 조직] 우리 조직의 AX 역량을 강화한다"},
        "s2": {"title":"전략 2: 시장 확장", "sub":"[잠재 고객] 잠재 고객에게 도달하고 신뢰를 얻는다"},
        "s3": {"title":"전략 3: 교육 서비스 체계화", "sub":"[특정 고객] 특정 고객에게 최고의 교육을 전달한다"},
        "vm": {"title":"비전·미션", "sub":""},
    },
}

# ── 데이터 I/O ────────────────────────────────────────────────────────────────
def load_data() -> dict:
    """JSON 파일이 유일한 데이터 소스. 없으면 INITIAL_DATA로 최초 생성."""
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # 최초 실행: INITIAL_DATA → JSON 파일 생성
    initial = copy.deepcopy(INITIAL_DATA)
    DATA_PATH.write_text(
        json.dumps(initial, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return initial

def save_data() -> None:
    DATA_PATH.write_text(
        json.dumps(st.session_state.data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

# ── 변이 함수 ────────────────────────────────────────────────────────────────
def toggle_priority(item_id: str) -> None:
    st.session_state.data["items"][item_id]["isPrio"] ^= True
    save_data()

def delete_item(item_id: str) -> None:
    st.session_state.data["items"].pop(item_id, None)
    for ids in st.session_state.data["columns"].values():
        if item_id in ids: ids.remove(item_id)
    save_data()

def move_item(item_id: str, from_col: str, to_col: str, before_id: str = "", new_timing: str = "") -> None:
    cols = st.session_state.data["columns"]
    if item_id in cols.get(from_col, []):
        cols[from_col].remove(item_id)
    target = cols.setdefault(to_col, [])
    if item_id in target:
        target.remove(item_id)
    if before_id and before_id in target:
        idx = target.index(before_id)
        target.insert(idx, item_id)
    else:
        target.append(item_id)
    # 드롭 대상 카드의 타이밍으로 변경
    if new_timing and new_timing in TIMINGS:
        st.session_state.data["items"][item_id]["timing"] = new_timing
    save_data()

def add_item(col_id: str, role: str, timing: str, text: str) -> None:
    nid = f"item_{int(time.time()*1000)}"
    st.session_state.data["items"][nid] = {
        "id": nid, "role": role, "timing": timing,
        "text": text, "isPrio": False, "notes": "", "ax": False,
    }
    st.session_state.data["columns"].setdefault(col_id, []).append(nid)
    save_data()

def save_item_edit(item_id, text, role, timing, notes, ax):
    item = st.session_state.data["items"][item_id]
    item["text"], item["role"], item["timing"], item["notes"], item["ax"] = text, role, timing, notes, ax
    save_data()
    st.session_state.editing = None

def save_col_meta(col_id, title, sub):
    meta = st.session_state.data.setdefault("col_meta", {}).setdefault(col_id, {})
    meta["title"] = title
    meta["sub"] = sub
    save_data()
    st.session_state.editing_col = None

def save_col_memo(col_id, key):
    meta = st.session_state.data.setdefault("col_meta", {}).setdefault(col_id, {})
    meta["memo"] = st.session_state[key]
    save_data()

def cancel_col_edit():
    st.session_state.editing_col = None

def set_editing(item_id):  st.session_state.editing = item_id
def cancel_editing():      st.session_state.editing = None
def update_vm(key, val):
    st.session_state.data[key] = val
    save_data()
    st.session_state[f"vm_ed_{key}"] = False
def cancel_vm(key):        st.session_state[f"vm_ed_{key}"] = False

def set_focus(item_id: str, rank: int) -> None:
    """아이템에 집중 순위(1,2,3) 설정. 같은 담당자의 기존 해당 순위는 해제."""
    data = st.session_state.data
    item = data["items"][item_id]
    role = item["role"]
    # 같은 담당자가 이미 해당 rank를 가지고 있으면 해제
    for iid, it in data["items"].items():
        if it.get("role") == role and it.get("focus_rank") == rank and iid != item_id:
            it["focus_rank"] = 0
    item["focus_rank"] = rank
    save_data()

def clear_focus(item_id: str) -> None:
    st.session_state.data["items"][item_id]["focus_rank"] = 0
    save_data()

def _ai_status(ai: dict) -> str:
    """액션아이템 상태 반환 (하위 호환: done 필드 → status 변환)"""
    if "status" in ai:
        return ai["status"]
    return "done" if ai.get("done", False) else "todo"

AI_STATUS_CYCLE = {"todo": "done", "in_progress": "done", "done": "todo"}
AI_STATUS_LABEL = {"todo": "⚪ 미착수", "in_progress": "✅ 완료", "done": "✅ 완료"}
AI_STATUS_SHORT = {"todo": "⚪", "in_progress": "✅", "done": "✅"}

def add_action_item(item_id: str, text: str) -> None:
    """집중 과제에 세부 액션아이템 추가"""
    item = st.session_state.data["items"][item_id]
    if "action_items" not in item:
        item["action_items"] = []
    ai_id = f"ai_{int(time.time()*1000)}"
    item["action_items"].append({"id": ai_id, "text": text, "status": "todo", "memo": ""})
    save_data()

def delete_action_item(item_id: str, ai_id: str) -> None:
    """액션아이템 삭제"""
    item = st.session_state.data["items"][item_id]
    item["action_items"] = [a for a in item.get("action_items", []) if a["id"] != ai_id]
    save_data()

def cycle_action_status(item_id: str, ai_id: str) -> None:
    """액션아이템 상태 순환: 미착수 → 진행중 → 완료 → 미착수"""
    item = st.session_state.data["items"][item_id]
    for ai in item.get("action_items", []):
        if ai["id"] == ai_id:
            cur = _ai_status(ai)
            ai["status"] = AI_STATUS_CYCLE.get(cur, "todo")
            ai.pop("done", None)
            break
    save_data()

def _on_action_memo(item_id: str, ai_id: str, key: str) -> None:
    """메모 저장 콜백"""
    item = st.session_state.data["items"][item_id]
    for ai in item.get("action_items", []):
        if ai["id"] == ai_id:
            ai["memo"] = st.session_state[key]
            break
    save_data()

def reset_all():
    st.session_state.data = copy.deepcopy(INITIAL_DATA)
    save_data()
    for k in [k for k in st.session_state if k != "data"]:
        del st.session_state[k]

# ── 담당자별 집계 ────────────────────────────────────────────────────────────
def get_items_by_person(data: dict) -> dict:
    result = {p: {"items": [], "prio": 0, "short": 0, "mid": 0, "total": 0}
              for p in PERSON_ORDER}
    for col_id, item_ids in data["columns"].items():
        for iid in item_ids:
            item = data["items"].get(iid)
            if not item:
                continue
            person = ROLE_TO_PERSON.get(item["role"], "미정")
            if person not in result:
                result[person] = {"items": [], "prio": 0, "short": 0, "mid": 0, "total": 0}
            result[person]["items"].append((col_id, iid))
            result[person]["total"] += 1
            if item.get("isPrio"):
                result[person]["prio"] += 1
            if item.get("timing") == "단기":
                result[person]["short"] += 1
            else:
                result[person]["mid"] += 1
    return result

# ── 카드 HTML ─────────────────────────────────────────────────────────────────
def card_html(item: dict, col_id: str) -> str:
    rc        = ROLE_CFG.get(item["role"], {"main":"#6A7698","prio":"#F0F2F5","dim":"#E0E4EA"})
    is_prio   = item["isPrio"]
    bg        = rc["prio"]  if is_prio else "#FFFFFF"
    border_c  = rc["main"]  if is_prio else "#D0D8E8"
    star_c    = rc["main"]  if is_prio else "#888888"
    text_c    = "#1A1A1A"
    fw        = "600"       if is_prio else "400"
    star      = "★"         if is_prio else "☆"
    tc        = T_CLR.get(item["timing"], "#888")
    role_bg   = rc["main"] + "18"
    tc_bg     = tc + "18"
    notes     = item.get("notes", "").strip()
    memo_icon = (
        f'<span style="margin-left:3px;font-size:15px;opacity:.55;flex-shrink:0">💬</span>'
    ) if notes else ""
    tip_html  = (
        f'<div class="ec-tip" style="display:none;position:absolute;left:0;top:100%;'
        f'background:#FFFFFF;border:1px solid #D0D8E8;border-radius:7px;'
        f'padding:9px 13px;font-size:15px;color:#1A1A1A;max-width:280px;'
        f'white-space:pre-wrap;word-break:keep-all;line-height:1.55;z-index:99999;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.12);margin-top:2px;pointer-events:none">'
        f'<span style="color:#074CBA;font-weight:700;font-size:15px">💬 메모</span>'
        f'<div style="margin-top:4px">{notes}</div></div>'
    ) if notes else ""

    focus_rank = item.get("focus_rank", 0)
    focus_badge = ""
    focus_border = ""
    if focus_rank in (1, 2, 3):
        focus_badge = (
            f'<span style="color:#074CBA;font-size:15px;font-weight:700;'
            f'background:rgba(7,76,186,.1);padding:2px 8px;border-radius:3px;flex-shrink:0">'
            f'📌{focus_rank}</span>'
        )
        focus_border = "box-shadow:0 0 0 1.5px rgba(7,76,186,.3);"

    return (
        f'<div data-item-id="{item["id"]}" data-col="{col_id}" data-timing="{item["timing"]}" style="'
        f'background:{bg};border-left:3.5px solid {border_c};border:1px solid #E8ECF2;'
        f'border-radius:7px;padding:12px 14px;margin-bottom:10px;user-select:none;{focus_border}">'
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:7px;flex-wrap:wrap">'
        f'<span style="color:{star_c};font-size:15px;flex-shrink:0;line-height:1">{star}</span>'
        f'{focus_badge}'
        f'<span style="color:{rc["main"]};font-size:15px;font-weight:700;'
        f'background:{role_bg};padding:2px 9px;border-radius:3px;flex-shrink:0">{item["role"]}</span>'
        f'{f"""<span style="color:#40C8F0;font-size:15px;font-weight:700;background:rgba(64,200,240,.15);padding:2px 9px;border-radius:3px;flex-shrink:0">AX</span>""" if item.get("ax") else ""}'
        f'{memo_icon}'
        f'<span style="margin-left:auto;flex-shrink:0;color:{tc};background:{tc_bg};'
        f'font-size:15px;font-weight:700;padding:2px 8px;border-radius:3px">{item["timing"]}</span>'
        f'</div>'
        f'<div style="font-size:15px;font-weight:{fw};color:{text_c};'
        f'line-height:1.55;word-break:keep-all">{item["text"]}</div>'
        f'{tip_html}'
        f'</div>'
    )

# ── 담당자 뷰용 카드 HTML (전략 태그 포함) ────────────────────────────────────
def card_html_person(item: dict, col_id: str, source_col: str) -> str:
    """담당자별 보기에서 사용 — 원래 전략 컬럼 태그가 추가됨"""
    rc        = ROLE_CFG.get(item["role"], {"main":"#6A7698","prio":"#2A3050","dim":"#4A5578"})
    is_prio   = item["isPrio"]
    bg        = rc["prio"]  if is_prio else "#FFFFFF"
    border_c  = rc["main"]  if is_prio else "#D0D8E8"
    star_c    = rc["main"]  if is_prio else "#888888"
    text_c    = "#1A1A1A"
    fw        = "600"       if is_prio else "400"
    star      = "★"         if is_prio else "☆"
    tc        = T_CLR.get(item["timing"], "#888")
    role_bg   = rc["main"] + "22"
    tc_bg     = tc + "22"
    notes     = item.get("notes", "").strip()
    memo_icon = (
        f'<span style="margin-left:3px;font-size:15px;opacity:.55;flex-shrink:0">💬</span>'
    ) if notes else ""
    tip_html  = (
        f'<div class="ec-tip" style="display:none;position:absolute;left:0;top:100%;'
        f'background:#E8ECF2;border:1px solid #C0C8D8;border-radius:7px;'
        f'padding:9px 13px;font-size:15px;color:#1A1A1A;max-width:280px;'
        f'white-space:pre-wrap;word-break:keep-all;line-height:1.55;z-index:99999;'
        f'box-shadow:0 6px 20px rgba(0,0,0,.55);margin-top:2px;pointer-events:none">'
        f'<span style="color:#074CBA;font-weight:700;font-size:15px">💬 메모</span>'
        f'<div style="margin-top:4px">{notes}</div></div>'
    ) if notes else ""

    # 전략 태그 (data col_meta 우선 참조 → COL_META fallback)
    custom_meta = st.session_state.data.get("col_meta", {}).get(source_col, {})
    src_meta = COL_META.get(source_col, {})
    src_title = custom_meta.get("title", src_meta.get("title", ""))
    strategy_tag = (
        f'<span style="color:#074CBA;font-size:15px;font-weight:700;'
        f'background:rgba(108,180,238,.15);padding:2px 8px;border-radius:3px;flex-shrink:0">'
        f'{src_title}</span>'
    )

    return (
        f'<div data-item-id="{item["id"]}" data-col="{col_id}" data-timing="{item["timing"]}" style="'
        f'background:{bg};border-left:3.5px solid {border_c};'
        f'border-radius:7px;padding:12px 14px;margin-bottom:10px;user-select:none;">'
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:7px;flex-wrap:wrap">'
        f'<span style="color:{star_c};font-size:15px;flex-shrink:0;line-height:1">{star}</span>'
        f'{strategy_tag}'
        f'{memo_icon}'
        f'</div>'
        f'<div style="font-size:15px;font-weight:{fw};color:{text_c};'
        f'line-height:1.55;word-break:keep-all">{item["text"]}</div>'
        f'{tip_html}'
        f'</div>'
    )

# ── 담당자별 컬럼 렌더링 ─────────────────────────────────────────────────────
def render_person_column(person: str) -> None:
    data = st.session_state.data
    role = {v: k for k, v in ROLE_TO_PERSON.items()}.get(person, "미정")
    rc = ROLE_CFG.get(role, {"main": "#6A7698"})
    person_stats = get_items_by_person(data)
    stats = person_stats.get(person, {"items": [], "prio": 0, "total": 0})

    # 헤더
    st.markdown(
        f'<div style="background:{rc["dim"]};border-left:4px solid {rc["main"]};border-radius:8px 8px 0 0;'
        f'padding:12px 16px 10px;margin-bottom:18px;">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between">'
        f'<div>'
        f'<div style="font-weight:700;font-size:19px;color:#1A1A1A;line-height:1.2">👤 {person}</div>'
        f'<div style="font-size:17px;color:{rc["main"]};margin-top:3px;font-weight:600">{role}</div>'
        f'</div>'
        f'<span style="font-size:17px;font-weight:700;color:{rc["main"]};background:rgba(0,0,0,.07);'
        f'padding:3px 10px;border-radius:12px;white-space:nowrap;margin-top:2px">'
        f'★{stats["prio"]} / {stats["total"]}</span>'
        f'</div></div>', unsafe_allow_html=True)

    item_list = stats["items"]
    short_items = [(cid, iid) for cid, iid in item_list
                   if data["items"].get(iid, {}).get("timing") == "단기"]
    mid_items = [(cid, iid) for cid, iid in item_list
                 if data["items"].get(iid, {}).get("timing") == "중장기"]

    col_id_person = f"person_{person}"

    if short_items:
        st.markdown(timing_divider("단기", T_CLR["단기"]), unsafe_allow_html=True)
        for source_col, iid in short_items:
            item = data["items"].get(iid)
            if item:
                st.markdown(card_html_person(item, col_id_person, source_col), unsafe_allow_html=True)
    if mid_items:
        st.markdown(timing_divider("중장기", T_CLR["중장기"]), unsafe_allow_html=True)
        for source_col, iid in mid_items:
            item = data["items"].get(iid)
            if item:
                st.markdown(card_html_person(item, col_id_person, source_col), unsafe_allow_html=True)
    if not item_list:
        st.markdown(
            '<p style="color:#666666;font-size:19px;text-align:center;'
            'padding:20px 8px;border:1px dashed #D0D8E8;border-radius:6px;margin:4px 0">과제 없음</p>',
            unsafe_allow_html=True)

# ── 아이템 렌더링 ─────────────────────────────────────────────────────────────
def render_item(item_id: str, col_id: str) -> None:
    data       = st.session_state.data
    item       = data["items"].get(item_id)
    if item is None: return
    edit_mode  = st.session_state.get("edit_mode", False)
    is_editing = st.session_state.get("editing") == item_id

    # ── 편집 폼 ──
    if is_editing:
        new_text = st.text_area("내용", value=item["text"], key=f"et_{item_id}", height=80)
        fc1, fc2 = st.columns(2)
        with fc1:
            new_role = st.selectbox("담당자", ROLES,
                index=ROLES.index(item["role"]) if item["role"] in ROLES else 0,
                key=f"er_{item_id}")
        with fc2:
            new_timing = st.selectbox("타이밍", TIMINGS,
                index=TIMINGS.index(item["timing"]), key=f"em_{item_id}")
        new_notes = st.text_area("메모", value=item.get("notes",""),
                                 key=f"en_{item_id}", height=60,
                                 placeholder="진행 상황, 참고 링크, 메모 등 자유롭게 기록…")
        new_ax = st.checkbox("AX (AI Transformation) 과제", value=item.get("ax", False),
                             key=f"eax_{item_id}")
        ac1, ac2 = st.columns(2)
        with ac1:
            st.button("💾 저장", key=f"sv_{item_id}", use_container_width=True,
                      on_click=save_item_edit,
                      args=(item_id, new_text, new_role, new_timing, new_notes, new_ax))
        with ac2:
            st.button("취소", key=f"cx_{item_id}", use_container_width=True,
                      on_click=cancel_editing)
        return

    # ── 카드 표시 ──
    st.markdown(card_html(item, col_id), unsafe_allow_html=True)

    # ── 편집 모드 액션 바 ──
    if edit_mode:
        st.markdown('<div class="edit-actions">', unsafe_allow_html=True)
        ab1, ab2, ab3, ab4 = st.columns([1, 1, 1, 5])
        with ab1:
            st.button("★" if item["isPrio"] else "☆", key=f"p_{item_id}",
                      help="우선순위 토글", on_click=toggle_priority, args=(item_id,))
        with ab2:
            st.button("✎", key=f"e_{item_id}", help="편집",
                      on_click=set_editing, args=(item_id,))
        with ab3:
            st.button("✕", key=f"d_{item_id}", help="삭제",
                      on_click=delete_item, args=(item_id,))
        with ab4:
            dest_map = {COL_META[k]["title"]: k for k in COL_ORDER if k != col_id}
            dest_map["📋 백로그"] = "backlog"
            sel = st.selectbox("이동 대상", ["이동 →"] + list(dest_map.keys()),
                               key=f"mv_{item_id}", label_visibility="collapsed")
            if sel != "이동 →":
                move_item(item_id, col_id, dest_map[sel])
                st.session_state.pop(f"mv_{item_id}", None)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ── 컬럼 헤더 HTML ────────────────────────────────────────────────────────────
def col_header_html(col_id: str, prio_cnt: int, total: int) -> str:
    cfg = COL_META[col_id]
    custom = st.session_state.data.get("col_meta", {}).get(col_id, {})
    title = custom.get("title", cfg["title"])
    sub   = custom.get("sub", cfg["sub"])
    memo  = custom.get("memo", "")
    dark  = cfg.get("dark_text", False)
    title_c = "#074CBA" if dark else "#fff"
    sub_c   = "rgba(7,76,186,.6)" if dark else "rgba(255,255,255,.75)"
    bold_c  = "#074CBA" if dark else "#fff"
    badge_bg= "rgba(7,76,186,.15)" if dark else "rgba(255,255,255,.2)"
    badge_c = "#074CBA" if dark else "#fff"
    # [대상] 부분을 볼드체로 변환
    sub_html = re.sub(r'\[([^\]]+)\]', lambda m: f'<b style="color:{bold_c};font-weight:700">[{m.group(1)}]</b>', sub)
    # 메모 있으면 💬 표시 + 호버 툴팁
    import html as _html
    memo_esc = _html.escape(memo, quote=True) if memo else ""
    memo_dot = f'<span style="margin-left:4px;font-size:11px;opacity:.6">💬</span>' if memo else ""
    tooltip_attr = f' data-memo-tip="{memo_esc}"' if memo else ""
    tooltip_css = (
        '<style>'
        '[data-memo-tip]{position:relative}'
        '[data-memo-tip]:hover::after{'
        'content:attr(data-memo-tip);position:absolute;top:calc(100% + 6px);left:0;'
        'background:#1a1a2e;color:#fff;padding:8px 12px;border-radius:6px;'
        'font-size:12px;line-height:1.5;white-space:pre-wrap;max-width:260px;min-width:120px;'
        'z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.25);pointer-events:none}'
        '</style>'
    ) if memo else ""
    # ▼ 토글 버튼
    is_open = st.session_state.get(f"col_memo_open_{col_id}", False)
    arrow = "▲" if is_open else "▼"
    arrow_html = (
        f'{tooltip_css}'
        f'<span data-memo-toggle="{col_id}"{tooltip_attr} style="color:{sub_c};font-size:11px;cursor:pointer;'
        f'padding:2px 6px;border-radius:3px;background:rgba(7,76,186,.08);'
        f'user-select:none;flex-shrink:0">{arrow}{memo_dot}</span>'
    )
    mb = "0" if is_open else "18px"
    br = "8px 8px 0 0" if is_open else "8px 8px 0 0"
    return (
        f'<div data-col-edit="{col_id}" style="background:{cfg["color"]};border-radius:{br};'
        f'padding:12px 16px 10px;margin-bottom:{mb};cursor:pointer;">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between">'
        f'<div style="flex:1">'
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<span style="font-weight:700;font-size:18px;color:{title_c};line-height:1.3">{title}</span>'
        f'{arrow_html}'
        f'</div>'
        f'<div style="font-size:13px;color:{sub_c};margin-top:3px">{sub_html}</div>'
        f'</div>'
        f'<span style="font-size:14px;font-weight:700;color:{badge_c};background:{badge_bg};'
        f'padding:3px 10px;border-radius:12px;white-space:nowrap;margin-top:2px">'
        f'★{prio_cnt} / {total}</span>'
        f'</div></div>'
    )

# ── 타이밍 구분선 ─────────────────────────────────────────────────────────────
def timing_divider(label: str, color: str) -> str:
    return (
        f'<div style="color:{color};font-size:19px;font-weight:700;'
        f'display:flex;align-items:center;gap:6px;margin:14px 0 8px;padding:0 2px;">'
        f'<span>● {label}</span>'
        f'<span style="flex:1;height:1px;background:{color};opacity:.25;display:block"></span>'
        f'</div>'
    )

# ── 컬럼 렌더링 ───────────────────────────────────────────────────────────────
def render_column(col_id: str) -> None:
    data      = st.session_state.data
    item_ids  = data["columns"].get(col_id, [])
    prio_cnt  = sum(1 for i in item_ids if data["items"].get(i,{}).get("isPrio"))
    edit_mode = st.session_state.get("edit_mode", False)

    # 컬럼 헤더 편집 모드
    if st.session_state.get("editing_col") == col_id:
        cfg = COL_META[col_id]
        custom = data.get("col_meta", {}).get(col_id, {})
        cur_title = custom.get("title", cfg["title"])
        cur_sub   = custom.get("sub", cfg["sub"])
        st.markdown(
            f'<div style="background:{cfg["color"]};border-radius:8px 8px 0 0;'
            f'padding:8px 10px 6px;margin-bottom:4px;">'
            f'<div style="font-size:15px;color:#074CBA;font-weight:600">헤더 편집</div></div>',
            unsafe_allow_html=True)
        new_title = st.text_input("제목", value=cur_title, key=f"cht_{col_id}")
        new_sub   = st.text_input("부제", value=cur_sub,   key=f"chs_{col_id}")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.button("💾 저장", key=f"chsv_{col_id}", use_container_width=True,
                      on_click=save_col_meta, args=(col_id, new_title, new_sub))
        with ec2:
            st.button("취소", key=f"chcx_{col_id}", use_container_width=True,
                      on_click=cancel_col_edit)
        return

    st.markdown(col_header_html(col_id, prio_cnt, len(item_ids)), unsafe_allow_html=True)

    # ── 전략 메모 ──
    col_memo = data.get("col_meta", {}).get(col_id, {}).get("memo", "")
    memo_toggle_key = f"col_memo_open_{col_id}"
    is_memo_open = st.session_state.get(memo_toggle_key, False)
    any_memo_open = any(st.session_state.get(f"col_memo_open_{c}", False) for c in COL_ORDER)
    if is_memo_open:
        st.text_area(
            "전략 메모",
            value=col_memo,
            placeholder="전략 관련 메모를 자유롭게 작성…",
            key=f"col_memo_val_{col_id}",
            height=120,
            label_visibility="collapsed",
            on_change=save_col_memo,
            args=(col_id, f"col_memo_val_{col_id}"),
        )
    elif any_memo_open:
        # 다른 컬럼 메모가 열려 있으면 동일 높이 스페이서 삽입
        st.markdown('<div style="height:120px"></div>', unsafe_allow_html=True)
    # DnD 드롭 타겟 마커 + 숨겨진 토글 버튼 (메모 뒤에 배치 → 간격 영향 없음)
    st.markdown(
        f'<div data-col-marker="{col_id}" style="height:0;overflow:hidden;font-size:0"> </div>',
        unsafe_allow_html=True)
    def _toggle_memo(cid):
        k = f"col_memo_open_{cid}"
        st.session_state[k] = not st.session_state.get(k, False)
    st.markdown(f'<div data-memo-btn="{col_id}" style="height:0;overflow:hidden;font-size:0"></div>',
                unsafe_allow_html=True)
    st.button(f"_mt_{col_id}", key=f"memo_btn_{col_id}",
              on_click=_toggle_memo, args=(col_id,), type="secondary")

    short_ids = [i for i in item_ids if data["items"].get(i,{}).get("timing") == "단기"]
    mid_ids   = [i for i in item_ids if data["items"].get(i,{}).get("timing") == "중장기"]

    if short_ids:
        st.markdown(timing_divider("단기", T_CLR["단기"]), unsafe_allow_html=True)
        for i in short_ids: render_item(i, col_id)
    if mid_ids:
        st.markdown(timing_divider("중장기", T_CLR["중장기"]), unsafe_allow_html=True)
        for i in mid_ids: render_item(i, col_id)
    if not item_ids:
        st.markdown(
            '<p style="color:#666666;font-size:19px;text-align:center;'
            'padding:20px 8px;border:1px dashed #D0D8E8;border-radius:6px;margin:4px 0">과제 없음</p>',
            unsafe_allow_html=True)

    if edit_mode:
        add_key = f"add_open_{col_id}"
        if st.session_state.get(add_key):
            with st.form(key=f"af_{col_id}", clear_on_submit=True):
                f1, f2 = st.columns(2)
                with f1: nr = st.selectbox("담당자", ROLES, key=f"nr_{col_id}")
                with f2: nt = st.selectbox("타이밍", TIMINGS, key=f"nt_{col_id}")
                ntx = st.text_input("내용", key=f"ntx_{col_id}", placeholder="액션아이템 내용 입력…")
                a1, a2 = st.columns(2)
                with a1: sub = st.form_submit_button("✚ 추가", use_container_width=True)
                with a2: can = st.form_submit_button("취소",   use_container_width=True)
                if sub and ntx.strip():
                    add_item(col_id, nr, nt, ntx.strip())
                    st.session_state[add_key] = False; st.rerun()
                if can:
                    st.session_state[add_key] = False; st.rerun()
        else:
            st.markdown('<div style="margin-top:6px"></div>', unsafe_allow_html=True)
            if st.button("＋ 과제 추가", key=f"ab_{col_id}", use_container_width=True):
                st.session_state[add_key] = True; st.rerun()

# ── DnD + 더블클릭 JS (iframe에서 실행, parent DOM 조작) ─────────────────
_DND_IFRAME = """<script>
(function() {
  var par = window.parent, pd;
  try { pd = par.document; } catch(e) { return; }

  var dragId = null, dragFrom = null;

  function nav(url) {
    try { par.location.href = url; } catch(e) {
      var s = pd.createElement('script');
      s.textContent = 'location.href="' + url + '"';
      pd.head.appendChild(s); s.remove();
    }
  }

  function mkUrl(params) {
    var base = par.location.href.split('?')[0] + '?';
    var parts = [];
    for (var k in params) parts.push(k + '=' + encodeURIComponent(params[k]));
    return base + parts.join('&');
  }

  function setupDnD() {
    pd.querySelectorAll('[data-col-marker]').forEach(function(m) {
      var col = m.getAttribute('data-col-marker');
      var el = m.parentElement;
      while (el) {
        if (el.getAttribute && el.getAttribute('data-testid') === 'column') {
          if (!el.__dz) { el.__dz=1; el.setAttribute('data-drop-col', col); addDrop(el, col); }
          break;
        }
        el = el.parentElement;
      }
    });

    pd.querySelectorAll('[data-drop-col]').forEach(function(z) {
      if (z.__dz) return; z.__dz=1;
      addDrop(z, z.getAttribute('data-drop-col'));
    });

    pd.querySelectorAll('[data-col-edit]').forEach(function(h) {
      if (h.__ce) return; h.__ce=1;
      h.addEventListener('dblclick', function(e) {
        e.preventDefault(); e.stopPropagation();
        nav(mkUrl({col_edit: h.getAttribute('data-col-edit')}));
      });
    });

    // 숨겨진 버튼 찾아서 숨기고 참조 저장 (공용)
    var HIDE_CSS = 'position:fixed!important;left:-9999px!important;height:0!important;max-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;pointer-events:auto!important';
    function hideAndStore(selector) {
      pd.querySelectorAll(selector).forEach(function(m) {
        if (m.__hb) return; m.__hb=1;
        // 마커 자신의 Streamlit 컨테이너도 축소
        var mp = m.parentElement;
        while (mp && mp !== pd.body) {
          if (mp.getAttribute && (mp.getAttribute('data-testid') === 'element-container' || mp.getAttribute('data-testid') === 'stVerticalBlockBorderWrapper')) {
            mp.style.cssText = 'height:0!important;max-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important';
            break;
          }
          if (mp.classList && mp.classList.contains('element-container')) {
            mp.style.cssText = 'height:0!important;max-height:0!important;overflow:hidden!important;margin:0!important;padding:0!important';
            break;
          }
          mp = mp.parentElement;
        }
        // 버튼 컨테이너 숨기기 + 참조 저장
        var el = m;
        while (el) {
          el = el.parentElement;
          if (!el) break;
          var next = el.nextElementSibling;
          if (next && next.querySelector('button')) {
            next.style.cssText = HIDE_CSS;
            m._stBtn = next.querySelector('button');
            break;
          }
        }
      });
    }
    hideAndStore('[data-memo-btn]');
    hideAndStore('[data-ai-memo-btn]');
    hideAndStore('[data-ai-del-btn]');
    hideAndStore('[data-focus-toggle-btn]');

    // 클릭 → 숨겨진 버튼 포워딩 (공용)
    function forwardClick(triggerSel, attr, markerPrefix) {
      pd.querySelectorAll(triggerSel).forEach(function(btn) {
        if (btn.__fc) return; btn.__fc=1;
        btn.addEventListener('click', function(e) {
          e.preventDefault(); e.stopPropagation();
          var id = btn.getAttribute(attr);
          var marker = pd.querySelector('[' + markerPrefix + '="' + id + '"]');
          if (marker && marker._stBtn) marker._stBtn.click();
        });
      });
    }
    forwardClick('[data-memo-toggle]', 'data-memo-toggle', 'data-memo-btn');
    forwardClick('[data-ai-memo]', 'data-ai-memo', 'data-ai-memo-btn');
    forwardClick('[data-ai-del]', 'data-ai-del', 'data-ai-del-btn');
    forwardClick('[data-focus-toggle]', 'data-focus-toggle', 'data-focus-toggle-btn');

    pd.querySelectorAll('[data-item-id]').forEach(function(c) {
      if (c.__dd) return; c.__dd=1;
      c.setAttribute('draggable', 'true');

      c.addEventListener('dragstart', function(e) {
        dragId = c.getAttribute('data-item-id');
        dragFrom = c.getAttribute('data-col');
        e.dataTransfer.effectAllowed = 'move';
        setTimeout(function(){ c.style.opacity='0.35'; }, 0);
      });
      c.addEventListener('dragend', function() {
        c.style.opacity=''; dragId=null; dragFrom=null;
      });
      c.addEventListener('dblclick', function(e) {
        e.preventDefault(); e.stopPropagation();
        nav(mkUrl({edit_id: c.getAttribute('data-item-id')}));
      });
      c.addEventListener('dragover', function(e) {
        if (dragId && dragId !== c.getAttribute('data-item-id')) {
          e.preventDefault(); e.stopPropagation();
          c.style.borderTop='2px solid rgba(7,76,186,.7)';
        }
      });
      c.addEventListener('dragleave', function(){ c.style.borderTop=''; });
      c.addEventListener('drop', function(e) {
        c.style.borderTop='';
        var targetId = c.getAttribute('data-item-id');
        var to = c.getAttribute('data-col');
        var toTiming = c.getAttribute('data-timing') || '';
        if (dragId && dragId !== targetId) {
          e.preventDefault(); e.stopPropagation();
          nav(mkUrl({mv_id:dragId, mv_from:dragFrom, mv_to:to, mv_before:targetId, mv_timing:toTiming}));
        }
      });
    });
  }

  function addDrop(z, col) {
    z.addEventListener('dragover', function(e) {
      e.preventDefault(); e.dataTransfer.dropEffect='move';
      z.style.outline='2px dashed rgba(7,76,186,.5)';
      z.style.borderRadius='6px';
    });
    z.addEventListener('dragleave', function(e) {
      if (!z.contains(e.relatedTarget)) z.style.outline='';
    });
    z.addEventListener('drop', function(e) {
      z.style.outline='';
      if (dragId) {
        e.preventDefault();
        nav(mkUrl({mv_id:dragId, mv_from:dragFrom, mv_to:col}));
      }
    });
  }

  function equalizeElements(selector) {
    var blocks = pd.querySelectorAll('[data-testid="stHorizontalBlock"]');
    blocks.forEach(function(block) {
      var els = block.querySelectorAll(selector);
      if (els.length < 2) return;
      els.forEach(function(e) { e.style.minHeight = ''; });
      var rows = {};
      els.forEach(function(e) {
        var top = Math.round(e.getBoundingClientRect().top / 10) * 10;
        if (!rows[top]) rows[top] = [];
        rows[top].push(e);
      });
      for (var k in rows) {
        var r = rows[k]; if (r.length < 2) continue;
        var maxH = 0;
        r.forEach(function(e) { maxH = Math.max(maxH, e.offsetHeight); });
        if (maxH > 0) r.forEach(function(e) { e.style.minHeight = maxH + 'px'; });
      }
    });
  }

  function equalizeAll() {
    equalizeElements('[data-col-edit]');
    equalizeElements('[data-item-id]');
  }

  setupDnD();
  equalizeAll();
  var t=null;
  new MutationObserver(function(){
    clearTimeout(t); t=setTimeout(function(){ setupDnD(); equalizeAll(); }, 200);
  }).observe(pd.body, {childList:true, subtree:true});
})();
</script>"""

# ── 메인 ─────────────────────────────────────────────────────────────────────
def main() -> None:
    if "data"      not in st.session_state: st.session_state.data      = load_data()
    if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
    if "editing"   not in st.session_state: st.session_state.editing   = None

    # ── 드래그 이동 쿼리 파람 처리 ───────────────────────────────────────────
    qp = st.experimental_get_query_params()
    if "mv_id" in qp:
        mv_id     = qp.get("mv_id",     [""])[0]
        mv_from   = qp.get("mv_from",   [""])[0]
        mv_to     = qp.get("mv_to",     [""])[0]
        mv_before = qp.get("mv_before", [""])[0]
        mv_timing = qp.get("mv_timing", [""])[0]
        all_cols = list(COL_ORDER) + ["backlog"]
        if (mv_id in st.session_state.data["items"]
                and mv_from in all_cols and mv_to in all_cols
                and mv_id != mv_before):
            move_item(mv_id, mv_from, mv_to, mv_before, mv_timing)
        st.experimental_set_query_params()

    # ── 더블클릭 편집 쿼리 파람 처리 ─────────────────────────────────────────
    if "edit_id" in qp:
        eid = qp.get("edit_id", [""])[0]
        if eid in st.session_state.data["items"]:
            st.session_state.editing   = eid
            st.session_state.edit_mode = True
        st.experimental_set_query_params()

    # ── 컬럼 헤더 더블클릭 편집 쿼리 파람 처리 ────────────────────────────────
    if "col_edit" in qp:
        ce = qp.get("col_edit", [""])[0]
        all_cols = list(COL_ORDER) + ["backlog"]
        if ce in all_cols:
            st.session_state.editing_col = ce
        st.experimental_set_query_params()

    data      = st.session_state.data
    edit_mode = st.session_state.edit_mode

    # ── 글로벌 CSS: 숨겨진 마커/버튼 컨테이너 간격 제거 ───────────────────
    st.markdown("""<style>
    /* 숨겨진 마커·버튼 컨테이너 축소 */
    div:has(> div > [data-ai-memo-btn]),
    div:has(> div > [data-ai-del-btn]),
    div:has(> div > [data-focus-toggle-btn]),
    div:has(> div > [data-memo-btn]) {
        height: 0 !important; max-height: 0 !important;
        overflow: hidden !important; margin: 0 !important; padding: 0 !important;
    }
    /* 전략 메모 textarea 높이 고정 + 리사이즈 금지 */
    [class*="stTextArea"] textarea {
        height: 120px !important;
        min-height: 120px !important;
        max-height: 120px !important;
        resize: none !important;
    }
    </style>""", unsafe_allow_html=True)

    # ── 헤더 ─────────────────────────────────────────────────────────────────
    view_mode = st.session_state.get("view_mode", "strategy")  # "strategy" | "person"
    h1, h2, h3, h4 = st.columns([7, 1.4, 1.1, 0.9])
    with h1:
        st.markdown(
            '<div style="padding:4px 0 2px">'
            f'{_LOGO_IMG}<span style="font-size:30px;font-weight:500;color:#074CBA;letter-spacing:-0.5px">에이블캠퍼스 전략 대시보드</span>'
            '&nbsp;&nbsp;<span style="font-size:19px;color:#333333">AX 팀 실행 과제 관리</span>'
            '</div>', unsafe_allow_html=True)
    with h2:
        view_lbl = "📊 전략별 보기" if view_mode == "person" else "👤 담당자별 보기"
        if st.button(view_lbl, key="view_toggle", use_container_width=True):
            st.session_state.view_mode = "strategy" if view_mode == "person" else "person"
            st.rerun()
    with h3:
        lbl = "✓ 편집 중" if edit_mode else "✏ 편집 모드"
        if st.button(lbl, key="edit_toggle", use_container_width=True):
            st.session_state.edit_mode = not edit_mode
            st.session_state.editing   = None
            st.rerun()
    with h4:
        if st.button("↺ 초기화", key="reset_btn", use_container_width=True):
            st.session_state._confirm = True; st.rerun()

    if st.session_state.get("_confirm"):
        st.warning("⚠️ 초기 데이터로 되돌립니다. 계속할까요?")
        c1, c2, _ = st.columns([1,1,6])
        with c1:
            if st.button("✓ 확인", key="conf_yes"): reset_all(); st.rerun()
        with c2:
            if st.button("✕ 취소", key="conf_no"):
                st.session_state._confirm = False; st.rerun()

    if edit_mode:
        st.markdown(
            '<div style="background:#E6F7ED;border:1px solid #B0DBBF;border-radius:6px;'
            'padding:6px 14px;margin-bottom:6px;font-size:15px;color:#2E7D32">'
            '✏ 편집 모드 ON — '
            '<span style="font-weight:400;color:#4A8A50">'
            '★/☆ 우선순위 · ✎ 내용편집 · 이동→ 컬럼이동 · ✕ 삭제 · ＋ 과제추가 | 더블클릭으로도 편집 가능'
            '</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-size:19px;color:#555555;padding:1px 0 5px">'
            '💡 카드를 드래그해 컬럼 이동 · 더블클릭하면 편집'
            '</div>', unsafe_allow_html=True)

    # ── 비전 / 미션 + 담당자 범례 (하나의 박스) ──────────────────────────────
    st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)

    LEGEND_ITEMS = [
        ("백수경(마케팅)",        ROLE_CFG["마케팅"]["main"]),
        ("김보현(영업)",          ROLE_CFG["영업"]["main"]),
        ("이기혁(교육설계)",      ROLE_CFG["교육설계"]["main"]),
        ("남동현(교육 콘텐츠/AX)", ROLE_CFG["강의자료"]["main"]),
        ("박지원(교육운영)",      ROLE_CFG["교육운영"]["main"]),
    ]
    legend_parts = "".join([
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:22px">'
        f'<span style="width:10px;height:10px;border-radius:3px;background:{clr};flex-shrink:0"></span>'
        f'<span style="font-size:15px;color:#1A1A1A">{name}</span></span>'
        for name, clr in LEGEND_ITEMS
    ])

    # 편집 모드가 아닐 때: 비전/미션 + 범례를 하나의 HTML 블록으로
    vm_editing = edit_mode and (st.session_state.get("vm_ed_vision") or st.session_state.get("vm_ed_mission"))
    if not vm_editing:
        vm_box = (
            f'<div style="background:#F5F7FA;border:1px solid #D0D8E8;border-radius:10px;padding:16px 20px 14px;margin-bottom:8px">'
            f'<div style="display:flex;gap:20px;flex-wrap:wrap">'
            f'<div style="flex:1;min-width:280px;display:flex;align-items:center;gap:10px;'
            f'background:#CBE2FF;border-radius:8px;padding:12px 14px">'
            f'<span style="color:#074CBA;font-size:17px;font-weight:700;'
            f'background:rgba(7,76,186,.15);padding:4px 13px;border-radius:3px;'
            f'flex-shrink:0">비전</span>'
            f'<span style="font-size:17px;color:#1A1A1A;line-height:1.55;font-weight:600">{data["vision"]}</span>'
            f'</div>'
            f'<div style="flex:1;min-width:280px;display:flex;align-items:center;gap:10px;'
            f'background:#CBE2FF;border-radius:8px;padding:12px 14px">'
            f'<span style="color:#074CBA;font-size:17px;font-weight:700;'
            f'background:rgba(7,76,186,.15);padding:4px 13px;border-radius:3px;'
            f'flex-shrink:0">미션</span>'
            f'<span style="font-size:17px;color:#1A1A1A;line-height:1.55;font-weight:600">{data["mission"]}</span>'
            f'</div>'
            f'</div>'
            f'<div style="border-top:1px solid #D0D8E8;margin-top:12px;padding-top:10px;'
            f'display:flex;align-items:center;flex-wrap:wrap;gap:4px">'
            f'<span style="font-size:15px;color:#333333;margin-right:12px;font-weight:700">담당자</span>'
            f'{legend_parts}</div>'
            f'</div>'
        )
        st.markdown(vm_box, unsafe_allow_html=True)
        if edit_mode:
            ve1, ve2, _ = st.columns([1,1,6])
            with ve1:
                if st.button("✎ 비전 편집", key="ve_vision"):
                    st.session_state["vm_ed_vision"] = True; st.rerun()
            with ve2:
                if st.button("✎ 미션 편집", key="ve_mission"):
                    st.session_state["vm_ed_mission"] = True; st.rerun()
    else:
        # 편집 중일 때는 기존 방식 (위젯 필요)
        vm_c1, vm_c2 = st.columns(2, gap="small")
        for (key, label), col in zip([("vision","비전"), ("mission","미션")], [vm_c1, vm_c2]):
            with col:
                vm_ed_key = f"vm_ed_{key}"
                if st.session_state.get(vm_ed_key):
                    new_val = st.text_area(f"{label} 편집", value=data[key], key=f"vm_a_{key}",
                                           height=60, label_visibility="collapsed")
                    vc1, vc2, _ = st.columns([1,1,4])
                    with vc1:
                        st.button("💾 저장", key=f"vs_{key}", use_container_width=True,
                                  on_click=update_vm, args=(key, new_val))
                    with vc2:
                        st.button("취소", key=f"vc_{key}", use_container_width=True,
                                  on_click=cancel_vm, args=(key,))
                else:
                    inner_html = (
                        f'<div style="background:#F5F7FA;border-radius:8px;padding:12px 16px;'
                        f'display:flex;align-items:flex-start;gap:10px;min-height:48px">'
                        f'<span style="color:#074CBA;font-size:17px;font-weight:700;'
                        f'background:rgba(7,76,186,.12);padding:4px 13px;border-radius:3px;'
                        f'flex-shrink:0;margin-top:2px">{label}</span>'
                        f'<span style="font-size:17px;color:#1A1A1A;line-height:1.55">{data[key]}</span>'
                        f'</div>'
                    )
                    st.markdown(inner_html, unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # ── 담당자별 집중 과제 (담당자별 보기에서만) ──────────────────────────────────
    if view_mode == "person":
      person_role_map = {v: k for k, v in ROLE_TO_PERSON.items()}
      person_items_all = get_items_by_person(data)

      # 집중 과제 수집 (focus_rank > 0)
      focus_by_person = {p: [] for p in PERSON_ORDER}
      for p in PERSON_ORDER:
          for col_id, iid in person_items_all[p]["items"]:
              it = data["items"].get(iid, {})
              if it.get("focus_rank", 0) in (1, 2, 3):
                  focus_by_person[p].append((it["focus_rank"], iid, it, col_id))
          focus_by_person[p].sort(key=lambda x: x[0])

      unset_persons = [p for p in PERSON_ORDER if len(focus_by_person[p]) == 0]

      # 헤더
      st.markdown(
          '<div style="background:#F5F7FA;border:1px solid #D0D8E8;border-radius:10px;'
          'padding:14px 16px 10px;margin-bottom:10px">'
          '<div style="display:flex;align-items:center;justify-content:space-between">'
          '<span style="font-size:15px;font-weight:700;color:#074CBA">📌 담당자별 현재 집중 과제</span>'
          + (f'<span style="font-size:19px;color:#FF6B6B;font-weight:600">'
             f'⚠ 미설정: {", ".join(unset_persons)}</span>' if unset_persons else
             '<span style="font-size:19px;color:#4CCE8A;font-weight:600">✅ 전원 설정 완료</span>')
          + '</div></div>', unsafe_allow_html=True)

      focus_cols = st.columns(len(PERSON_ORDER), gap="small")
      for col_ui, person in zip(focus_cols, PERSON_ORDER):
          with col_ui:
              role = person_role_map.get(person, "미정")
              rc = ROLE_CFG.get(role, {"main": "#6A7698"})

              # 미니 헤더
              st.markdown(
                  f'<div style="background:{rc["dim"]};border-left:3px solid {rc["main"]};border-radius:6px 6px 0 0;'
                  f'padding:8px 12px 6px">'
                  f'<span style="font-weight:700;font-size:17px;color:#1A1A1A">{person}</span>'
                  f'<span style="font-size:17px;color:{rc["main"]};margin-left:6px;font-weight:600">{role}</span>'
                  f'</div>', unsafe_allow_html=True)

              if edit_mode:
                  # ── 편집 모드: 체크리스트 ──
                  all_items = person_items_all.get(person, {}).get("items", [])
                  checked_ids = []
                  for col_id, iid in all_items:
                      it = data["items"].get(iid, {})
                      is_focused = it.get("focus_rank", 0) > 0
                      val = st.checkbox(
                          it.get("text", iid),
                          value=is_focused,
                          key=f"fc_{person}_{iid}",
                      )
                      if val:
                          checked_ids.append(iid)
                  if not all_items:
                      st.markdown('<span style="color:#666666;font-size:19px">과제 없음</span>',
                                  unsafe_allow_html=True)
                  if st.button("💾 저장", key=f"fc_save_{person}", use_container_width=True):
                      # 기존 focus 전부 해제
                      for col_id, iid in all_items:
                          data["items"][iid]["focus_rank"] = 0
                      # 체크된 것만 순서대로 1,2,3...
                      for rank, iid in enumerate(checked_ids, 1):
                          data["items"][iid]["focus_rank"] = rank
                      save_data()
                      st.rerun()
              else:
                  # ── 일반 모드: 텍스트로 표시 + 세부 액션아이템 ──
                  items_list = focus_by_person[person]
                  if items_list:
                      for rank, iid, it, src_col in items_list:
                          src_meta = COL_META.get(src_col, {})
                          src_title = data.get("col_meta", {}).get(src_col, {}).get("title", src_meta.get("title", ""))

                          # 액션아이템 진행률
                          action_items = it.get("action_items", [])
                          done_count = sum(1 for a in action_items if _ai_status(a) == "done")
                          total_count = len(action_items)
                          progress_html = ""
                          if total_count > 0:
                              pct = int(done_count / total_count * 100)
                              bar_color = "#4CCE8A" if pct == 100 else "#074CBA"
                              status_txt = f"{done_count}/{total_count}"
                              progress_html = (
                                  f'<div style="display:flex;align-items:center;gap:6px;margin-top:6px">'
                                  f'<div style="flex:1;height:4px;background:#E8E8E8;border-radius:2px;overflow:hidden">'
                                  f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:2px"></div></div>'
                                  f'<span style="font-size:11px;color:#888;white-space:nowrap">{status_txt}</span>'
                                  f'</div>'
                              )

                          is_expanded = st.session_state.get("expanded_focus") == iid
                          arrow = "▲" if is_expanded else "▼"
                          arrow_html = (
                              f'<span data-focus-toggle="{iid}" style="cursor:pointer;font-size:10px;'
                              f'color:#888;padding:1px 4px;border-radius:3px;'
                              f'background:rgba(7,76,186,.08)">{arrow}</span>'
                          )
                          # 세부항목 HTML (펼침 시 카드 안에 포함)
                          items_section = ""
                          if is_expanded and action_items:
                              rows_html = []
                              for idx, ai in enumerate(action_items):
                                  memo = ai.get("memo", "")
                                  memo_html = (
                                      f'<div style="font-size:11px;color:#888;margin-top:2px;padding-left:14px">'
                                      f'┗ {memo}</div>'
                                  ) if memo else ""
                                  memo_icon = '<span style="font-size:10px;opacity:.5;margin-left:2px">💬</span>' if memo else ""
                                  is_memo_editing = st.session_state.get(f"ai_memo_edit_{ai['id']}", False)
                                  memo_btn_icon = "접기" if is_memo_editing else "메모"
                                  border_top = 'border-top:1px solid #EEF0F4;' if idx > 0 else ''
                                  rows_html.append(
                                      f'<div style="{border_top}padding:5px 0">'
                                      f'<div style="display:flex;align-items:center;gap:6px">'
                                      f'<span style="color:#B0B8C8;font-size:11px;flex-shrink:0">•</span>'
                                      f'<span style="font-size:13px;font-weight:500;color:#1A1A1A;'
                                      f'flex:1;word-break:keep-all">{ai["text"]}{memo_icon}</span>'
                                      f'<span data-ai-memo="{ai["id"]}" style="cursor:pointer;font-size:10px;'
                                      f'color:#666;background:#E0E4EA;padding:2px 8px;'
                                      f'border-radius:8px;font-weight:600;white-space:nowrap">'
                                      f'{memo_btn_icon}</span>'
                                      f'<span data-ai-del="{ai["id"]}" style="cursor:pointer;font-size:11px;'
                                      f'color:#C0C0C0;padding:0 2px" title="삭제">✕</span>'
                                      f'</div>'
                                      f'{memo_html}'
                                      f'</div>'
                                  )
                              items_section = (
                                  f'<div style="border-top:1px solid #E8ECF2;margin-top:8px;padding-top:4px">'
                                  f'{"".join(rows_html)}'
                                  f'</div>'
                              )
                          # 카드 + 세부항목 하나의 HTML
                          st.markdown(
                              f'<div style="background:#FFFFFF;border-left:3px solid #074CBA;'
                              f'border-radius:5px;padding:8px 10px;margin-top:4px;'
                              f'box-shadow:0 1px 4px rgba(0,0,0,.06)">'
                              f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:4px">'
                              f'<span style="color:#074CBA;font-size:17px;font-weight:700">#{rank}</span>'
                              f'<span style="color:#074CBA;font-size:17px;font-weight:600;'
                              f'background:rgba(108,180,238,.15);padding:1px 6px;border-radius:3px">{src_title}</span>'
                              f'{arrow_html}'
                              f'</div>'
                              f'<div style="font-size:15px;color:#1A1A1A;font-weight:500;'
                              f'line-height:1.4;word-break:keep-all">{it["text"]}</div>'
                              f'{progress_html}'
                              f'{items_section}'
                              f'</div>', unsafe_allow_html=True)
                          # 새 액션아이템 추가 (카드 바로 다음 — 간격 최소)
                          if is_expanded:
                              if st.session_state.get(f"clear_ai_{iid}"):
                                  st.session_state[f"new_ai_{iid}"] = ""
                                  del st.session_state[f"clear_ai_{iid}"]
                              ai_inp, ai_btn = st.columns([4, 1])
                              with ai_inp:
                                  new_ai_text = st.text_input(
                                      "새 액션아이템",
                                      placeholder="액션아이템 입력…",
                                      key=f"new_ai_{iid}",
                                      label_visibility="collapsed",
                                  )
                              with ai_btn:
                                  if st.button("✚", key=f"ai_add_{iid}", use_container_width=True):
                                      if new_ai_text.strip():
                                          add_action_item(iid, new_ai_text.strip())
                                          st.session_state[f"clear_ai_{iid}"] = True
                                          st.rerun()
                          # 숨겨진 버튼들 (입력 칸 뒤에 배치 → 간격 영향 없음)
                          def _toggle_focus(item_id):
                              if st.session_state.get("expanded_focus") == item_id:
                                  st.session_state.expanded_focus = None
                              else:
                                  st.session_state.expanded_focus = item_id
                          st.markdown(f'<div data-focus-toggle-btn="{iid}" style="height:0;overflow:hidden;font-size:0"></div>',
                                      unsafe_allow_html=True)
                          st.button(f"_ft_{iid}", key=f"focus_detail_{iid}",
                                    on_click=_toggle_focus, args=(iid,))
                          if is_expanded and action_items:
                              editing_ai = None
                              for ai in action_items:
                                  def _toggle_ai_memo(aid):
                                      k = f"ai_memo_edit_{aid}"
                                      st.session_state[k] = not st.session_state.get(k, False)
                                  def _delete_ai(itm_id, aid):
                                      delete_action_item(itm_id, aid)
                                  st.markdown(f'<div data-ai-memo-btn="{ai["id"]}" style="height:0;overflow:hidden;font-size:0"></div>',
                                              unsafe_allow_html=True)
                                  st.button(f"_am_{ai['id']}", key=f"ai_memo_btn_{ai['id']}",
                                            on_click=_toggle_ai_memo, args=(ai['id'],))
                                  st.markdown(f'<div data-ai-del-btn="{ai["id"]}" style="height:0;overflow:hidden;font-size:0"></div>',
                                              unsafe_allow_html=True)
                                  st.button(f"_ad_{ai['id']}", key=f"ai_del_{ai['id']}",
                                            on_click=_delete_ai, args=(iid, ai['id'],))
                                  if st.session_state.get(f"ai_memo_edit_{ai['id']}", False):
                                      editing_ai = ai
                              if editing_ai:
                                  st.text_input(
                                      "메모",
                                      value=editing_ai.get("memo", ""),
                                      placeholder=f"「{editing_ai['text']}」 메모…",
                                      key=f"ai_memo_{editing_ai['id']}",
                                      label_visibility="collapsed",
                                      on_change=_on_action_memo,
                                      args=(iid, editing_ai["id"], f"ai_memo_{editing_ai['id']}"),
                                  )
                  else:
                      st.markdown(
                          '<div style="background:#FFFFFF;border-radius:5px;padding:14px 8px;'
                          'margin-top:4px;text-align:center;border:1px dashed #D0D8E8">'
                          '<span style="color:#666666;font-size:19px">미설정</span></div>',
                          unsafe_allow_html=True)

      st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

    # ── 보드 (전략별 / 담당자별) ──────────────────────────────────────────────
    if view_mode == "person":
        board_cols = st.columns(len(PERSON_ORDER), gap="small")
        for col_ui, person in zip(board_cols, PERSON_ORDER):
            with col_ui:
                render_person_column(person)
    else:
        board_cols = st.columns(len(COL_ORDER), gap="small")
        for col_ui, col_id in zip(board_cols, COL_ORDER):
            with col_ui:
                render_column(col_id)

    st.markdown('<hr style="border:none;border-top:1px solid #D0D8E8;margin:8px 0 10px"/>',
                unsafe_allow_html=True)

    # ── 백로그 ────────────────────────────────────────────────────────────────
    bk_ids    = data["columns"].get("backlog", [])
    bk_label  = f"📋 백로그  —  {len(bk_ids)}개 과제"
    with st.expander(bk_label, expanded=True):
        # 항상 표시: 빠른 추가 행
        qa1, qa2, qa3, qa4 = st.columns([4, 1.5, 1.5, 0.8])
        with qa1:
            qa_text = st.text_input("백로그 항목", placeholder="새 백로그 항목 추가…",
                                    key="qa_bk_text", label_visibility="collapsed")
        with qa2:
            qa_role = st.selectbox("담당자", ROLES, key="qa_bk_role", label_visibility="collapsed")
        with qa3:
            qa_timing = st.selectbox("타이밍", TIMINGS, key="qa_bk_timing", label_visibility="collapsed")
        with qa4:
            if st.button("✚ 추가", key="qa_bk_add", use_container_width=True):
                if qa_text.strip():
                    add_item("backlog", qa_role, qa_timing, qa_text.strip())
                    st.rerun()

        # 백로그 드롭 존 (다른 컬럼에서 드래그해 올 수 있음)
        st.markdown(
            '<div data-drop-col="backlog" style="min-height:32px;border:1px dashed #999999;'
            'border-radius:6px;display:flex;align-items:center;justify-content:center;'
            'margin:4px 0 8px;color:#999999;font-size:19px;cursor:default">'
            '여기에 드롭하면 백로그로 이동</div>',
            unsafe_allow_html=True)

        if bk_ids:
            bk_cols = st.columns(min(3, max(1, len(bk_ids))), gap="small")
            for idx, iid in enumerate(bk_ids):
                with bk_cols[idx % 3]:
                    render_item(iid, "backlog")
        else:
            st.markdown(
                '<p style="color:#666666;font-size:19px;text-align:center;'
                'padding:14px;border:1px dashed #D0D8E8;border-radius:6px">'
                '비어 있음 — 위 입력창으로 추가하거나 보드 카드를 드래그해 이동하세요</p>',
                unsafe_allow_html=True)

    # ── DnD / 더블클릭 JS 삽입 (iframe에서 parent DOM 접근) ──
    stc.html(_DND_IFRAME, height=0)

if __name__ == "__main__":
    main()
