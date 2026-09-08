import os
import random
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image, ImageDraw
import torch
from torchvision.ops import nms
from ultralytics import YOLO

# ==============================================================================
# [1] 웹 페이지 기본 설정
# ==============================================================================
st.set_page_config(
    page_title="AI 맞춤형 식단 다이어리 & 대시보드",
    page_icon="🥗",
    layout="wide"
)

# ==============================================================================
# [2] 라벨 번역 맵 및 영양 데이터베이스
# ==============================================================================
# 55종 모델(best1.pt)의 영문 라벨 -> 한글 변환 매핑
BEST1_KO_MAP = {
    "Braised lotus roots": "연근조림", "Dongchimi": "동치미", "Japchae": "잡채",
    "Kimchi stew": "김치찌개", "Kimchi": "배추김치", "Korean rib": "갈비구이",
    "Korean style raw beef": "육회", "Seasoned bean sprouts": "콩나물무침",
    "Udon": "우동", "baek Kimchi": "백김치", "banquet noodles": "잔치국수",
    "bean sprout soup": "콩나물국", "beef-bone soup": "곰탕_설렁탕",
    "bellflower greens": "도라지무침", "bibimbap": "비빔밥",
    "boiled fish paste soup": "어묵탕", "budaejjigae": "부대찌개",
    "bulgogi": "불고기", "chonggak Kimchi": "총각김치", "cucumber kimchi": "오이소박이",
    "cup rice": "컵밥", "dried pollack soup": "북엇국", "eel": "장어구이",
    "fried rice": "볶음밥", "green onion Kimchi": "파김치", "grilled mackerel": "고등어구이",
    "janjorim": "장조림", "jeyuk bokkeum": "제육볶음", "memil soba": "메밀소바",
    "miso soup": "된장찌개", "mixed rice": "잡곡밥", "nabak Kimchi": "나박김치",
    "naengMyeon": "물냉면", "pickled sesame leaf": "깻잎장아찌", "pig hocks": "족발",
    "pork belly": "삼겹살", "radish Kimchi": "깍두기", "radish kimchi": "깍두기",
    "rice ball": "주먹밥", "rice roll": "김밥", "rice": "쌀밥",
    "seasoned bean sprouts": "숙주나물", "seasoned bellflower root": "도라지무침",
    "seasoned bracken": "고사리나물", "seasoned zucchini": "애호박볶음",
    "seaweed soup": "미역국", "seaweed": "미역줄기볶음", "shellfish soup": "조개탕",
    "spicy yuke jang": "육개장", "spinach greens": "시금치나물", "stewed mackerel": "고등어조림",
    "stir-fried anchovies": "멸치볶음", "young radish Kimchi": "열무김치"
}

# 기본 모델(yolov8n.pt)의 과일/간식류 영문 라벨 -> 한글 변환 매핑
COCO_KO_MAP = {
    "sandwich": "샌드위치", "hot dog": "핫도그", "apple": "사과",
    "banana": "바나나", "orange": "오렌지", "broccoli": "데친 브로콜리",
    "carrot": "당근", "donut": "도넛", "cake": "조각 케이크"
}

# 150종 한식 + 과일/양식 표준 1인분 영양 데이터베이스
NUTRITION_DB = {
    # 과일/간식류 (COCO 보충)
    "샌드위치": {"category": "간편식", "unit": "개", "cal": 380, "carbs": 42.0, "protein": 16.0, "fat": 15.0, "sugar": 5.0, "sodium": 750},
    "핫도그": {"category": "간편식", "unit": "개", "cal": 290, "carbs": 26.0, "protein": 10.0, "fat": 16.0, "sugar": 4.0, "sodium": 680},
    "사과": {"category": "과일", "unit": "개", "cal": 105, "carbs": 27.5, "protein": 0.6, "fat": 0.3, "sugar": 21.0, "sodium": 2},
    "바나나": {"category": "과일", "unit": "개", "cal": 105, "carbs": 27.0, "protein": 1.3, "fat": 0.3, "sugar": 14.4, "sodium": 1},
    "오렌지": {"category": "과일", "unit": "개", "cal": 62, "carbs": 15.0, "protein": 1.2, "fat": 0.2, "sugar": 12.0, "sodium": 0},
    "데친 브로콜리": {"category": "채소", "unit": "접시", "cal": 35, "carbs": 6.8, "protein": 2.8, "fat": 0.4, "sugar": 1.4, "sodium": 33},
    "당근": {"category": "채소", "unit": "개", "cal": 35, "carbs": 8.0, "protein": 0.9, "fat": 0.2, "sugar": 4.5, "sodium": 60},
    "도넛": {"category": "디저트", "unit": "개", "cal": 250, "carbs": 30.0, "protein": 3.0, "fat": 14.0, "sugar": 15.0, "sodium": 190},
    "조각 케이크": {"category": "디저트", "unit": "조각", "cal": 350, "carbs": 45.0, "protein": 4.0, "fat": 18.0, "sugar": 28.0, "sodium": 220},

    # 밥/죽류
    "쌀밥": {"category": "밥류", "unit": "공기", "cal": 300, "carbs": 68.0, "protein": 5.5, "fat": 0.7, "sugar": 0.1, "sodium": 5},
    "잡곡밥": {"category": "밥류", "unit": "공기", "cal": 320, "carbs": 66.0, "protein": 7.0, "fat": 1.5, "sugar": 0.2, "sodium": 6},
    "김밥": {"category": "밥류", "unit": "줄", "cal": 400, "carbs": 65.0, "protein": 12.0, "fat": 9.0, "sugar": 2.5, "sodium": 850},
    "김치볶음밥": {"category": "밥류", "unit": "인분", "cal": 570, "carbs": 80.0, "protein": 13.0, "fat": 18.0, "sugar": 3.2, "sodium": 980},
    "비빔밥": {"category": "밥류", "unit": "그릇", "cal": 580, "carbs": 95.0, "protein": 18.0, "fat": 14.0, "sugar": 7.0, "sodium": 920},
    "새우볶음밥": {"category": "밥류", "unit": "인분", "cal": 550, "carbs": 78.0, "protein": 15.0, "fat": 17.0, "sugar": 2.5, "sodium": 820},
    "알밥": {"category": "밥류", "unit": "뚝배기", "cal": 490, "carbs": 74.0, "protein": 14.0, "fat": 12.0, "sugar": 3.0, "sodium": 760},
    "유부초밥": {"category": "밥류", "unit": "인분", "cal": 380, "carbs": 64.0, "protein": 11.0, "fat": 8.0, "sugar": 9.0, "sodium": 650},
    "주먹밥": {"category": "밥류", "unit": "개", "cal": 210, "carbs": 42.0, "protein": 4.5, "fat": 2.0, "sugar": 0.5, "sodium": 380},
    "누룽지": {"category": "밥류", "unit": "그릇", "cal": 220, "carbs": 50.0, "protein": 3.5, "fat": 0.5, "sugar": 0.0, "sodium": 10},
    "전복죽": {"category": "죽류", "unit": "대접", "cal": 280, "carbs": 52.0, "protein": 11.0, "fat": 2.5, "sugar": 0.8, "sodium": 590},
    "호박죽": {"category": "죽류", "unit": "대접", "cal": 210, "carbs": 48.0, "protein": 3.0, "fat": 0.6, "sugar": 14.0, "sodium": 420},

    # 국/탕/찌개류
    "계란국": {"category": "국류", "unit": "대접", "cal": 95, "carbs": 3.0, "protein": 8.0, "fat": 5.5, "sugar": 0.8, "sodium": 720},
    "곰탕_설렁탕": {"category": "탕류", "unit": "뚝배기", "cal": 320, "carbs": 6.0, "protein": 34.0, "fat": 16.0, "sugar": 0.1, "sodium": 650},
    "김치찌개": {"category": "찌개류", "unit": "인분", "cal": 210, "carbs": 12.0, "protein": 15.0, "fat": 11.0, "sugar": 3.5, "sodium": 1450},
    "김치찜": {"category": "찜류", "unit": "인분", "cal": 350, "carbs": 14.0, "protein": 28.0, "fat": 20.0, "sugar": 5.5, "sodium": 1550},
    "닭계장": {"category": "국류", "unit": "대접", "cal": 310, "carbs": 10.0, "protein": 26.0, "fat": 18.0, "sugar": 2.5, "sodium": 1450},
    "동태찌개": {"category": "찌개류", "unit": "인분", "cal": 230, "carbs": 8.0, "protein": 32.0, "fat": 6.0, "sugar": 2.0, "sodium": 1350},
    "된장찌개": {"category": "찌개류", "unit": "뚝배기", "cal": 150, "carbs": 11.0, "protein": 12.0, "fat": 5.5, "sugar": 2.5, "sodium": 1280},
    "떡국_만두국": {"category": "국류", "unit": "그릇", "cal": 490, "carbs": 82.0, "protein": 16.0, "fat": 10.0, "sugar": 2.0, "sodium": 1450},
    "매운탕": {"category": "탕류", "unit": "대접", "cal": 260, "carbs": 10.0, "protein": 34.0, "fat": 8.0, "sugar": 3.0, "sodium": 1520},
    "무국": {"category": "국류", "unit": "대접", "cal": 85, "carbs": 5.0, "protein": 8.0, "fat": 3.5, "sugar": 1.5, "sodium": 780},
    "미역국": {"category": "국류", "unit": "대접", "cal": 80, "carbs": 6.0, "protein": 5.0, "fat": 4.0, "sugar": 0.5, "sodium": 750},
    "북엇국": {"category": "국류", "unit": "대접", "cal": 120, "carbs": 5.0, "protein": 18.0, "fat": 2.5, "sugar": 0.2, "sodium": 950},
    "순두부찌개": {"category": "찌개류", "unit": "뚝배기", "cal": 230, "carbs": 8.0, "protein": 17.0, "fat": 14.0, "sugar": 2.2, "sodium": 1220},
    "시래기국": {"category": "국류", "unit": "대접", "cal": 95, "carbs": 9.0, "protein": 6.0, "fat": 3.5, "sugar": 1.2, "sodium": 980},
    "육개장": {"category": "탕류", "unit": "대접", "cal": 350, "carbs": 14.0, "protein": 24.0, "fat": 21.0, "sugar": 3.0, "sodium": 1650},
    "추어탕": {"category": "탕류", "unit": "뚝배기", "cal": 280, "carbs": 12.0, "protein": 22.0, "fat": 14.0, "sugar": 1.8, "sodium": 1150},
    "콩나물국": {"category": "국류", "unit": "대접", "cal": 45, "carbs": 4.0, "protein": 4.0, "fat": 1.5, "sugar": 0.3, "sodium": 850},
    "갈비탕": {"category": "탕류", "unit": "뚝배기", "cal": 450, "carbs": 8.0, "protein": 42.0, "fat": 26.0, "sugar": 0.5, "sodium": 950},
    "감자탕": {"category": "탕류", "unit": "뚝배기", "cal": 520, "carbs": 18.0, "protein": 45.0, "fat": 28.0, "sugar": 3.0, "sodium": 1750},
    "곱창전골": {"category": "전골류", "unit": "인분", "cal": 540, "carbs": 16.0, "protein": 32.0, "fat": 38.0, "sugar": 4.0, "sodium": 1620},
    "삼계탕": {"category": "탕류", "unit": "뚝배기", "cal": 920, "carbs": 45.0, "protein": 78.0, "fat": 38.0, "sugar": 1.0, "sodium": 1100},

    # 고기/구이/볶음/조림류
    "갈비구이": {"category": "육류", "unit": "인분", "cal": 520, "carbs": 12.0, "protein": 38.0, "fat": 35.0, "sugar": 8.0, "sodium": 720},
    "갈비찜": {"category": "육류", "unit": "인분", "cal": 580, "carbs": 16.0, "protein": 42.0, "fat": 38.0, "sugar": 10.0, "sodium": 880},
    "곱창구이": {"category": "육류", "unit": "인분", "cal": 590, "carbs": 4.0, "protein": 28.0, "fat": 50.0, "sugar": 1.0, "sodium": 520},
    "닭갈비": {"category": "육류", "unit": "인분", "cal": 560, "carbs": 24.0, "protein": 44.0, "fat": 30.0, "sugar": 9.0, "sodium": 1150},
    "닭볶음탕": {"category": "육류", "unit": "인분", "cal": 540, "carbs": 26.0, "protein": 48.0, "fat": 24.0, "sugar": 8.0, "sodium": 1280},
    "떡갈비": {"category": "육류", "unit": "인분", "cal": 420, "carbs": 14.0, "protein": 28.0, "fat": 26.0, "sugar": 7.0, "sodium": 680},
    "보쌈": {"category": "육류", "unit": "인분", "cal": 540, "carbs": 2.0, "protein": 42.0, "fat": 39.0, "sugar": 1.0, "sodium": 480},
    "불고기": {"category": "육류", "unit": "인분", "cal": 380, "carbs": 18.0, "protein": 30.0, "fat": 20.0, "sugar": 9.0, "sodium": 790},
    "삼겹살": {"category": "육류", "unit": "인분", "cal": 650, "carbs": 0.0, "protein": 35.0, "fat": 56.0, "sugar": 0.0, "sodium": 120},
    "수육": {"category": "육류", "unit": "인분", "cal": 510, "carbs": 1.0, "protein": 40.0, "fat": 37.0, "sugar": 0.5, "sodium": 390},
    "양념치킨": {"category": "육류", "unit": "조각(2개)", "cal": 580, "carbs": 38.0, "protein": 32.0, "fat": 31.0, "sugar": 16.0, "sodium": 920},
    "육회": {"category": "육류", "unit": "접시", "cal": 240, "carbs": 8.0, "protein": 28.0, "fat": 10.0, "sugar": 6.0, "sodium": 520},
    "제육볶음": {"category": "육류", "unit": "접시", "cal": 450, "carbs": 15.0, "protein": 32.0, "fat": 28.0, "sugar": 8.0, "sodium": 880},
    "족발": {"category": "육류", "unit": "인분", "cal": 550, "carbs": 4.0, "protein": 48.0, "fat": 37.0, "sugar": 2.0, "sodium": 650},
    "찜닭": {"category": "육류", "unit": "인분", "cal": 520, "carbs": 32.0, "protein": 46.0, "fat": 20.0, "sugar": 12.0, "sodium": 1350},
    "편육": {"category": "육류", "unit": "접시", "cal": 310, "carbs": 1.0, "protein": 26.0, "fat": 21.0, "sugar": 0.2, "sodium": 340},
    "후라이드치킨": {"category": "육류", "unit": "조각(2개)", "cal": 520, "carbs": 20.0, "protein": 35.0, "fat": 32.0, "sugar": 1.0, "sodium": 680},
    "훈제오리": {"category": "육류", "unit": "인분", "cal": 480, "carbs": 2.0, "protein": 32.0, "fat": 36.0, "sugar": 1.5, "sodium": 650},

    # 생선/해물류
    "갈치구이": {"category": "생선구이", "unit": "토막", "cal": 250, "carbs": 0.0, "protein": 30.0, "fat": 13.0, "sugar": 0.0, "sodium": 420},
    "갈치조림": {"category": "생선조림", "unit": "토막", "cal": 290, "carbs": 11.0, "protein": 28.0, "fat": 14.0, "sugar": 5.0, "sodium": 920},
    "고등어구이": {"category": "생선구이", "unit": "토막", "cal": 310, "carbs": 0.0, "protein": 29.0, "fat": 21.0, "sugar": 0.0, "sodium": 480},
    "고등어조림": {"category": "생선조림", "unit": "토막", "cal": 280, "carbs": 10.0, "protein": 26.0, "fat": 14.0, "sugar": 5.0, "sodium": 890},
    "꽁치조림": {"category": "생선조림", "unit": "토막", "cal": 270, "carbs": 9.0, "protein": 24.0, "fat": 15.0, "sugar": 4.5, "sodium": 850},
    "장어구이": {"category": "생선구이", "unit": "마리", "cal": 420, "carbs": 8.0, "protein": 36.0, "fat": 27.0, "sugar": 6.0, "sodium": 580},
    "조기구이": {"category": "생선구이", "unit": "마리", "cal": 210, "carbs": 0.0, "protein": 26.0, "fat": 11.0, "sugar": 0.0, "sodium": 440},
    "간장게장": {"category": "절임류", "unit": "마리", "cal": 180, "carbs": 10.0, "protein": 24.0, "fat": 4.0, "sugar": 5.0, "sodium": 1890},
    "양념게장": {"category": "무침류", "unit": "접시", "cal": 220, "carbs": 16.0, "protein": 22.0, "fat": 6.0, "sugar": 9.0, "sodium": 1720},
    "꼬막찜": {"category": "해물찜", "unit": "접시", "cal": 130, "carbs": 4.0, "protein": 18.0, "fat": 3.0, "sugar": 1.0, "sodium": 680},
    "주꾸미볶음": {"category": "볶음류", "unit": "접시", "cal": 260, "carbs": 16.0, "protein": 28.0, "fat": 8.0, "sugar": 7.0, "sodium": 1050},
    "해물찜": {"category": "찜류", "unit": "인분", "cal": 380, "carbs": 24.0, "protein": 42.0, "fat": 11.0, "sugar": 6.0, "sodium": 1550},
    "황태구이": {"category": "구이류", "unit": "마리", "cal": 260, "carbs": 12.0, "protein": 38.0, "fat": 4.0, "sugar": 6.0, "sodium": 820},

    # 반찬/나물/김치/계란
    "배추김치": {"category": "김치류", "unit": "접시", "cal": 14, "carbs": 2.4, "protein": 1.1, "fat": 0.3, "sugar": 1.0, "sodium": 420},
    "깍두기": {"category": "김치류", "unit": "접시", "cal": 16, "carbs": 3.0, "protein": 0.8, "fat": 0.2, "sugar": 1.5, "sodium": 410},
    "갓김치": {"category": "김치류", "unit": "접시", "cal": 18, "carbs": 3.2, "protein": 1.3, "fat": 0.3, "sugar": 1.2, "sodium": 460},
    "백김치": {"category": "김치류", "unit": "접시", "cal": 10, "carbs": 1.8, "protein": 0.7, "fat": 0.1, "sugar": 0.8, "sodium": 310},
    "부추김치": {"category": "김치류", "unit": "접시", "cal": 22, "carbs": 3.5, "protein": 1.2, "fat": 0.4, "sugar": 1.4, "sodium": 430},
    "열무김치": {"category": "김치류", "unit": "접시", "cal": 12, "carbs": 2.0, "protein": 0.9, "fat": 0.2, "sugar": 0.8, "sodium": 380},
    "오이소박이": {"category": "김치류", "unit": "접시", "cal": 20, "carbs": 3.5, "protein": 1.0, "fat": 0.2, "sugar": 1.8, "sodium": 390},
    "총각김치": {"category": "김치류", "unit": "접시", "cal": 18, "carbs": 3.2, "protein": 1.2, "fat": 0.3, "sugar": 1.1, "sodium": 450},
    "파김치": {"category": "김치류", "unit": "접시", "cal": 25, "carbs": 3.8, "protein": 1.4, "fat": 0.5, "sugar": 1.5, "sodium": 430},
    "나박김치": {"category": "김치류", "unit": "대접", "cal": 14, "carbs": 2.8, "protein": 0.6, "fat": 0.1, "sugar": 1.7, "sodium": 460},
    "가지볶음": {"category": "반찬류", "unit": "접시", "cal": 60, "carbs": 7.0, "protein": 1.5, "fat": 3.0, "sugar": 2.5, "sodium": 380},
    "감자조림": {"category": "반찬류", "unit": "접시", "cal": 95, "carbs": 18.0, "protein": 2.0, "fat": 1.5, "sugar": 4.0, "sodium": 420},
    "감자채볶음": {"category": "반찬류", "unit": "접시", "cal": 85, "carbs": 15.0, "protein": 1.8, "fat": 2.2, "sugar": 1.0, "sodium": 310},
    "고사리나물": {"category": "나물류", "unit": "접시", "cal": 50, "carbs": 6.0, "protein": 2.5, "fat": 2.0, "sugar": 0.8, "sodium": 310},
    "도라지무침": {"category": "나물류", "unit": "접시", "cal": 65, "carbs": 11.0, "protein": 1.5, "fat": 1.8, "sugar": 2.0, "sodium": 330},
    "두부조림": {"category": "반찬류", "unit": "접시", "cal": 130, "carbs": 5.0, "protein": 12.0, "fat": 7.0, "sugar": 2.5, "sodium": 580},
    "두부김치": {"category": "안주/반찬", "unit": "접시", "cal": 240, "carbs": 10.0, "protein": 18.0, "fat": 14.0, "sugar": 3.5, "sodium": 790},
    "땅콩조림": {"category": "반찬류", "unit": "접시", "cal": 140, "carbs": 11.0, "protein": 6.0, "fat": 8.0, "sugar": 5.0, "sodium": 390},
    "멸치볶음": {"category": "반찬류", "unit": "접시", "cal": 95, "carbs": 6.0, "protein": 8.0, "fat": 4.0, "sugar": 4.0, "sodium": 410},
    "무생채": {"category": "나물류", "unit": "접시", "cal": 30, "carbs": 6.0, "protein": 0.8, "fat": 0.2, "sugar": 2.5, "sodium": 390},
    "미역줄기볶음": {"category": "반찬류", "unit": "접시", "cal": 45, "carbs": 4.0, "protein": 1.8, "fat": 2.5, "sugar": 0.5, "sodium": 480},
    "숙주나물": {"category": "나물류", "unit": "접시", "cal": 35, "carbs": 2.8, "protein": 3.0, "fat": 1.2, "sugar": 0.3, "sodium": 250},
    "시금치나물": {"category": "나물류", "unit": "접시", "cal": 45, "carbs": 4.0, "protein": 3.2, "fat": 1.8, "sugar": 0.5, "sodium": 290},
    "애호박볶음": {"category": "반찬류", "unit": "접시", "cal": 55, "carbs": 6.0, "protein": 1.8, "fat": 2.8, "sugar": 2.5, "sodium": 320},
    "어묵볶음": {"category": "반찬류", "unit": "접시", "cal": 140, "carbs": 14.0, "protein": 8.0, "fat": 5.5, "sugar": 3.5, "sodium": 680},
    "연근조림": {"category": "반찬류", "unit": "접시", "cal": 75, "carbs": 15.0, "protein": 1.8, "fat": 0.5, "sugar": 8.0, "sodium": 350},
    "우엉조림": {"category": "반찬류", "unit": "접시", "cal": 80, "carbs": 16.0, "protein": 1.6, "fat": 1.0, "sugar": 7.0, "sodium": 390},
    "장조림": {"category": "반찬류", "unit": "접시", "cal": 85, "carbs": 3.0, "protein": 13.0, "fat": 2.0, "sugar": 2.5, "sodium": 620},
    "메추리알장조림": {"category": "반찬류", "unit": "접시", "cal": 95, "carbs": 4.0, "protein": 8.5, "fat": 5.0, "sugar": 3.0, "sodium": 590},
    "콩나물무침": {"category": "나물류", "unit": "접시", "cal": 40, "carbs": 3.0, "protein": 3.5, "fat": 1.5, "sugar": 0.5, "sodium": 280},
    "콩자반": {"category": "반찬류", "unit": "접시", "cal": 110, "carbs": 12.0, "protein": 8.5, "fat": 3.0, "sugar": 6.0, "sodium": 420},
    "깻잎장아찌": {"category": "반찬류", "unit": "접시", "cal": 30, "carbs": 4.5, "protein": 1.8, "fat": 0.4, "sugar": 2.0, "sodium": 490},
    "계란말이": {"category": "반찬류", "unit": "접시", "cal": 190, "carbs": 2.5, "protein": 14.0, "fat": 13.5, "sugar": 1.0, "sodium": 420},
    "계란찜": {"category": "반찬류", "unit": "뚝배기", "cal": 140, "carbs": 3.0, "protein": 12.0, "fat": 8.5, "sugar": 1.2, "sodium": 550},
    "계란후라이": {"category": "반찬류", "unit": "개", "cal": 90, "carbs": 0.5, "protein": 6.5, "fat": 7.0, "sugar": 0.2, "sodium": 110},
    "소세지볶음": {"category": "반찬류", "unit": "접시", "cal": 210, "carbs": 12.0, "protein": 8.0, "fat": 14.0, "sugar": 5.0, "sodium": 650},

    # 면/만두류
    "라면": {"category": "면류", "unit": "그릇", "cal": 520, "carbs": 82.0, "protein": 12.0, "fat": 16.0, "sugar": 4.0, "sodium": 1780},
    "막국수": {"category": "면류", "unit": "그릇", "cal": 480, "carbs": 90.0, "protein": 13.0, "fat": 6.0, "sugar": 11.0, "sodium": 1350},
    "물냉면": {"category": "면류", "unit": "그릇", "cal": 460, "carbs": 94.0, "protein": 14.0, "fat": 2.0, "sugar": 11.0, "sodium": 1550},
    "비빔냉면": {"category": "면류", "unit": "그릇", "cal": 510, "carbs": 98.0, "protein": 15.0, "fat": 5.0, "sugar": 18.0, "sodium": 1420},
    "수제비": {"category": "면류", "unit": "그릇", "cal": 420, "carbs": 84.0, "protein": 12.0, "fat": 3.5, "sugar": 2.0, "sodium": 1380},
    "잔치국수": {"category": "면류", "unit": "그릇", "cal": 380, "carbs": 72.0, "protein": 12.0, "fat": 4.0, "sugar": 3.0, "sodium": 1450},
    "잡채": {"category": "면류", "unit": "접시", "cal": 210, "carbs": 32.0, "protein": 5.0, "fat": 7.0, "sugar": 5.0, "sodium": 520},
    "짜장면": {"category": "면류", "unit": "그릇", "cal": 680, "carbs": 110.0, "protein": 18.0, "fat": 18.0, "sugar": 9.0, "sodium": 1650},
    "짬뽕": {"category": "면류", "unit": "그릇", "cal": 590, "carbs": 92.0, "protein": 24.0, "fat": 14.0, "sugar": 6.0, "sodium": 1950},
    "쫄면": {"category": "면류", "unit": "그릇", "cal": 490, "carbs": 96.0, "protein": 12.0, "fat": 6.0, "sugar": 15.0, "sodium": 1480},
    "칼국수": {"category": "면류", "unit": "그릇", "cal": 460, "carbs": 86.0, "protein": 14.0, "fat": 5.0, "sugar": 2.5, "sodium": 1520},
    "콩국수": {"category": "면류", "unit": "그릇", "cal": 510, "carbs": 74.0, "protein": 24.0, "fat": 13.0, "sugar": 3.0, "sodium": 820},
    "열무국수": {"category": "면류", "unit": "그릇", "cal": 390, "carbs": 76.0, "protein": 11.0, "fat": 3.5, "sugar": 8.0, "sodium": 1450},
    "만두": {"category": "만두류", "unit": "접시(5개)", "cal": 320, "carbs": 36.0, "protein": 14.0, "fat": 13.0, "sugar": 2.0, "sodium": 650},

    # 분식/전/기타
    "떡볶이": {"category": "분식", "unit": "인분", "cal": 380, "carbs": 76.0, "protein": 7.0, "fat": 4.5, "sugar": 14.0, "sodium": 1150},
    "라볶이": {"category": "분식", "unit": "인분", "cal": 520, "carbs": 92.0, "protein": 11.0, "fat": 11.0, "sugar": 16.0, "sodium": 1480},
    "순대": {"category": "분식", "unit": "인분", "cal": 360, "carbs": 48.0, "protein": 12.0, "fat": 13.0, "sugar": 1.0, "sodium": 750},
    "떡꼬치": {"category": "분식", "unit": "개", "cal": 220, "carbs": 44.0, "protein": 3.5, "fat": 3.0, "sugar": 11.0, "sodium": 420},
    "피자": {"category": "양식", "unit": "조각", "cal": 320, "carbs": 35.0, "protein": 13.0, "fat": 14.0, "sugar": 4.0, "sodium": 620},
    "감자전": {"category": "전류", "unit": "장", "cal": 240, "carbs": 38.0, "protein": 4.0, "fat": 8.0, "sugar": 1.0, "sodium": 350},
    "김치전": {"category": "전류", "unit": "장", "cal": 280, "carbs": 34.0, "protein": 7.0, "fat": 13.0, "sugar": 2.5, "sodium": 780},
    "동그랑땡": {"category": "전류", "unit": "접시(5개)", "cal": 220, "carbs": 12.0, "protein": 14.0, "fat": 13.0, "sugar": 1.5, "sodium": 450},
    "생선전": {"category": "전류", "unit": "접시", "cal": 190, "carbs": 8.0, "protein": 18.0, "fat": 9.5, "sugar": 0.5, "sodium": 410},
    "파전": {"category": "전류", "unit": "장", "cal": 340, "carbs": 42.0, "protein": 12.0, "fat": 14.0, "sugar": 3.0, "sodium": 690},
    "호박전": {"category": "전류", "unit": "접시", "cal": 150, "carbs": 16.0, "protein": 4.0, "fat": 7.5, "sugar": 2.5, "sodium": 320},
    "새우튀김": {"category": "튀김류", "unit": "개(3개)", "cal": 240, "carbs": 18.0, "protein": 12.0, "fat": 13.5, "sugar": 1.0, "sodium": 420},
    "오징어튀김": {"category": "튀김류", "unit": "개(3개)", "cal": 260, "carbs": 22.0, "protein": 14.0, "fat": 12.5, "sugar": 1.0, "sodium": 450},
    "고추튀김": {"category": "튀김류", "unit": "개(2개)", "cal": 190, "carbs": 16.0, "protein": 8.0, "fat": 10.0, "sugar": 1.5, "sodium": 380},
    "도토리묵": {"category": "무침류", "unit": "접시", "cal": 90, "carbs": 18.0, "protein": 1.5, "fat": 1.0, "sugar": 2.0, "sodium": 490},
    "경단": {"category": "떡/한과", "unit": "알(5개)", "cal": 180, "carbs": 38.0, "protein": 3.5, "fat": 1.0, "sugar": 12.0, "sodium": 120},
    "꿀떡": {"category": "떡/한과", "unit": "알(5개)", "cal": 195, "carbs": 44.0, "protein": 2.5, "fat": 0.5, "sugar": 16.0, "sodium": 110},
    "송편": {"category": "떡/한과", "unit": "알(5개)", "cal": 220, "carbs": 48.0, "protein": 3.5, "fat": 1.2, "sugar": 14.0, "sodium": 130},
    "약과": {"category": "떡/한과", "unit": "개", "cal": 140, "carbs": 21.0, "protein": 1.2, "fat": 5.5, "sugar": 9.0, "sodium": 40},
    "식혜": {"category": "음료", "unit": "캔/잔", "cal": 120, "carbs": 29.0, "protein": 0.5, "fat": 0.1, "sugar": 24.0, "sodium": 15}
}

# ==============================================================================
# [3] 3중 앙상블 모델 로드 및 추론
# ==============================================================================
@st.cache_resource
def load_triple_ensemble_models():
    # 1. 150종 한식 모델 (Small)
    m_150 = YOLO("best.pt") if os.path.exists("best.pt") else YOLO("yolov8s.pt")
    # 2. 55종 한식 모델 (Nano)
    m_55 = YOLO("best1.pt") if os.path.exists("best1.pt") else None
    # 3. 기본 COCO 80종 모델 (과일/간식 보조용)
    m_base = YOLO("yolov8n.pt")
    return m_150, m_55, m_base

def run_triple_ensemble(image, conf_val=0.08, iou_val=0.45, imgsz_val=960):
    m_150, m_55, m_base = load_triple_ensemble_models()
    
    # 세 모델을 고해상도로 각각 추론
    res_150 = m_150(image, conf=conf_val, imgsz=imgsz_val, verbose=False)[0]
    res_base = m_base(image, conf=conf_val, imgsz=imgsz_val, verbose=False)[0]
    res_55 = m_55(image, conf=conf_val, imgsz=imgsz_val, verbose=False)[0] if m_55 else None

    all_boxes, all_scores, all_meta = [], [], []

    # [1] 150종 한식 모델 결과 (최우선 가중치 +1.0)
    for box in res_150.boxes:
        cls_id = int(box.cls[0])
        name = m_150.names[cls_id]
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        all_boxes.append(xyxy)
        all_scores.append(conf + 1.0)
        all_meta.append({
            "name": name,
            "conf": conf * 100,
            "box": xyxy,
            "source": "한식150(best)"
        })

    # [2] 55종 한식 모델 결과 (중간 가중치 +0.5)
    if res_55:
        for box in res_55.boxes:
            cls_id = int(box.cls[0])
            en_name = m_55.names[cls_id]
            if en_name in BEST1_KO_MAP:
                ko_name = BEST1_KO_MAP[en_name]
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                all_boxes.append(xyxy)
                all_scores.append(conf + 0.5)
                all_meta.append({
                    "name": ko_name,
                    "conf": conf * 100,
                    "box": xyxy,
                    "source": "한식55(best1)"
                })

    # [3] COCO 모델 (과일/간식 필터링)
    for box in res_base.boxes:
        cls_id = int(box.cls[0])
        en_name = m_base.names[cls_id]
        if en_name in COCO_KO_MAP:
            ko_name = COCO_KO_MAP[en_name]
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            all_boxes.append(xyxy)
            all_scores.append(conf)
            all_meta.append({
                "name": ko_name,
                "conf": conf * 100,
                "box": xyxy,
                "source": "일반(yolov8n)"
            })

    detected_items = []
    annotated_img = image.copy()
    draw = ImageDraw.Draw(annotated_img)

    if all_boxes:
        b_tensor = torch.tensor(all_boxes, dtype=torch.float32)
        s_tensor = torch.tensor(all_scores, dtype=torch.float32)
        # NMS로 중복 영역 제거 (가장 신뢰도/가중치가 높은 모델 결과 우선 보존)
        keep = nms(b_tensor, s_tensor, iou_val).tolist()

        w, h = image.size
        for idx in keep:
            item = all_meta[idx]
            x1, y1, x2, y2 = map(int, item["box"])
            crop_box = (max(0, x1), max(0, y1), min(w, x2), min(h, y2))
            crop_img = image.crop(crop_box) if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1] else None
            item["crop"] = crop_img
            detected_items.append(item)

            # 박스 색상 구분 (150종: 초록, 55종: 주황, COCO: 파랑)
            color = "#28a745" if "150" in item["source"] else ("#ffc107" if "55" in item["source"] else "#17a2b8")
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            draw.text((x1 + 4, max(0, y1 - 16)), f"{item['name']} ({item['conf']:.0f}%)", fill=color)

    return detected_items, annotated_img

# ==============================================================================
# [4] 가상 데이터 생성 및 세션 초기화
# ==============================================================================
def generate_mock_meals(count=20):
    sample_keys = list(NUTRITION_DB.keys())
    mock_data = []
    base_date = datetime.now()
    
    for _ in range(count):
        target_date = base_date - timedelta(days=random.randint(0, 6))
        meal_type = random.choice(["아침", "점심", "저녁", "간식/야식"])
        hour = random.randint(7, 21)
        minute = random.randint(10, 55)
        time_str = f"{target_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
        
        food_name = random.choice(sample_keys)
        item = NUTRITION_DB[food_name]
        portion = random.choice([0.5, 1.0, 1.0, 1.5])
        
        mock_data.append({
            "데이터구분": "가상생성",
            "기록일시": time_str,
            "날짜": target_date.strftime('%Y-%m-%d'),
            "식사구분": meal_type,
            "음식명": food_name,
            "섭취수량": f"{portion} {item['unit']}",
            "칼로리(kcal)": round(item["cal"] * portion, 1),
            "탄수화물(g)": round(item["carbs"] * portion, 1),
            "단백질(g)": round(item["protein"] * portion, 1),
            "지방(g)": round(item["fat"] * portion, 1),
            "당류(g)": round(item["sugar"] * portion, 1),
            "나트륨(mg)": int(item["sodium"] * portion)
        })
    mock_data.sort(key=lambda x: x["기록일시"], reverse=True)
    return mock_data

if "initialized" not in st.session_state:
    st.session_state.meal_history = generate_mock_meals(20)
    st.session_state.initialized = True
elif "meal_history" not in st.session_state:
    st.session_state.meal_history = []

if "last_added_message" not in st.session_state:
    st.session_state.last_added_message = None

# ==============================================================================
# [5] 사이드바 네비게이션 & 실시간 AI 파라미터 조절
# ==============================================================================
st.sidebar.title("📌 네비게이션")
view_mode = st.sidebar.radio("화면 모드", ["📷 음식 사진 분석 및 추가", "📊 종합 통계 대시보드"])

st.sidebar.write("---")
st.sidebar.subheader("⚙️ AI 3중 앙상블 탐지 설정")
conf_threshold = st.sidebar.slider("AI 감지 신뢰도(Conf) 기준", 0.01, 0.40, 0.08, 0.01, help="낮출수록 더 많은 음식을 민감하게 찾아냅니다.")
iou_threshold = st.sidebar.slider("중복 제거(IoU) 기준", 0.20, 0.70, 0.45, 0.05, help="인접한 반찬이 지워지지 않도록 조정합니다.")
imgsz_choice = st.sidebar.select_slider("분석 해상도(imgsz)", options=[640, 800, 960, 1024, 1280], value=960, help="해상도가 클수록 작은 반찬을 선명하게 감지합니다.")

st.sidebar.write("---")
st.sidebar.subheader("🎲 가상 데이터 관리")
mock_count = st.sidebar.slider("추가할 가상 데이터 수", 5, 30, 10, 5)

if st.sidebar.button("✨ 가상 식단 데이터 추가 생성"):
    st.session_state.meal_history.extend(generate_mock_meals(mock_count))
    st.session_state.meal_history.sort(key=lambda x: x["기록일시"], reverse=True)
    st.sidebar.success(f"{mock_count}건의 식단이 추가되었습니다!")
    st.rerun()

if st.sidebar.button("🗑️ 전체 데이터 비우기"):
    st.session_state.meal_history = []
    st.session_state.last_added_message = None
    st.sidebar.warning("데이터가 모두 삭제되었습니다.")
    st.rerun()

daily_goal = st.sidebar.number_input("🎯 1일 목표 칼로리 (kcal)", 1200, 3500, 2000, 100)

# ==============================================================================
# [6] 화면 1: 다중 사진 분석 및 3중 앙상블 음식 감지
# ==============================================================================
if view_mode == "📷 음식 사진 분석 및 추가":
    st.title("📷 AI 3중 앙상블 다중 음식 감지 & 식단 등록")
    st.caption("🟢 초록색: 150종 한식 / 🟡 노란색: 55종 한식 / 🔵 파란색: 일반 과일·양식 모델")

    if st.session_state.last_added_message:
        st.success(st.session_state.last_added_message)
        if st.button("알림 닫기"):
            st.session_state.last_added_message = None
            st.rerun()

    input_source = st.radio("이미지 입력 방식:", ["📂 시연용 샘플 이미지 선택", "💻 내 컴퓨터에서 업로드"], horizontal=True)
    
    images_to_process = []
    sample_dir = "samples"
    
    if input_source == "📂 시연용 샘플 이미지 선택":
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)
        sample_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if sample_files:
            selected_samples = st.multiselect("샘플 사진을 선택하세요:", options=sample_files, default=[sample_files[0]])
            for file_name in selected_samples:
                img_path = os.path.join(sample_dir, file_name)
                images_to_process.append((file_name, Image.open(img_path).convert("RGB")))
        else:
            st.info("💡 `samples/` 폴더에 사진들을 넣어두면 간편하게 선택할 수 있습니다.")
    else:
        uploaded_files = st.file_uploader("음식 사진을 선택하세요 (여러 장 가능)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        if uploaded_files:
            for up_file in uploaded_files:
                images_to_process.append((up_file.name, Image.open(up_file).convert("RGB")))

    if images_to_process:
        st.write("---")
        global_meal_slot = st.selectbox("🕒 식사 구분 (일괄 적용)", ["아침", "점심", "저녁", "간식/야식"], index=1)
        staged_records = []
        
        for img_idx, (img_title, img_obj) in enumerate(images_to_process):
            st.markdown(f"### 🖼️ [사진 {img_idx+1}] {img_title}")
            
            # 3중 앙상블 추론 실행
            detected_items, annotated_img = run_triple_ensemble(
                img_obj,
                conf_val=conf_threshold,
                iou_val=iou_threshold,
                imgsz_val=imgsz_choice
            )

            # 1단계: 1차 탐색 결과 브리핑
            col_img, col_summary = st.columns([1.3, 1], gap="medium")
            with col_img:
                st.image(annotated_img, caption="🎯 AI 3중 앙상블 객체 탐색 결과", use_container_width=True)
            with col_summary:
                st.markdown("#### 🔍 1차 탐색 요약")
                if not detected_items:
                    st.warning("⚠️ 사진에서 인식된 음식이 없습니다. 사이드바의 감도 기준을 낮추거나 아래에서 수동으로 선택해 주세요.")
                else:
                    st.success(f"총 **{len(detected_items)}개**의 음식을 발견했습니다!")
                    tags = [f"**{it['name']}** ({it['conf']:.0f}%)" for it in detected_items]
                    st.markdown("발견된 음식: " + " · ".join(tags))
                    
                    thumb_cols = st.columns(min(len(detected_items), 4))
                    for t_idx, it in enumerate(detected_items[:4]):
                        with thumb_cols[t_idx]:
                            if it["crop"]:
                                st.image(it["crop"], caption=it["name"], use_container_width=True)

            # 2단계: 개별 음식 메뉴 확인 및 수량 조절
            with st.expander("✏️ 각 음식별 상세 메뉴 및 섭취량 조절", expanded=True):
                all_foods = list(NUTRITION_DB.keys())
                
                if not detected_items:
                    food_key = st.selectbox(
                        "메뉴 수동 선택",
                        options=all_foods,
                        format_func=lambda k: f"{k} ({NUTRITION_DB[k]['category']})",
                        key=f"manual_{img_idx}"
                    )
                    item = NUTRITION_DB[food_key]
                    portion = st.number_input(f"섭취 수량 ({item['unit']})", min_value=0.5, max_value=5.0, value=1.0, step=0.5, key=f"p_man_{img_idx}")
                    
                    staged_records.append({
                        "데이터구분": "직접입력", "식사구분": global_meal_slot, "음식명": food_key,
                        "섭취수량": f"{portion} {item['unit']}",
                        "칼로리(kcal)": round(item["cal"] * portion, 1),
                        "탄수화물(g)": round(item["carbs"] * portion, 1),
                        "단백질(g)": round(item["protein"] * portion, 1),
                        "지방(g)": round(item["fat"] * portion, 1),
                        "당류(g)": round(item["sugar"] * portion, 1),
                        "나트륨(mg)": int(item["sodium"] * portion)
                    })
                else:
                    for it_idx, it in enumerate(detected_items):
                        c_crop, c_detail = st.columns([1, 3])
                        with c_crop:
                            if it["crop"]:
                                st.image(it["crop"], caption=f"#{it_idx+1} {it['name']}", use_container_width=True)
                        with c_detail:
                            def_idx = all_foods.index(it["name"]) if it["name"] in all_foods else 0
                            sel_food = st.selectbox(
                                f"#{it_idx+1} 메뉴 확인/수정",
                                options=all_foods,
                                index=def_idx,
                                format_func=lambda k: f"{k} ({NUTRITION_DB[k]['category']})",
                                key=f"menu_{img_idx}_{it_idx}"
                            )
                            item = NUTRITION_DB[sel_food]
                            portion = st.number_input(
                                f"수량 ({item['unit']})",
                                min_value=0.5, max_value=5.0, value=1.0, step=0.5,
                                key=f"portion_{img_idx}_{it_idx}"
                            )
                            
                            c_cal = round(item["cal"] * portion, 1)
                            st.caption(f"🔥 **{c_cal} kcal** | 탄 {round(item['carbs']*portion, 1)}g | 단 {round(item['protein']*portion, 1)}g | 지 {round(item['fat']*portion, 1)}g | 나트륨 {int(item['sodium']*portion)}mg")
                            
                            staged_records.append({
                                "데이터구분": "직접입력", "식사구분": global_meal_slot, "음식명": sel_food,
                                "섭취수량": f"{portion} {item['unit']}",
                                "칼로리(kcal)": c_cal,
                                "탄수화물(g)": round(item["carbs"] * portion, 1),
                                "단백질(g)": round(item["protein"] * portion, 1),
                                "지방(g)": round(item["fat"] * portion, 1),
                                "당류(g)": round(item["sugar"] * portion, 1),
                                "나트륨(mg)": int(item["sodium"] * portion)
                            })
                        st.write("---")

        # 3단계: 식단 일괄 등록
        if staged_records:
            total_cal = sum(r["칼로리(kcal)"] for r in staged_records)
            btn_label = f"🚀 감지된 총 {len(staged_records)}개 음식 일괄 등록하기 (총 {total_cal:,.1f} kcal)"
            
            if st.button(btn_label, type="primary", use_container_width=True):
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M")
                date_str = now.strftime("%Y-%m-%d")
                
                names = []
                for r in staged_records:
                    r["기록일시"] = now_str
                    r["날짜"] = date_str
                    st.session_state.meal_history.insert(0, r)
                    names.append(r["음식명"])
                    
                st.session_state.last_added_message = (
                    f"✅ **[일괄 등록 성공]** 총 {len(staged_records)}개 품목({', '.join(names)})이 "
                    f"오늘의 **[{global_meal_slot}]** 식단으로 정상 저장되었습니다!"
                )
                st.rerun()

# ==============================================================================
# [7] 화면 2: 대시보드
# ==============================================================================
elif view_mode == "📊 종합 통계 대시보드":
    st.title("📊 다이어트 영양 통계 대시보드")
    
    if not st.session_state.meal_history:
        st.info("데이터가 비어 있습니다. 사진을 등록하거나 사이드바에서 가상 데이터를 생성하세요.")
    else:
        df = pd.DataFrame(st.session_state.meal_history)
        
        tot_cal = round(df["칼로리(kcal)"].sum(), 1)
        tot_carbs = round(df["탄수화물(g)"].sum(), 1)
        tot_protein = round(df["단백질(g)"].sum(), 1)
        tot_fat = round(df["지방(g)"].sum(), 1)
        
        st.markdown(f"### 📈 누적 식단 데이터 현황 (총 {len(df)}건)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("누적 섭취 칼로리", f"{tot_cal:,} kcal")
        c2.metric("누적 탄수화물", f"{tot_carbs:,} g")
        c3.metric("누적 단백질", f"{tot_protein:,} g")
        c4.metric("누적 지방", f"{tot_fat:,} g")
        st.write("---")

        st.subheader("📅 최근 일자별 칼로리 섭취 추이")
        daily_df = df.groupby("날짜")["칼로리(kcal)"].sum().reset_index().sort_values("날짜")
        fig_daily = px.line(daily_df, x="날짜", y="칼로리(kcal)", markers=True, title="일자별 칼로리 변화")
        fig_daily.add_hline(y=daily_goal, line_dash="dash", line_color="red", annotation_text="목표 칼로리")
        fig_daily.update_layout(height=320, margin=dict(t=30, b=20, l=10, r=10))
        st.plotly_chart(fig_daily, use_container_width=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("🍽️ 식사 구분별 총 섭취량")
            meal_grp = df.groupby("식사구분")["칼로리(kcal)"].sum().reset_index()
            fig_bar = px.bar(
                meal_grp, x="식사구분", y="칼로리(kcal)", color="식사구분",
                category_orders={"식사구분": ["아침", "점심", "저녁", "간식/야식"]}
            )
            fig_bar.update_layout(height=300, showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_c2:
            st.subheader("⚖️ 전체 탄·단·지 칼로리 구성 비율")
            macro_cal = pd.DataFrame({
                "영양소": ["탄수화물", "단백질", "지방"],
                "열량": [tot_carbs * 4, tot_protein * 4, tot_fat * 9]
            })
            fig_pie = px.pie(
                macro_cal, values="열량", names="영양소", hole=0.45, color="영양소",
                color_discrete_map={"탄수화물": "#4CAF50", "단백질": "#2196F3", "지방": "#FF9800"}
            )
            fig_pie.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.write("---")
        st.subheader("📋 전체 식사 히스토리 테이블")
        st.caption("🟢 **초록색으로 칠해진 행**은 사용자가 사진으로 직접 등록한 실제 데이터입니다.")

        def highlight_real_data(row):
            if row["데이터구분"] == "직접입력":
                return ["background-color: #d4edda; color: #155724; font-weight: bold;"] * len(row)
            return [""] * len(row)

        styled_df = df.style.apply(highlight_real_data, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        csv_file = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 전체 식단 CSV 다운로드",
            data=csv_file,
            file_name=f"diet_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )