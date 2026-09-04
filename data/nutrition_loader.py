from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent
NUTRITION_CSV = DATA_DIR / "CaloDetect_nutrition_clean_unique.csv"
REQUIRED_COLUMNS = [
    "food_code",
    "food_name",
    "food_category",
    "representative_food",
    "serving_basis",
    "calories",
    "carbs",
    "protein",
    "fat",
    "sugar",
    "sodium",
    "source",
]


@st.cache_data

def load_nutrition_db():
    database = pd.read_csv(NUTRITION_CSV, encoding="utf-8-sig")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in database.columns]
    if missing_columns:
        raise ValueError(f"영양 CSV에 필요한 컬럼이 없습니다: {missing_columns}")
    return database[REQUIRED_COLUMNS]


def get_nutrition_by_name(food_name):
    database = load_nutrition_db()
    matches = database[database["food_name"] == food_name]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()


def get_nutrition_by_code(food_code):
    database = load_nutrition_db()
    matches = database[database["food_code"] == food_code]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()


def search_foods(keyword, limit=20):
    if not keyword or not keyword.strip():
        return []
    database = load_nutrition_db()
    matches = database[database["food_name"].str.contains(keyword.strip(), na=False, regex=False)]
    return matches["food_name"].drop_duplicates().head(limit).tolist()


def get_food_names():
    return load_nutrition_db()["food_name"].drop_duplicates().tolist()
