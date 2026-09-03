import random
from datetime import datetime, timedelta

import streamlit as st

from data.nutrition import NUTRITION_DB

MEAL_SLOTS = {
    "아침": ["apple_fuji", "sandwich_egg", "banana_standard", "broccoli_steamed", "cup_americano"],
    "점심": ["bowl_bibimbap", "bowl_jeyuk", "bowl_kimchi_jjigae", "bowl_ramen", "sandwich_chicken"],
    "저녁": ["pizza_pepperoni", "pizza_cheese", "pizza_combination", "salad_chicken", "bowl_jeyuk"],
    "간식/야식": ["cake_piece", "donut_glazed", "cup_latte", "bottle_cola_zero", "banana_standard"],
}


def build_meal_record(food_key, portion, meal_type, source="직접입력", recorded_at=None):
    item = NUTRITION_DB[food_key]
    recorded_at = recorded_at or datetime.now()
    return {
        "데이터구분": source,
        "기록일시": recorded_at.strftime("%Y-%m-%d %H:%M"),
        "날짜": recorded_at.strftime("%Y-%m-%d"),
        "식사구분": meal_type,
        "음식명": item["name"],
        "섭취수량": f"{portion} {item['unit']}",
        "칼로리(kcal)": round(item["cal"] * portion, 1),
        "탄수화물(g)": round(item["carbs"] * portion, 1),
        "단백질(g)": round(item["protein"] * portion, 1),
        "지방(g)": round(item["fat"] * portion, 1),
        "당류(g)": round(item["sugar"] * portion, 1),
        "나트륨(mg)": int(item["sodium"] * portion),
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
        food_key = random.choice(MEAL_SLOTS[meal_type])
        portion = random.choice([0.5, 1.0, 1.0, 1.0, 1.5, 2.0])
        records.append(build_meal_record(food_key, portion, meal_type, "가상생성", recorded_at))
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
