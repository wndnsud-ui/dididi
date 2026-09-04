from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


def _highlight_real_data(row):
    if row["데이터구분"] == "직접입력":
        return ["background-color: #d4edda; color: #155724; font-weight: bold;"] * len(row)
    return [""] * len(row)


def _sum_known_values(series):
    total = series.sum(min_count=1)
    return None if pd.isna(total) else round(float(total), 1)


def _format_metric(value, unit):
    return "-" if value is None else f"{value:,} {unit}"


def render_dashboard(daily_goal):
    st.title("📊 다이어트 영양 통계 대시보드")
    if not st.session_state.meal_history:
        st.info("데이터가 비어 있습니다. 사진을 분석해 추가하거나 사이드바에서 가상 데이터를 생성하세요.")
        return

    df = pd.DataFrame(st.session_state.meal_history)
    totals = {
        "calories": _sum_known_values(df["칼로리(kcal)"]),
        "carbs": _sum_known_values(df["탄수화물(g)"]),
        "protein": _sum_known_values(df["단백질(g)"]),
        "fat": _sum_known_values(df["지방(g)"]),
    }
    st.markdown(f"### 📈 누적 식단 데이터 현황 (총 {len(df)}건)")
    columns = st.columns(4)
    columns[0].metric("누적 섭취 칼로리", _format_metric(totals["calories"], "kcal"))
    columns[1].metric("누적 탄수화물", _format_metric(totals["carbs"], "g"))
    columns[2].metric("누적 단백질", _format_metric(totals["protein"], "g"))
    columns[3].metric("누적 지방", _format_metric(totals["fat"], "g"))

    st.divider()
    st.subheader("📅 최근 일자별 칼로리 섭취 추이")
    daily_df = df.groupby("날짜")["칼로리(kcal)"].sum().reset_index().sort_values("날짜")
    daily_chart = px.line(daily_df, x="날짜", y="칼로리(kcal)", markers=True,
                          title="일자별 칼로리 변화 (목표선: 빨간 점선)")
    daily_chart.add_hline(y=daily_goal, line_dash="dash", line_color="red", annotation_text="목표 칼로리")
    daily_chart.update_layout(height=320, margin=dict(t=30, b=20, l=10, r=10))
    st.plotly_chart(daily_chart, width="stretch")

    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.subheader("🍽️ 식사 구분별 총 섭취량")
        meal_group = df.groupby("식사구분")["칼로리(kcal)"].sum().reset_index()
        meal_chart = px.bar(
            meal_group, x="식사구분", y="칼로리(kcal)", color="식사구분",
            category_orders={"식사구분": ["아침", "점심", "저녁", "간식/야식"]},
        )
        meal_chart.update_layout(height=300, showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(meal_chart, width="stretch")

    with chart_columns[1]:
        st.subheader("⚖️ 전체 탄·단·지 칼로리 구성 비율")
        macro_values = {
            "탄수화물": (totals["carbs"], 4),
            "단백질": (totals["protein"], 4),
            "지방": (totals["fat"], 9),
        }
        macro_data = pd.DataFrame({
            "영양소": [name for name, (value, _) in macro_values.items() if value is not None],
            "열량": [value * multiplier for value, multiplier in macro_values.values() if value is not None],
        })
        if macro_data.empty:
            st.info("탄·단·지 정보가 있는 기록이 없어 비율을 계산할 수 없습니다.")
        else:
            st.caption("영양성분 결측값은 탄·단·지 합산에서 제외했습니다.")
            macro_chart = px.pie(
                macro_data, values="열량", names="영양소", hole=0.45, color="영양소",
                color_discrete_map={"탄수화물": "#4CAF50", "단백질": "#2196F3", "지방": "#FF9800"},
            )
            macro_chart.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(macro_chart, width="stretch")

    st.divider()
    st.subheader("📋 전체 식사 히스토리 테이블")
    st.caption("🟢 **초록색으로 칠해진 행**은 사용자가 사진으로 직접 등록한 실제 데이터입니다.")
    st.dataframe(df.style.apply(_highlight_real_data, axis=1), width="stretch", hide_index=True)
    st.download_button(
        label="📥 전체 식단 CSV 다운로드",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"diet_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
