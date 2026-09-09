import os  # 운영체제 파일 경로 및 존재 여부 확인용 라이브러리 임포트
import random  # 가상 데이터 생성 시 무작위 값 추출용 라이브러리 임포트
from datetime import datetime, timedelta  # 날짜 및 시간 계산용 라이브러리 임포트
import yaml  # 5차 모델 클래스 설정(YAML) 파일을 읽기 위한 라이브러리 임포트
import streamlit as st  # 웹 UI 및 대시보드 구성을 위한 Streamlit 프레임워크 임포트
import pandas as pd  # 식단 데이터 테이블 관리 및 그룹화 연산용 판다스 라이브러리 임포트
from PIL import Image, ImageDraw  # 업로드된 이미지 열기 및 바운딩 박스 드로잉용 라이브러리 임포트
from ultralytics import YOLO  # 5차 객체 탐지 비전 AI 모델 구동을 위한 라이브러리 임포트
from streamlit_echarts import st_echarts  # Apache ECharts 5 차트를 Streamlit에서 렌더링하기 위한 컴포넌트 임포트

# [1] 웹 페이지 기본 설정
st.set_page_config(
    page_title="AI 맞춤형 식단 다이어리 & 대시보드",  # 브라우저 탭에 표시되는 서비스 타이틀 설정
    page_icon="🥗",                            # 브라우저 탭 아이콘 설정
    layout="wide"                              # 화면 전체를 넓게 사용하는 와이드 모드 레이아웃 적용
)


# [2] 고급 건강검진 / 영양분석 서비스 스타일 (CSS 디자인 시스템 정의)
st.markdown(
    """
    <style>
/* 헬스케어 엔터프라이즈 테마 전용 CSS 변수 선언 (네이비, 블루, 틸 그린 색상 조합) */
:root {
  --nv-navy:#16324F; --nv-blue:#2F5B7C; --nv-teal:#238A8D;
  --nv-bg:#F6F8FA; --nv-surface:#FFFFFF; --nv-border:#E2E8ED;
  --nv-text:#243746; --nv-muted:#71808C; --nv-soft:#EEF6F6;
}
/* 전역 폰트 및 애플리케이션 배경 색상 설정 */
html, body, [class*="css"] { font-family:'Noto Sans KR',sans-serif; }
.stApp { background:var(--nv-bg); color:var(--nv-text); }
[data-testid="stHeader"] { background:rgba(246,248,250,.96); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--nv-border); }
[data-testid="stSidebar"] > div:first-child { padding-top:1.25rem; }
.block-container { max-width:1480px; padding:1.7rem 2.2rem 3rem; }

/* 타이틀 및 섹션 헤더 타이포그래피 스타일링 */
h1,h2,h3 { color:var(--nv-navy)!important; font-weight:800!important; letter-spacing:-.035em; }
h1 { font-size:2rem!important; margin-bottom:.25rem!important; }
h2 { font-size:1.35rem!important; }
h3 { font-size:1.05rem!important; }
.page-kicker { color:var(--nv-teal); font-size:.72rem; font-weight:800; letter-spacing:.14em; margin-bottom:.45rem; }
.page-description { color:var(--nv-muted); font-size:.9rem; line-height:1.6; margin-bottom:1.25rem; }
.section-title { color:var(--nv-navy); font-size:.9rem; font-weight:800; letter-spacing:.05em; margin:1.35rem 0 .7rem; text-transform:uppercase; }

/* 사이드바 브랜드 로고 및 서브타이틀 디자인 */
.sidebar-brand { color:var(--nv-navy); font-size:1.2rem; font-weight:800; letter-spacing:-.03em; }
.sidebar-sub { color:#84919A; font-size:.72rem; margin:2px 0 18px; }

/* 카드 형태 컴포넌트 디자인 (박스 그림자 및 곡선 테두리) */
.health-card,.enterprise-card,.report-box { background:var(--nv-surface); border:1px solid var(--nv-border); border-radius:12px; box-shadow:0 2px 10px rgba(22,50,79,.035); }
.health-card { padding:18px 20px; }
.report-box { padding:18px 20px; margin:.5rem 0 1rem; }
.report-title { color:var(--nv-navy); font-size:.92rem; font-weight:800; margin-bottom:7px; }
.report-text { color:#647480; font-size:.83rem; line-height:1.7; }

/* KPI 메트릭 카드 라벨 및 수치 디자인 */
.metric-label { color:var(--nv-muted); font-size:.72rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.metric-value { color:var(--nv-navy); font-size:1.75rem; font-weight:800; line-height:1.1; margin-top:7px; }
.metric-unit { color:#6D7C87; font-size:.8rem; font-weight:500; margin-left:3px; }
.metric-note,.small-muted { color:#87949E; font-size:.7rem; margin-top:7px; }

/* 영양 상태 평가 상태별 텍스트 색상 클래스 */
.status-good { color:var(--nv-teal); font-weight:700; }
.status-warning { color:#A46A00; font-weight:700; }
.tag { display:inline-block; background:var(--nv-soft); color:#237779; border:1px solid #D5EAEA; padding:4px 8px; border-radius:999px; font-size:.72rem; font-weight:700; margin:2px 3px 2px 0; }

/* 버튼 및 입력 폼 UI 컴포넌트 디자인 설정 */
.stButton > button,.stDownloadButton > button { border-radius:8px; font-weight:700; border:1px solid var(--nv-border); }
[data-testid="stFileUploader"] { background:#fff; border:1px dashed #C8D4DC; border-radius:10px; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--nv-border); border-radius:10px; padding:12px 14px; }
[data-testid="stDataFrame"] { border:1px solid var(--nv-border); border-radius:10px; overflow:hidden; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { border-radius:8px; }
hr { border:0; border-top:1px solid var(--nv-border); margin:1.2rem 0; }
</style>
    """,
    unsafe_allow_html=True
)


# [3] CSV 영양 데이터 로드 및 정제 함수
@st.cache_data  # 동일한 파일 경로 및 수정 시각일 경우 데이터를 캐싱하여 로딩 속도 최적화
def load_nutrition_db(csv_path, csv_modified_time):
    # CSV 파일에 반드시 존재해야 하는 필수 컬럼 집합 정의
    required_columns = {"food_name", "category", "unit", "cal", "carbs", "protein", "fat", "sugar", "sodium"}

    # 지정된 경로에 CSV 파일이 존재하는지 확인
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"영양 데이터 CSV 파일이 없습니다: {csv_path}")

    # pandas를 이용해 UTF-8-sig 인코딩으로 CSV 파일 읽기
    nutrition_df = pd.read_csv(csv_path, encoding="utf-8-sig")
    missing_columns = required_columns - set(nutrition_df.columns)
    if missing_columns:
        raise ValueError(f"영양 데이터 CSV에 필요한 컬럼이 없습니다: {sorted(missing_columns)}")

    nutrition_df = nutrition_df.copy()
    nutrition_df["food_name"] = nutrition_df["food_name"].astype(str).str.strip()  # 음식명 공백 제거
    nutrition_df = nutrition_df[nutrition_df["food_name"] != ""]                 # 빈 이름 행 제거

    # 영양소 수치 데이터 컬럼들을 숫자로 변환하고 결측치는 0.0으로 대체
    numeric_columns = ["cal", "carbs", "protein", "fat", "sugar", "sodium"]
    for column in numeric_columns:
        nutrition_df[column] = pd.to_numeric(nutrition_df[column], errors="coerce").fillna(0.0)

    # 음식 이름을 키(Key)로 하고 영양 성분 딕셔너리를 값(Value)으로 하는 빠른 조회용 맵 반환
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

# 영양 데이터베이스 CSV 파일 경로 검증 및 로드 실행
NUTRITION_CSV_PATH = os.path.join(os.path.dirname(__file__), "CaloDetect_nutrition_all_matched.csv")
if not os.path.exists(NUTRITION_CSV_PATH):
    raise FileNotFoundError(f"영양 데이터 CSV 파일이 없습니다: {NUTRITION_CSV_PATH}")

NUTRITION_DB = load_nutrition_db(
    NUTRITION_CSV_PATH,
    os.path.getmtime(NUTRITION_CSV_PATH)
)


# [4] 5차 비전 AI 모델 로드 및 추론 함수
@st.cache_resource  # 모델은 메모리에 한 번만 로드하고 재사용하도록 캐싱 처리
def load_5th_model():
    model_path = "best.pt"  # YOLO 학습 가중치 파일 경로
    data_path = "5차data.yaml"  # 클래스 정보가 담긴 설정 파일 경로

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"필수 모델 파일이 없습니다: {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"필수 데이터 설정 파일이 없습니다: {data_path}")

    # YAML 설정 파일 열기
    with open(data_path, "r", encoding="utf-8") as yaml_file:
        data_config = yaml.safe_load(yaml_file)

    yaml_names = data_config["names"]
    if isinstance(yaml_names, dict):
        yaml_names = [yaml_names[index] for index in range(data_config["nc"])]

    if len(yaml_names) != data_config["nc"]:
        raise ValueError("5차data.yaml의 nc와 names 개수가 다릅니다.")

    # YOLO 모델 초기화 및 클래스 이름 일치 여부 검증
    model = YOLO(model_path)
    model_names = [model.names[index] for index in range(len(model.names))]
    if model_names != yaml_names:
        raise ValueError("5차best.pt의 클래스 순서 또는 이름이 5차data.yaml과 다릅니다.")

    return model, yaml_names

def run_5th_model(image, conf_val=0.08, iou_val=0.45, imgsz_val=960):
    model, class_names = load_5th_model()
    
    # YOLO 추론 수행 (신뢰도 Conf, 중복 제거 IoU, 분석 해상도 반영)
    result = model(image, conf=conf_val, iou=iou_val, imgsz=imgsz_val, verbose=False)[0]
    detected_items = []
    annotated_img = image.copy()
    draw = ImageDraw.Draw(annotated_img)

    # 탐지된 각 바운딩 박스 순회
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
        # 이미지 위에 탐지 객체 경계 상자 및 라벨 텍스트 드로잉
        draw.rectangle([x1, y1, x2, y2], outline="#28a745", width=3)
        draw.text((x1 + 4, max(0, y1 - 16)), f"{name} ({conf * 100:.0f}%)", fill="#28a745")

    return detected_items, annotated_img


# [5] 가상 데이터 생성 및 세션 상태 초기화 함수
def generate_mock_meals(count=20):
    sample_keys = list(NUTRITION_DB.keys())
    mock_data = []
    base_date = datetime.now()
    
    for _ in range(count):
        # 최근 6일 이내의 랜덤 날짜 및 식사 시간 생성
        target_date = base_date - timedelta(days=random.randint(0, 6))
        meal_type = random.choice(["아침", "점심", "저녁", "간식/야식"])
        hour = random.randint(7, 21)
        minute = random.randint(10, 55)
        time_str = f"{target_date.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}"
        
        food_name = random.choice(sample_keys)
        item = NUTRITION_DB[food_name]
        portion = random.choice([0.5, 1.0, 1.0, 1.5]) # 섭취 배율 무작위 설정
        
        # 가상 데이터 딕셔너리 구성 (영양 성분 비례 계산)
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

# 앱 최초 실행 시 세션 상태에 가상 식단 20건 자동 주입
if "initialized" not in st.session_state:
    st.session_state.meal_history = generate_mock_meals(20)
    st.session_state.initialized = True
elif "meal_history" not in st.session_state:
    st.session_state.meal_history = []

if "last_added_message" not in st.session_state:
    st.session_state.last_added_message = None


# [6] 사이드바 네비게이션 및 파라미터 조절 위젯 구성
st.sidebar.markdown('<div class="sidebar-brand">🥗 NutriVision</div><div class="sidebar-sub">AI 맞춤형 식단 분석 서비스</div>', unsafe_allow_html=True)
st.sidebar.markdown("### 화면")
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


# [7] 화면 1: 다중 사진 분석 및 5차 모델 음식 감지 인터페이스
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
            
            # 비전 AI 객체 탐지 실행
            detected_items, annotated_img = run_5th_model(
                img_obj,
                conf_val=conf_threshold,
                iou_val=iou_threshold,
                imgsz_val=imgsz_choice
            )

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


# [8] ECharts 공통 테마 및 렌더링 헬퍼 함수 설정
ECHARTS_TEXT = "#40515F"
ECHARTS_MUTED = "#82909A"
ECHARTS_NAVY = "#16324F"
ECHARTS_TEAL = "#238A8D"
ECHARTS_BORDER = "#E3E9ED"

def render_echart(options, height="330px", key=None):
    return st_echarts(
        options=options,
        height=height,
        key=key
    )


# [9] 화면 2: 고급 건강검진형 종합 통계 대시보드
if view_mode == "📊 종합 통계 대시보드":

    st.markdown(
        '<div class="page-kicker">NUTRIVISION · HEALTH ANALYTICS</div>',
        unsafe_allow_html=True
    )

    st.title("AI 맞춤형 식단 다이어리 & 대시보드")

    st.markdown(
        '<div class="page-description">'
        '식단 기록을 기반으로 일일 에너지 섭취량과 '
        '탄수화물·단백질·지방 균형을 한눈에 확인합니다.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.meal_history:
        st.info(
            "데이터가 비어 있습니다. 사진을 등록하거나 "
            "사이드바에서 가상 데이터를 생성하세요."
        )
    else:
        df = pd.DataFrame(st.session_state.meal_history)

        # [계산 공식 1] 전체 누적 영양 성분 합산 산출
        tot_cal = round(df["칼로리(kcal)"].sum(), 1)
        tot_carbs = round(df["탄수화물(g)"].sum(), 1)
        tot_protein = round(df["단백질(g)"].sum(), 1)
        tot_fat = round(df["지방(g)"].sum(), 1)
        tot_sugar = round(df["당류(g)"].sum(), 1)
        tot_sodium = round(df["나트륨(mg)"].sum(), 1)

        # [계산 공식 2] 오늘 날짜 기준으로 데이터 필터링 및 금일 섭취량 계산
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_df = df[df["날짜"].astype(str) == today_str].copy()

        today_cal = round(today_df["칼로리(kcal)"].sum(), 1) if not today_df.empty else 0
        today_carbs = round(today_df["탄수화물(g)"].sum(), 1) if not today_df.empty else 0
        today_protein = round(today_df["단백질(g)"].sum(), 1) if not today_df.empty else 0
        today_fat = round(today_df["지방(g)"].sum(), 1) if not today_df.empty else 0

        # [계산 공식 3] 금일 목표 칼로리 대비 달성률(%) 연산
        goal_percent = today_cal / daily_goal * 100 if daily_goal > 0 else 0

        # ----------------------------------------------------------------------
        # 오늘의 영양 상태 KPI 카드 렌더링
        # ----------------------------------------------------------------------
        st.markdown(
            '<div class="section-title">오늘의 영양 상태</div>',
            unsafe_allow_html=True
        )

        k1, k2, k3, k4 = st.columns(4)

        cards = [
            ("오늘 섭취 칼로리", f"{today_cal:,.0f}", "kcal", f"목표 {daily_goal:,.0f} kcal · {goal_percent:.0f}%"),
            ("탄수화물", f"{today_carbs:,.1f}", "g", "오늘 기록 기준"),
            ("단백질", f"{today_protein:,.1f}", "g", "오늘 기록 기준"),
            ("지방", f"{today_fat:,.1f}", "g", "오늘 기록 기준"),
        ]

        for col, (label, value, unit, note) in zip([k1, k2, k3, k4], cards):
            with col:
                st.markdown(
                    f"""
                    <div class="health-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}
                            <span class="metric-unit">{unit}</span>
                        </div>
                        <div class="metric-note">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # AI 식단 분석 요약 문구 동적 결정
        if today_cal == 0:
            report_text = "오늘 등록된 식단이 없습니다. 음식 사진을 분석하여 오늘의 식단을 먼저 기록해 주세요."
            report_class = "status-warning"
        elif today_cal <= daily_goal:
            report_text = f"오늘 섭취량은 목표 칼로리의 {goal_percent:.0f}% 수준입니다. 현재 기록 기준으로 목표 범위 안에 있습니다."
            report_class = "status-good"
        else:
            report_text = f"오늘 섭취량이 목표보다 {today_cal - daily_goal:,.0f} kcal 높습니다. 다음 식사에서는 섭취량을 조절해 보세요."
            report_class = "status-warning"

        st.markdown(
            f"""
            <div class="report-box">
                <div class="report-title">AI 식단 분석 요약</div>
                <div class="report-text">
                    <span class="{report_class}">{report_text}</span>
                    <br>
                    아래 차트에서 최근 일자별 섭취 추이와 영양소 구성을 자세히 확인할 수 있습니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ----------------------------------------------------------------------
        # [차트 1] 최근 일자별 칼로리 섭취 추이 라인 차트 설정
        # ----------------------------------------------------------------------
        daily_df = (
            df.groupby("날짜")["칼로리(kcal)"]
            .sum()
            .reset_index()
            .sort_values("날짜")
        )

        st.markdown(
            '<div class="section-title">최근 일자별 칼로리 섭취 추이</div>',
            unsafe_allow_html=True
        )

        line_options = {
            "animation": True,
            "tooltip": {
                "trigger": "axis",
                "backgroundColor": "#FFFFFF",
                "borderColor": ECHARTS_BORDER,
                "textStyle": {"color": ECHARTS_TEXT}
            },
            "grid": {"left": "4%", "right": "4%", "top": "14%", "bottom": "12%", "containLabel": True},
            "xAxis": {
                "type": "category",
                "data": daily_df["날짜"].tolist(),
                "boundaryGap": False,
                "axisLine": {"lineStyle": {"color": ECHARTS_BORDER}},
                "axisLabel": {"color": ECHARTS_MUTED, "fontSize": 11}
            },
            "yAxis": {
                "type": "value",
                "name": "kcal",
                "nameTextStyle": {"color": ECHARTS_MUTED},
                "splitLine": {"lineStyle": {"color": "#EEF2F4"}},
                "axisLabel": {"color": ECHARTS_MUTED}
            },
            "series": [{
                "name": "섭취 칼로리",
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 7,
                "data": [round(v, 1) for v in daily_df["칼로리(kcal)"].tolist()],
                "lineStyle": {"width": 3, "color": ECHARTS_TEAL},
                "itemStyle": {"color": ECHARTS_TEAL},
                "areaStyle": {"opacity": 0.08},
                # 사이드바에서 입력한 목표 칼로리를 점선 기준선(MarkLine)으로 시각화
                "markLine": {
                    "silent": True,
                    "symbol": "none",
                    "data": [{
                        "yAxis": daily_goal,
                        "label": {"formatter": f"목표 {daily_goal:,} kcal", "color": ECHARTS_NAVY},
                        "lineStyle": {"type": "dashed", "color": "#9AA8B2"}
                    }]
                }
            }]
        }

        render_echart(line_options, height="360px", key="daily_calorie_line")

        # ----------------------------------------------------------------------
        # [차트 2 & 3] 식사 세션별 바 차트 및 탄단지 도넛 차트 설정
        # ----------------------------------------------------------------------
        col_c1, col_c2 = st.columns(2, gap="large")

        with col_c1:
            st.markdown(
                '<div class="section-title">식사 구분별 섭취 칼로리</div>',
                unsafe_allow_html=True
            )

            meal_order = ["아침", "점심", "저녁", "간식/야식"]
            meal_grp = (
                df.groupby("식사구분")["칼로리(kcal)"]
                .sum()
                .reindex(meal_order)
                .fillna(0)
                .reset_index()
            )

            bar_options = {
                "animation": True,
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "grid": {"left": "5%", "right": "5%", "top": "10%", "bottom": "12%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": meal_grp["식사구분"].tolist(),
                    "axisLine": {"lineStyle": {"color": ECHARTS_BORDER}},
                    "axisLabel": {"color": ECHARTS_MUTED}
                },
                "yAxis": {
                    "type": "value",
                    "name": "kcal",
                    "splitLine": {"lineStyle": {"color": "#EEF2F4"}},
                    "axisLabel": {"color": ECHARTS_MUTED}
                },
                "series": [{
                    "name": "칼로리",
                    "type": "bar",
                    "barWidth": "42%",
                    "data": [round(v, 1) for v in meal_grp["칼로리(kcal)"].tolist()],
                    "itemStyle": {"color": ECHARTS_NAVY, "borderRadius": [5, 5, 0, 0]}
                }]
            }

            render_echart(bar_options, height="320px", key="meal_calorie_bar")

        with col_c2:
            st.markdown(
                '<div class="section-title">탄수화물 · 단백질 · 지방 구성</div>',
                unsafe_allow_html=True
            )

            # [계산 공식 4] Atwater 환산 계수 적용: 탄수화물(4kcal/g), 단백질(4kcal/g), 지방(9kcal/g)
            macro_cal = [
                {"name": "탄수화물", "value": round(tot_carbs * 4, 1)},
                {"name": "단백질", "value": round(tot_protein * 4, 1)},
                {"name": "지방", "value": round(tot_fat * 9, 1)}
            ]

            macro_total = sum(x["value"] for x in macro_cal)

            donut_options = {
                "animation": True,
                "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c} kcal ({d}%)"},
                "legend": {
                    "bottom": 0,
                    "icon": "circle",
                    "textStyle": {"color": ECHARTS_TEXT}
                },
                "series": [{
                    "name": "탄단지",
                    "type": "pie",
                    "radius": ["52%", "74%"],
                    "center": ["50%", "45%"],
                    "avoidLabelOverlap": True,
                    "itemStyle": {
                        "borderRadius": 5,
                        "borderColor": "#FFFFFF",
                        "borderWidth": 3
                    },
                    "label": {"show": False},
                    "data": macro_cal
                }],
                # 도넛 차트 가운데에 총 칼로리 수치 텍스트 그래픽 삽입
                "graphic": [{
                    "type": "text",
                    "left": "center",
                    "top": "38%",
                    "style": {
                        "text": f"{macro_total:,.0f}\nkcal",
                        "textAlign": "center",
                        "fill": ECHARTS_NAVY,
                        "fontSize": 20,
                        "fontWeight": 700
                    }
                }]
            }

            render_echart(donut_options, height="320px", key="macro_donut")

        # ----------------------------------------------------------------------
        # [지표 카드] 매크로 밸런스 레이더, 목표 게이지, 당류·나트륨 바 차트
        # ----------------------------------------------------------------------
        st.markdown(
            '<div class="section-title">주요 영양 지표</div>',
            unsafe_allow_html=True
        )

        n1, n2, n3 = st.columns(3, gap="large")

        with n1:
            # [계산 공식 5] 전체 칼로리 대비 각 영양소의 열량 비중(%) 산출
            carb_ratio = tot_carbs * 4 / tot_cal * 100 if tot_cal > 0 else 0
            protein_ratio = tot_protein * 4 / tot_cal * 100 if tot_cal > 0 else 0
            fat_ratio = tot_fat * 9 / tot_cal * 100 if tot_cal > 0 else 0

            radar_options = {
                "tooltip": {},
                "radar": {
                    "radius": "62%",
                    "indicator": [
                        {"name": "탄수화물", "max": 60},
                        {"name": "단백질", "max": 40},
                        {"name": "지방", "max": 40}
                    ],
                    "axisName": {"color": ECHARTS_TEXT},
                    "splitLine": {
                        "lineStyle": {
                            "color": ["#E9EEF1", "#E3E9ED", "#DCE4E8", "#D5DEE3"]
                        }
                    }
                },
                "series": [{
                    "type": "radar",
                    "data": [{
                        "value": [
                            round(carb_ratio, 1),
                            round(protein_ratio, 1),
                            round(fat_ratio, 1)
                        ],
                        "name": "현재 구성",
                        "areaStyle": {"opacity": 0.18},
                        "lineStyle": {"width": 2}
                    }]
                }]
            }

            st.markdown('<div class="health-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">MACRO BALANCE</div>', unsafe_allow_html=True)
            render_echart(radar_options, height="280px", key="macro_radar")
            st.markdown('</div>', unsafe_allow_html=True)

        with n2:
            gauge_options = {
                "series": [{
                    "type": "gauge",
                    "startAngle": 210,
                    "endAngle": -30,
                    "min": 0,
                    "max": max(daily_goal, 1),
                    "progress": {"show": True, "width": 13},
                    "axisLine": {
                        "lineStyle": {
                            "width": 13,
                            "color": [[1, "#E7EEF1"]]
                        }
                    },
                    "pointer": {"show": True, "length": "58%", "width": 5},
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"show": False},
                    "anchor": {"show": True, "size": 8},
                    "title": {
                        "show": True,
                        "offsetCenter": [0, "62%"],
                        "color": ECHARTS_MUTED,
                        "fontSize": 12
                    },
                    "detail": {
                        "valueAnimation": True,
                        "offsetCenter": [0, "18%"],
                        "fontSize": 25,
                        "fontWeight": 800,
                        "color": ECHARTS_NAVY,
                        "formatter": "{value} kcal"
                    },
                    "data": [{
                        "value": round(min(today_cal, daily_goal), 1),
                        "name": "오늘 목표 대비"
                    }]
                }]
            }

            st.markdown('<div class="health-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">DAILY CALORIE GOAL</div>', unsafe_allow_html=True)
            render_echart(gauge_options, height="280px", key="daily_goal_gauge")
            st.markdown(
                f'<div class="small-muted">목표 {daily_goal:,} kcal · 현재 {today_cal:,.0f} kcal</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with n3:
            # [안전 장치] BidiComponent 에러 방지를 위해 당류 및 나트륨 값이 없을 경우 0.0으로 기본값 보정
            safe_sugar = float(tot_sugar) if 'tot_sugar' in locals() and tot_sugar is not None else 0.0
            safe_sodium = float(tot_sodium) if 'tot_sodium' in locals() and tot_sodium is not None else 0.0

            nutrient_options = {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "shadow"}
                },
                "grid": {
                    "left": "4%",
                    "right": "4%",
                    "top": "8%",
                    "bottom": "8%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category",
                    "data": ["당류", "나트륨"],
                    "axisLine": {"lineStyle": {"color": ECHARTS_BORDER}},
                    "axisLabel": {"color": ECHARTS_MUTED}
                },
                "yAxis": {
                    "type": "value",
                    "splitLine": {"lineStyle": {"color": "#EEF2F4"}},
                    "axisLabel": {"color": ECHARTS_MUTED}
                },
                "series": [{
                    "type": "bar",
                    "barWidth": "35%",
                    "data": [
                        {"value": safe_sugar, "itemStyle": {"color": "#6C7A89"}},
                        {"value": safe_sodium, "itemStyle": {"color": ECHARTS_NAVY}}
                    ],
                    "itemStyle": {"borderRadius": [5, 5, 0, 0]}
                }]
            }

            st.markdown('<div class="health-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">SUGAR · SODIUM</div>', unsafe_allow_html=True)
            render_echart(nutrient_options, height="280px", key="sugar_sodium_bar")
            st.markdown(
                f'<div class="small-muted">당류 {safe_sugar:,.1f} g · 나트륨 {safe_sodium:,.0f} mg</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # [히스토리 테이블 및 CSV 다운로드 기능]
        # ----------------------------------------------------------------------
        st.markdown(
            '<div class="section-title">전체 식사 히스토리</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "🟢 직접 등록한 실제 데이터와 가상 생성 데이터를 구분하여 관리할 수 있습니다."
        )

        # 사용자가 사진을 통해 직접 입력한 행에만 배경색을 입혀 시각적으로 강조하는 스타일 함수
        def highlight_real_data(row):
            if row["데이터구분"] == "직접입력":
                return [
                    "background-color: #EEF7F6; color: #1E6F70; font-weight: 600;"
                ] * len(row)
            return [""] * len(row)

        styled_df = df.style.apply(highlight_real_data, axis=1)

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        # 전체 식단 데이터를 CSV 파일로 인코딩하여 다운로드 버튼 제공
        csv_file = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 전체 식단 CSV 다운로드",
            data=csv_file,
            file_name=f"diet_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )