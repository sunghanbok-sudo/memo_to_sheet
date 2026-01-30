import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import time
from groq import Groq

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Memo to Sheet",
    page_icon="🍊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- 디자인: 따뜻하고 깔끔한 웜톤 (Cream & Soft Orange) ---
st.markdown("""
    <style>
        .stApp { background-color: #FFFEFA; color: #424242; }
        [data-testid="stSidebar"] { background-color: #F7F5F0; border-right: 1px solid #EAE0D5; }
        .stTextArea textarea {
            background-color: #FFFFFF; color: #333333;
            border-radius: 12px; border: 1px solid #E0E0E0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .stTextArea textarea:focus {
             border: 1px solid #FF8C42; box-shadow: 0 0 5px rgba(255, 140, 66, 0.3);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #FF9966 0%, #FF5E62 100%);
            color: white; border: none; border-radius: 20px;
            padding: 0.6rem 1.5rem; font-weight: 600;
            box-shadow: 0 4px 6px rgba(255, 94, 98, 0.2); transition: all 0.3s ease;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px); box-shadow: 0 6px 12px rgba(255, 94, 98, 0.3);
        }
        .stButton > button[kind="secondary"] {
            background-color: #FFFFFF; color: #555;
            border: 1px solid #DDD; border-radius: 20px;
        }
        h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #2D2D2D !important; }
        .highlight-text { color: #FF6B6B; font-weight: bold; }
        div[data-testid="stToast"] { background-color: #FFF; border-left: 5px solid #FF8C42; color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'step' not in st.session_state: st.session_state.step = 'input'
if 'raw_text' not in st.session_state: st.session_state.raw_text = ""
if 'summarized_text' not in st.session_state: st.session_state.summarized_text = ""

# --- [기능 1] Groq (Llama 3) AI 요약 함수 (프롬프트 수정됨) ---
def run_ai_summarize(text):
    try:
        # 1. Groq 클라이언트 설정
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        # 2. 프롬프트 구성 (요청사항 반영: 10줄 이내 + 억지로 늘리기 금지)
        prompt = f"""
        당신은 진주햄 마케팅 육가공사업팀의 전문 서기입니다.
        아래 [입력 내용]을 주간 업무 보고서에 바로 쓸 수 있도록 요약하세요.

        [작성 원칙]
        1. 불필요한 인사말, 사담, 이모티콘은 모두 제거할 것.
        2. 핵심 이슈와 실행 계획(Action Item) 위주로 정리할 것.
        3. 문장은 명사형 또는 '보고서체(~함, ~음)'로 간결하게 끝낼 것.
        4. 글머리 기호('-')를 사용하여 가독성을 높일 것.
        5. 분량은 **최대 10줄 이내**로 작성하되, 원문 내용이 적을 경우 억지로 늘리지 말고 핵심만 간결하게 작성할 것.

        [입력 내용]
        {text}
        """

        # 3. AI에게 업무 지시 (Llama3 모델 사용)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3, # 창의성 낮춤 (사실 기반 요약)
        )

        # 4. 결과 반환
        return completion.choices[0].message.content

    except Exception as e:
        return f"AI 오류 발생: {e}"

# --- [기능 2] 구글 시트 전송 함수 ---
def save_to_sheet(user_name, content):
    try:
        with st.spinner('시트에 기록하는 중... 📝'):
            # 금고(Secrets)에서 정보 가져오기
            credentials_dict = st.secrets["gcp_service_account"]
            gc = gspread.service_account_from_dict(credentials_dict)
            
            sheet_name = st.secrets["SPREADSHEET_NAME"]
            tab_name = st.secrets["SPREADSHEET_TAB_NAME"]
            
            sh = gc.open(sheet_name)
            worksheet = sh.worksheet(tab_name)

            # 한국 시간(KST) 설정
            korea_time = datetime.datetime.now() + datetime.timedelta(hours=9)
            now_str = korea_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 2번째 줄에 삽입 (최신순)
            worksheet.insert_row([now_str, user_name, content], 2)
            
            st.toast(f"✅ 저장 완료!", icon="🍊")
            return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

# --- 메인 화면 로직 ---
def main():
    with st.sidebar:
        st.title("👤 작성자 선택")
        # 요청하신 팀원 목록
        user_name = st.selectbox(
            "이름을 선택하세요", 
            ["복성한 팀장", "권미연 차장", "노경진 과장", "정나라 대리"]
        )
        st.markdown("---")
        st.caption("Memo to Sheet (Groq Cloud ver.)")

    st.title("🍊 Memo to Sheet")
    st.markdown("따뜻한 커피 한 잔처럼, <span class='highlight-text'>업무 지시도 깔끔하게.</span>", unsafe_allow_html=True)
    st.write("")

    if st.session_state.step == 'input':
        st.subheader("1. 업무 내용 입력")
        raw_input = st.text_area("카톡/메일 원문", height=300, placeholder="여기에 내용을 붙여넣으세요...", key="input_area")
        
        if st.button("✨ 깔끔하게 정리하기", type="primary", use_container_width=True):
            if raw_input.strip():
                with st.spinner('AI가 내용을 요약 중입니다... ⚡'):
                    summary = run_ai_summarize(raw_input)
                
                if summary:
                    st.session_state.raw_text = raw_input
                    st.session_state.summarized_text = summary
                    st.session_state.step = 'review'
                    st.rerun()
            else:
                st.warning("내용을 입력해주세요.")

    elif st.session_state.step == 'review':
        st.subheader("2. 내용 확인")
        edited_summary = st.text_area("정리된 내용 (수정 가능)", value=st.session_state.summarized_text, height=150)

        col1, col2 = st.columns(2)
        with col1:
             if st.button("⬅️ 다시 쓰기", use_container_width=True):
                 st.session_state.step = 'input'
                 st.session_state.summarized_text = ""
                 st.rerun()
        with col2:
            if st.button("🚀 시트로 보내기", type="primary", use_container_width=True):
                if edited_summary.strip():
                    success = save_to_sheet(user_name, edited_summary)
                    if success:
                        time.sleep(1.2)
                        st.session_state.step = 'input'
                        st.session_state.raw_text = ""
                        st.session_state.summarized_text = ""
                        st.rerun()

if __name__ == "__main__":
    main()

