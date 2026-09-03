import streamlit as st

from app_pages.dashboard import render_dashboard
from app_pages.meal_analysis import render_meal_analysis
from components.sidebar import render_sidebar
from services.meal_service import initialize_meal_history

st.set_page_config(
    page_title="AI 맞춤형 식단 다이어리 & 대시보드",
    page_icon="🥗",
    layout="wide",
)

initialize_meal_history()
view_mode, daily_goal = render_sidebar()

if view_mode == "📷 음식 사진 분석 및 추가":
    render_meal_analysis()
else:
    render_dashboard(daily_goal)
