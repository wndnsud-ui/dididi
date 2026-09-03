import os
import random
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from ultralytics import YOLO

# ==============================================================================
# [1] 웹 페이지 설정
# ==============================================================================
st.set_page_config(
    page_title="AI 맞춤형 식단 다이어리 & 대시보드",
    page_icon="🥗",
    layout="wide"
)

# ==============================================================================
# [2] 세분화 영양 데이터베이스
# ==============================================================================
NUTRITION_DB = {
    # 피자류
    "pizza_pepperoni": {"name": "페퍼로니 피자", "category": "패스트푸드", "unit": "조각", "cal": 298, "carbs": 32.0, "protein": 13.0, "fat": 13.5, "sugar": 3.8, "sodium": 680},
    "pizza_cheese": {"name": "치즈 피자", "category": "패스트푸드", "unit": "조각", "cal": 272, "carbs": 33.5, "protein": 12.2, "fat": 9.8, "sugar": 4.1, "sodium": 540},
    "pizza_combination": {"name": "콤비네이션 피자", "category": "패스트푸드", "unit": "조각", "cal": 310, "carbs": 34.0, "protein": 13.8, "fat": 14.0, "sugar": 4.5, "sodium": 650},
    
    # 샌드위치/간편식
    "sandwich_chicken": {"name": "치킨 텐더 샌드위치", "category": "간편식", "unit": "개", "cal": 420, "carbs": 44.0, "protein": 22.0, "fat": 17.5, "sugar": 5.2, "sodium": 890},
    "sandwich_egg": {"name": "에그 마요 샌드위치", "category": "간편식", "unit": "개", "cal": 390, "carbs": 38.0, "protein": 12.5, "fat": 21.0, "sugar": 4.0, "sodium": 720},
    "hotdog_classic": {"name": "클래식 핫도그", "category": "패스트푸드", "unit": "개", "cal": 290, "carbs": 24.0, "protein": 10.0, "fat": 16.0, "sugar": 4.0, "sodium": 680},

    # 한식/식사류 (그릇 요리)
    "bowl_bibimbap": {"name": "전주 비빔밥", "category": "한식", "unit": "그릇", "cal": 585, "carbs": 98.0, "protein": 20.0, "fat": 13.0, "sugar": 9.5, "sodium": 1150},
    "bowl_jeyuk": {"name": "제육 덮밥", "category": "한식", "unit": "그릇", "cal": 680, "carbs": 88.0, "protein": 32.0, "fat": 22.0, "sugar": 12.0, "sodium": 1380},
    "bowl_kimchi_jjigae": {"name": "김치찌개 정식", "category": "한식", "unit": "인분", "cal": 510, "carbs": 74.0, "protein": 26.0, "fat": 12.0, "sugar": 6.0, "sodium": 1960},
    "bowl_ramen": {"name": "라면 (계란 포함)", "category": "면류", "unit": "그릇", "cal": 520, "carbs": 82.0, "protein": 12.0, "fat": 16.0, "sugar": 4.0, "sodium": 1780},

    # 과일/채소류
    "apple_fuji": {"name": "사과 (후지)", "category": "과일", "unit": "개", "cal": 105, "carbs": 27.5, "protein": 0.6, "fat": 0.3, "sugar": 21.0, "sodium": 2},
    "banana_standard": {"name": "바나나", "category": "과일", "unit": "개", "cal": 105, "carbs": 27.0, "protein": 1.3, "fat": 0.3, "sugar": 14.4, "sodium": 1},
    "orange_sweet": {"name": "오렌지", "category": "과일", "unit": "개", "cal": 62, "carbs": 15.0, "protein": 1.2, "fat": 0.2, "sugar": 12.0, "sodium": 0},
    "salad_chicken": {"name": "닭가슴살 샐러드", "category": "다이어트", "unit": "접시", "cal": 260, "carbs": 14.0, "protein": 28.0, "fat": 10.0, "sugar": 5.0, "sodium": 580},
    "broccoli_steamed": {"name": "데친 브로콜리", "category": "채소", "unit": "접시", "cal": 35, "carbs": 6.8, "protein": 2.8, "fat": 0.4, "sugar": 1.4, "sodium": 33},

    # 디저트 및 음료류
    "cake_piece": {"name": "조각 케이크", "category": "디저트", "unit": "조각", "cal": 350, "carbs": 45.0, "protein": 4.0, "fat": 18.0, "sugar": 28.0, "sodium": 220},
    "donut_glazed": {"name": "글레이즈드 도넛", "category": "디저트", "unit": "개", "cal": 250, "carbs": 30.0, "protein": 3.0, "fat": 14.0, "sugar": 15.0, "sodium": 190},
    "cup_americano": {"name": "아이스 아메리카노", "category": "음료", "unit": "잔", "cal": 10, "carbs": 1.5, "protein": 0.8, "fat": 0.1, "sugar": 0.0, "sodium": 5},
    "cup_latte": {"name": "카페 라떼", "category": "음료", "unit": "잔", "cal": 180, "carbs": 14.0, "protein": 10.0, "fat": 9.5, "sugar": 13.0, "sodium": 115},
    "bottle_cola_zero": {"name": "제로 콜라", "category": "음료", "unit": "캔", "cal": 0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sugar": 0.0, "sodium": 28}
}

YOLO_TO_DETAIL_MAP = {
    "pizza": ["pizza_pepperoni", "pizza_cheese", "pizza_combination"],
    "sandwich": ["sandwich_chicken", "sandwich_egg"],
    "hot dog": ["hotdog_classic"],
    "bowl": ["bowl_bibimbap", "bowl_jeyuk", "bowl_kimchi_jjigae", "bowl_ramen"],
    "apple": ["apple_fuji"],
    "banana": ["banana_standard"],
    "orange": ["orange_sweet"],
    "broccoli": ["salad_chicken", "broccoli_steamed"],
    "cake": ["cake_piece"],
    "donut": ["donut_glazed"],
    "cup": ["cup_americano", "cup_latte"],
    "bottle": ["bottle_cola_zero"]
}

# ==============================================================================
# [3] 가상 데이터 생성 함수
# ==============================================================================
def generate_mock_meals(count=30):
    meal_slots = {
        "아침": ["apple_fuji", "sandwich_egg", "banana_standard", "broccoli_steamed", "cup_americano"],
        "점심": ["bowl_bibimbap", "bowl_jeyuk", "bowl_kimchi_jjigae", "bowl_ramen", "sandwich_chicken"],
        "저녁": ["pizza_pepperoni", "pizza_cheese", "pizza_combination", "salad_chicken", "bowl_jeyuk"],
        "간식/야식": ["cake_piece", "donut_glazed", "cup_latte", "bottle_cola_zero", "banana_standard"]
    }
    
    mock_data = []
    base_date = datetime.now()
    
    for _ in range(count):
        days_ago = random.randint(0, 6)
        target_date = base_date - timedelta(days=days_ago)
        meal_type = random.choice(["아침", "점심", "저녁", "간식/야식"])
        
        if meal_type == "아침":
            hour, minute = random.randint(7, 9), random.randint(10, 55)
        elif meal_type == "점심":
            hour, minute = random.randint(12, 13), random.randint(10, 55)
        elif meal_type == "저녁":
            hour, minute = random.randint(18, 20), random.randint(10, 55)
        else:
            hour, minute = random.randint(14, 16), random.randint(10, 55)
            
        time_str = f"{target_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
        
        food_key = random.choice(meal_slots[meal_type])
        item = NUTRITION_DB[food_key]
        portion_mult = random.choice([0.5, 1.0, 1.0, 1.0, 1.5, 2.0])
        
        mock_data.append({
            "데이터구분": "가상생성",
            "기록일시": time_str,
            "날짜": target_date.strftime('%Y-%m-%d'),
            "식사구분": meal_type,
            "음식명": item["name"],
            "섭취수량": f"{portion_mult} {item['unit']}",
            "칼로리(kcal)": round(item["cal"] * portion_mult, 1),
            "탄수화물(g)": round(item["carbs"] * portion_mult, 1),
            "단백질(g)": round(item["protein"] * portion_mult, 1),
            "지방(g)": round(item["fat"] * portion_mult, 1),
            "당류(g)": round(item["sugar"] * portion_mult, 1),
            "나트륨(mg)": int(item["sodium"] * portion_mult)
        })
        
    mock_data.sort(key=lambda x: x["기록일시"], reverse=True)
    return mock_data

# 세션 초기화
if "initialized" not in st.session_state:
    st.session_state.meal_history = generate_mock_meals(30)
    st.session_state.initialized = True
elif "meal_history" not in st.session_state:
    st.session_state.meal_history = []

if "last_added_message" not in st.session_state:
    st.session_state.last_added_message = None

# ==============================================================================
# [4] 모델 로드
# ==============================================================================
@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt")

model = load_yolo()

# ==============================================================================
# [5] 사이드바 메뉴 & 제어
# ==============================================================================
st.sidebar.title("📌 네비게이션")
view_mode = st.sidebar.radio("화면 모드", ["📷 음식 사진 분석 및 추가", "📊 종합 통계 대시보드"])

st.sidebar.write("---")
st.sidebar.subheader("🎲 가상 데이터 관리")
mock_count = st.sidebar.slider("추가할 가상 데이터 수", 10, 50, 20, 5)

if st.sidebar.button("✨ 가상 식단 데이터 추가 생성"):
    new_data = generate_mock_meals(mock_count)
    st.session_state.meal_history.extend(new_data)
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
# [6] 화면 1: 다중 사진 분석 및 식단 등록 (핵심 수정)
# ==============================================================================
if view_mode == "📷 음식 사진 분석 및 추가":
    st.title("📷 AI 다중 음식 사진 분석 & 식단 등록")
    st.caption("여러 장의 음식 사진을 한 번에 올리고 각각의 메뉴와 수량을 확인한 뒤 일괄 등록하세요.")

    if st.session_state.last_added_message:
        st.success(st.session_state.last_added_message)
        if st.button("알림 닫기"):
            st.session_state.last_added_message = None
            st.rerun()

    input_source = st.radio(
        "이미지 입력 방식:",
        ["📂 시연용 샘플 이미지 다중 선택", "💻 내 컴퓨터에서 여러 장 업로드"],
        horizontal=True
    )
    
    # 여러 이미지를 (파일명, PIL Image) 튜플 리스트로 보관
    images_to_process = []
    sample_dir = "samples"
    
    if input_source == "📂 시연용 샘플 이미지 다중 선택":
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)
            
        sample_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if sample_files:
            # 다중 선택 지원 (multiselect)
            selected_samples = st.multiselect(
                "시연할 샘플 사진들을 선택하세요 (여러 개 선택 가능):", 
                options=sample_files,
                default=[sample_files[0]] if sample_files else []
            )
            for file_name in selected_samples:
                img_path = os.path.join(sample_dir, file_name)
                images_to_process.append((file_name, Image.open(img_path).convert("RGB")))
        else:
            st.info("💡 `samples/` 폴더에 사진들을 넣어두면 여러 장을 동시에 선택할 수 있습니다.")
    else:
        # 파일 업로더에서 여러 파일 선택 허용 (accept_multiple_files=True)
        uploaded_files = st.file_uploader(
            "음식 사진들을 선택하세요 (Ctrl/Shift 키를 누르고 여러 장 선택 가능)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True
        )
        if uploaded_files:
            for up_file in uploaded_files:
                images_to_process.append((up_file.name, Image.open(up_file).convert("RGB")))

    # 사진이 1장 이상 준비되었을 때 처리
    if len(images_to_process) > 0:
        st.write("---")
        st.subheader(f"🔍 총 {len(images_to_process)}장의 사진이 감지되었습니다. 각각의 정보를 확인하세요.")
        
        # 공통 적용 식사 구분
        global_meal_slot = st.selectbox(
            "🕒 식사 구분 (선택한 모든 음식에 일괄 적용)",
            ["아침", "점심", "저녁", "간식/야식"],
            index=1
        )
        
        # 일괄 등록 시 저장할 데이터를 모으는 리스트
        staged_records = []
        
        # 각 사진별로 Expander 카드 형태로 배치하여 개별 확인/조정
        for idx, (img_title, img_obj) in enumerate(images_to_process):
            with st.expander(f"📷 [{idx+1}/{len(images_to_process)}] {img_title}", expanded=True):
                c_img, c_info = st.columns([1, 1.5], gap="medium")
                
                with c_img:
                    st.image(img_obj, use_container_width=True)
                
                with c_info:
                    # 각 이미지별 YOLO 추론
                    results = model(img_obj, conf=0.25)
                    detected_label = None
                    detected_conf = 0.0
                    
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0])
                        name = model.names[cls_id]
                        if name in YOLO_TO_DETAIL_MAP:
                            detected_label = name
                            detected_conf = float(box.conf[0]) * 100
                            break
                    
                    # 자동 감지 여부에 따라 메뉴 선택 분기
                    if detected_label:
                        st.success(f"AI 인식: **{detected_label}** ({detected_conf:.1f}%)")
                        selected_key = st.selectbox(
                            f"상세 메뉴 확인/변경 (사진 {idx+1})",
                            options=YOLO_TO_DETAIL_MAP[detected_label],
                            format_func=lambda x: f"{NUTRITION_DB[x]['name']} ({NUTRITION_DB[x]['category']})",
                            key=f"menu_{idx}"
                        )
                    else:
                        st.warning("⚠️ 음식 자동 감지 실패 (수동 선택)")
                        selected_key = st.selectbox(
                            f"메뉴 수동 선택 (사진 {idx+1})",
                            options=list(NUTRITION_DB.keys()),
                            format_func=lambda x: f"{NUTRITION_DB[x]['name']} ({NUTRITION_DB[x]['category']})",
                            key=f"menu_{idx}"
                        )
                        
                    item = NUTRITION_DB[selected_key]
                    
                    # 인분 배수 입력
                    portion = st.number_input(
                        f"섭취 수량 ({item['unit']})",
                        min_value=0.5,
                        max_value=5.0,
                        value=1.0,
                        step=0.5,
                        key=f"portion_{idx}"
                    )
                    
                    calc_cal = round(item["cal"] * portion, 1)
                    calc_carbs = round(item["carbs"] * portion, 1)
                    calc_protein = round(item["protein"] * portion, 1)
                    calc_fat = round(item["fat"] * portion, 1)
                    calc_sugar = round(item["sugar"] * portion, 1)
                    calc_sodium = int(item["sodium"] * portion)
                    
                    # 수치 요약 배너
                    st.caption(
                        f"🔥 **{calc_cal} kcal** | 탄수화물 {calc_carbs}g | 단백질 {calc_protein}g | 지방 {calc_fat}g | 나트륨 {calc_sodium}mg"
                    )
                    
                    # 임시 저장
                    staged_records.append({
                        "데이터구분": "직접입력",
                        "식사구분": global_meal_slot,
                        "음식명": item["name"],
                        "섭취수량": f"{portion} {item['unit']}",
                        "칼로리(kcal)": calc_cal,
                        "탄수화물(g)": calc_carbs,
                        "단백질(g)": calc_protein,
                        "지방(g)": calc_fat,
                        "당류(g)": calc_sugar,
                        "나트륨(mg)": calc_sodium
                    })

        st.write("---")
        
        # 일괄 등록 버튼
        total_batch_cal = sum(r["칼로리(kcal)"] for r in staged_records)
        btn_label = f"🚀 위 {len(staged_records)}개 음식 일괄 등록하기 (총 {total_batch_cal:,.1f} kcal)"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M")
            date_str = now.strftime("%Y-%m-%d")
            
            registered_names = []
            for r in staged_records:
                r["기록일시"] = now_str
                r["날짜"] = date_str
                st.session_state.meal_history.insert(0, r)
                registered_names.append(r["음식명"])
            
            names_summary = ", ".join(registered_names)
            st.session_state.last_added_message = (
                f"✅ **[일괄 등록 성공]** 총 {len(staged_records)}개 품목({names_summary})이 "
                f"오늘의 **[{global_meal_slot}]** 식단으로 정상 저장되었습니다! (대시보드에서 확인 가능)"
            )
            st.rerun()

# ==============================================================================
# [7] 화면 2: 종합 통계 대시보드
# ==============================================================================
elif view_mode == "📊 종합 통계 대시보드":
    st.title("📊 다이어트 영양 통계 대시보드")
    
    if not st.session_state.meal_history:
        st.info("데이터가 비어 있습니다. 사진을 분석해 추가하거나 사이드바에서 가상 데이터를 생성하세요.")
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

        # 1. 일자별 섭취 칼로리 추이
        st.subheader("📅 최근 일자별 칼로리 섭취 추이")
        daily_df = df.groupby("날짜")["칼로리(kcal)"].sum().reset_index().sort_values("날짜")
        fig_daily = px.line(
            daily_df,
            x="날짜",
            y="칼로리(kcal)",
            markers=True,
            title="일자별 칼로리 변화 (목표선: 빨간 점선)"
        )
        fig_daily.add_hline(y=daily_goal, line_dash="dash", line_color="red", annotation_text="목표 칼로리")
        fig_daily.update_layout(height=320, margin=dict(t=30, b=20, l=10, r=10))
        st.plotly_chart(fig_daily, use_container_width=True)

        # 2. 식사 구분별 칼로리 & 영양소 비율 2분할 차트
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("🍽️ 식사 구분별 총 섭취량")
            meal_grp = df.groupby("식사구분")["칼로리(kcal)"].sum().reset_index()
            fig_bar = px.bar(
                meal_grp,
                x="식사구분",
                y="칼로리(kcal)",
                color="식사구분",
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
                macro_cal,
                values="열량",
                names="영양소",
                hole=0.45,
                color="영양소",
                color_discrete_map={"탄수화물": "#4CAF50", "단백질": "#2196F3", "지방": "#FF9800"}
            )
            fig_pie.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        # 3. 전체 데이터 테이블 (직접 입력 데이터 초록색 하이라이트 유지)
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