import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from data.nutrition_loader import get_nutrition_by_name, search_foods

MEAL_SLOTS = {
    "아침": ["사과", "샌드위치", "바나나", "브로콜리", "아메리카노"],
    "점심": ["비빔밥", "제육", "김치찌개", "라면", "샌드위치"],
    "저녁": ["피자", "샐러드", "제육", "비빔밥"],
    "간식/야식": ["케이크", "도넛", "라떼", "콜라", "바나나"],
}


def safe_multiply(value, portion, decimals=1):
    if value is None or pd.isna(value):
        return None
    return round(float(value) * portion, decimals)


def build_meal_record(food_name, portion, meal_type, source="직접입력", recorded_at=None):
    item = get_nutrition_by_name(food_name)
    if item is None:
        raise ValueError(f"CSV에서 음식을 찾을 수 없습니다: {food_name}")

    recorded_at = recorded_at or datetime.now()
    return {
        "데이터구분": source,
        "기록일시": recorded_at.strftime("%Y-%m-%d %H:%M"),
        "날짜": recorded_at.strftime("%Y-%m-%d"),
        "식사구분": meal_type,
        "음식명": item["food_name"],
        "섭취수량": f"{portion} {item['serving_basis']}",
        "칼로리(kcal)": safe_multiply(item["calories"], portion),
        "탄수화물(g)": safe_multiply(item["carbs"], portion),
        "단백질(g)": safe_multiply(item["protein"], portion),
        "지방(g)": safe_multiply(item["fat"], portion),
        "당류(g)": safe_multiply(item["sugar"], portion),
        "나트륨(mg)": safe_multiply(item["sodium"], portion),
    }


def generate_mock_meals(count=30):
    records = []
    hour_ranges = {"아침": (7, 9), "점심": (12, 13), "저녁": (18, 20), "간식/야식": (14, 16)}
    for _ in range(count):
        meal_type = random.choice(list(MEAL_SLOTS))
        start_hour, end_hour = hour_ranges[meal_type]
        recorded_at = (datetime.now() - timedelta(days=random.randint(0, 6))).replace(
            hour=random.randint(start_hour, end_hour), minute=random.randint(10, 55)
        )
        keyword = random.choice(MEAL_SLOTS[meal_type])
        matches = search_foods(keyword, limit=20)
        if not matches:
            continue
        food_name = random.choice(matches)
        portion = random.choice([0.5, 1.0, 1.0, 1.0, 1.5, 2.0])
        records.append(build_meal_record(food_name, portion, meal_type, "가상생성", recorded_at))
    return sorted(records, key=lambda record: record["기록일시"], reverse=True)


def initialize_meal_history():
    if "initialized" not in st.session_state:
        st.session_state.meal_history = generate_mock_meals(30)
        st.session_state.initialized = True
    elif "meal_history" not in st.session_state:
        st.session_state.meal_history = []
    if "last_added_message" not in st.session_state:
        st.session_state.last_added_message = None


def add_meal_records(records):
    st.session_state.meal_history[0:0] = records
