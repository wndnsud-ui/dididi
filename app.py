import os
import random
from datetime import datetime, timedelta
import yaml
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image, ImageDraw
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
# ==============================================================================
# [3] CSV 영양 데이터 로드
# ==============================================================================
@st.cache_data
def load_nutrition_db(csv_path, csv_modified_time):
    required_columns = {"food_name", "category", "unit", "cal", "carbs", "protein", "fat", "sugar", "sodium"}

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"영양 데이터 CSV 파일이 없습니다: {csv_path}")

    nutrition_df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing_columns = required_columns - set(nutrition_df.columns)
    if missing_columns:
        raise ValueError(f"영양 데이터 CSV에 필요한 컬럼이 없습니다: {sorted(missing_columns)}")

    nutrition_df = nutrition_df.copy()
    nutrition_df["food_name"] = nutrition_df["food_name"].astype(str).str.strip()
    nutrition_df = nutrition_df[nutrition_df["food_name"] != ""]

    numeric_columns = ["cal", "carbs", "protein", "fat", "sugar", "sodium"]
    for column in numeric_columns:
        nutrition_df[column] = pd.to_numeric(nutrition_df[column], errors="coerce").fillna(0.0)

    return {
        row["food_name"]: {
            "category": row["category"],
            "unit": row["unit"],
            "cal": row["cal"],
            "carbs": row["carbs"],
            "protein": row["protein"],
            "fat": row["fat"],
            "sugar": row["sugar"],
            "sodium": row["sodium"]
        }
        for _, row in nutrition_df.iterrows()
    }


NUTRITION_CSV_PATH = os.path.join(os.path.dirname(__file__), "CaloDetect_nutrition_all_matched.csv")
if not os.path.exists(NUTRITION_CSV_PATH):
    raise FileNotFoundError(f"영양 데이터 CSV 파일이 없습니다: {NUTRITION_CSV_PATH}")

NUTRITION_DB = load_nutrition_db(
    NUTRITION_CSV_PATH,
    os.path.getmtime(NUTRITION_CSV_PATH)
)

# ============================================================================== 
# [4] 5차 단일 모델 로드 및 추론
# ============================================================================== 
@st.cache_resource
def load_5th_model():
    model_path = "best.pt"
    data_path = "5차data.yaml"

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"필수 모델 파일이 없습니다: {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"필수 데이터 설정 파일이 없습니다: {data_path}")

    with open(data_path, "r", encoding="utf-8") as yaml_file:
        data_config = yaml.safe_load(yaml_file)

    yaml_names = data_config["names"]
    if isinstance(yaml_names, dict):
        yaml_names = [yaml_names[index] for index in range(data_config["nc"])]

    if len(yaml_names) != data_config["nc"]:
        raise ValueError("5차data.yaml의 nc와 names 개수가 다릅니다.")

    model = YOLO(model_path)
    model_names = [model.names[index] for index in range(len(model.names))]
    if model_names != yaml_names:
        raise ValueError("5차best.pt의 클래스 순서 또는 이름이 5차data.yaml과 다릅니다.")

    return model, yaml_names

def run_5th_model(image, conf_val=0.08, iou_val=0.45, imgsz_val=960):
    model, class_names = load_5th_model()
    
    result = model(image, conf=conf_val, iou=iou_val, imgsz=imgsz_val, verbose=False)[0]
    detected_items = []
    annotated_img = image.copy()
    draw = ImageDraw.Draw(annotated_img)

    for box in result.boxes:
        cls_id = int(box.cls[0])
        name = class_names[cls_id]
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = map(int, xyxy)
        w, h = image.size
        crop_box = (max(0, x1), max(0, y1), min(w, x2), min(h, y2))
        crop_img = image.crop(crop_box) if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1] else None
        detected_items.append({
            "name": name,
            "conf": conf * 100,
            "box": xyxy,
            "source": "한식59(5차best)",
            "crop": crop_img
        })
        draw.rectangle([x1, y1, x2, y2], outline="#28a745", width=3)
        draw.text((x1 + 4, max(0, y1 - 16)), f"{name} ({conf * 100:.0f}%)", fill="#28a745")

    return detected_items, annotated_img

# ==============================================================================
# [5] 가상 데이터 생성 및 세션 초기화
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
# [6] 사이드바 네비게이션 & 실시간 AI 파라미터 조절
# ==============================================================================
st.sidebar.title("📌 네비게이션")
view_mode = st.sidebar.radio("화면 모드", ["📷 음식 사진 분석 및 추가", "📊 종합 통계 대시보드"])

st.sidebar.write("---")
st.sidebar.subheader("⚙️ AI 5차 모델 탐지 설정")
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
# [7] 화면 1: 다중 사진 분석 및 5차 모델 음식 감지
# ==============================================================================
if view_mode == "📷 음식 사진 분석 및 추가":
    st.title("📷 AI 5차 모델 다중 음식 감지 & 식단 등록")
    st.caption("🟢 초록색: 5차 59종 한식")

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
            
            # 5차 모델 기반 추론 실행
            detected_items, annotated_img = run_5th_model(
                img_obj,
                conf_val=conf_threshold,
                iou_val=iou_threshold,
                imgsz_val=imgsz_choice
            )

            # 1단계: 1차 탐색 결과 브리핑
            col_img, col_summary = st.columns([1.3, 1], gap="medium")
            with col_img:
                st.image(annotated_img, caption="🎯 AI 5차 모델 객체 탐색 결과", use_container_width=True)
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
# [8] 화면 2: 대시보드
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