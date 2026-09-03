import streamlit as st

from services.meal_service import generate_mock_meals


def render_sidebar():
    st.sidebar.title("📌 네비게이션")
    view_mode = st.sidebar.radio(
        "화면 모드", ["📷 음식 사진 분석 및 추가", "📊 종합 통계 대시보드"]
    )
    st.sidebar.divider()
    st.sidebar.subheader("🎲 가상 데이터 관리")
    mock_count = st.sidebar.slider("추가할 가상 데이터 수", 10, 50, 20, 5)

    if st.sidebar.button("✨ 가상 식단 데이터 추가 생성"):
        st.session_state.meal_history.extend(generate_mock_meals(mock_count))
        st.session_state.meal_history.sort(key=lambda record: record["기록일시"], reverse=True)
        st.sidebar.success(f"{mock_count}건의 식단이 추가되었습니다!")
        st.rerun()

    if st.sidebar.button("🗑️ 전체 데이터 비우기"):
        st.session_state.meal_history = []
        st.session_state.last_added_message = None
        st.sidebar.warning("데이터가 모두 삭제되었습니다.")
        st.rerun()

    daily_goal = st.sidebar.number_input("🎯 1일 목표 칼로리 (kcal)", 1200, 3500, 2000, 100)
    return view_mode, daily_goal
