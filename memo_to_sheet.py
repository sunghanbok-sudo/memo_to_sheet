import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
# [중요] 구글 라이브러리 대신 Groq을 가져옵니다.
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

# --- [기능 1] Groq (Llama 3) AI 요약 함수 ---
def run_ai_summarize(text):
    try:
        # Secrets에서 Groq 키를 가져옵니다.
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        # AI에게 일을 시킵니다.
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # 무료이고 가장 빠른 모델
            messages=[
                {
                    "role": "system", 
                    "content": "당신은 진주햄 마케팅팀의 유능한 비서입니다. 업무 내용을 바탕으로 [실행 요약]을 3줄 이내 개조식으로, 보고서체(~함)로 작성하세요."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            temperature=0.5, # 창의성 조절 (0에 가까울수록 사실적)
        )

        # 결과를 반환합니다.
        return completion.choices[0].message.content

    except Exception as e:
        return f"AI 오류 발생: {e}"
        당신은 군더더기 없는 '핵심 요약 전문가'입니다. 
        아래 원문을 보고 실무자가 즉시 실행할 수 있도록 '간단'하게 요약하세요.

        [원문]:
        {text}

        [절대 규칙]:
        1. 인사말, 배경 설명 등 불필요한 말 삭제.
        2. 오직 '행동(Action)'과 '핵심(Key)'만 남길 것.
        3. '~함', '~할 것', '~요망' 등 명사형 종결 사용.
        4. 최대 10줄 이내.
        """
        
        with st.spinner('핵심만 쏙쏙 뽑는 중... ☕'):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        st.error(f"AI 오류: {e}")
        return None

# --- [기능 2] 구글 시트 전송 함수 (Secrets 적용) ---
def save_to_sheet(user_name, content):
    try:
        with st.spinner('시트에 기록하는 중... 📝'):
            # [변경] 파일 경로 삭제 -> 클라우드 금고에 있는 JSON 내용 자체를 읽음
            credentials_dict = st.secrets["gcp_service_account"]
            gc = gspread.service_account_from_dict(credentials_dict)
            
            # [변경] 시트 이름도 금고에서 가져옴 (보안 및 수정 용이성)
            sheet_name = st.secrets["SPREADSHEET_NAME"]
            tab_name = st.secrets["SPREADSHEET_TAB_NAME"]
            
            sh = gc.open(sheet_name)
            worksheet = sh.worksheet(tab_name)

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
        st.caption("Memo to Sheet (Cloud ver.)")

    st.title("🍊 Memo to Sheet")
    st.markdown("따뜻한 커피 한 잔처럼, <span class='highlight-text'>업무 지시도 깔끔하게.</span>", unsafe_allow_html=True)
    st.write("")

    if st.session_state.step == 'input':
        st.subheader("1. 업무 내용 입력")
        raw_input = st.text_area("카톡/메일 원문", height=300, placeholder="여기에 내용을 붙여넣으세요...", key="input_area")
        
        if st.button("✨ 깔끔하게 정리하기", type="primary", use_container_width=True):
            if raw_input.strip():
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






