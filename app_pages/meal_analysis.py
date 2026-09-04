from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

from data.nutrition import YOLO_TO_DETAIL_MAP
from data.nutrition_loader import get_nutrition_by_name, search_foods
from services.detector import detect_foods
from services.meal_service import add_meal_records, build_meal_record

SAMPLE_DIR = Path("samples")


def _draw_detections(image, detections):
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for detection in detections:
        bbox = detection["bbox"]
        coordinates = (bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"])
        draw.rectangle(coordinates, outline="#00C853", width=4)
        draw.text(
            (bbox["x1"], max(0, bbox["y1"] - 18)),
            f"{detection['label']} {detection['confidence']:.1f}%",
            fill="#00C853",
        )
    return annotated


def _load_images():
    input_source = st.radio(
        "이미지 입력 방식:",
        ["📂 시연용 샘플 이미지 다중 선택", "💻 내 컴퓨터에서 여러 장 업로드"],
        horizontal=True,
    )
    images = []
    if input_source == "📂 시연용 샘플 이미지 다중 선택":
        SAMPLE_DIR.mkdir(exist_ok=True)
        sample_files = sorted(
            path for path in SAMPLE_DIR.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        if not sample_files:
            st.info("💡 `samples/` 폴더에 사진들을 넣어두면 여러 장을 동시에 선택할 수 있습니다.")
            return images
        selected_names = st.multiselect(
            "시연할 샘플 사진들을 선택하세요 (여러 개 선택 가능):",
            options=[path.name for path in sample_files],
            default=[sample_files[0].name],
        )
        for name in selected_names:
            path = SAMPLE_DIR / name
            images.append((name, Image.open(path).convert("RGB")))
    else:
        uploaded_files = st.file_uploader(
            "음식 사진들을 선택하세요 (Ctrl/Shift 키를 누르고 여러 장 선택 가능)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
        )
        for uploaded_file in uploaded_files or []:
            images.append((uploaded_file.name, Image.open(uploaded_file).convert("RGB")))
    return images


def _render_food_card(index, total, image_title, image, meal_slot):
    with st.expander(f"📷 [{index + 1}/{total}] {image_title}", expanded=True):
        detections = detect_foods(image)
        image_column, info_column = st.columns([1, 1.5], gap="medium")
        with image_column:
            st.image(_draw_detections(image, detections), width="stretch")
            if detections:
                st.caption("초록색 박스는 YOLO가 탐지한 객체의 위치입니다.")
        with info_column:
            if detections:
                detected_labels = ", ".join(sorted({detection["label"] for detection in detections}))
                confidence_text = ", ".join(
                    f"{detection['confidence']:.1f}%" for detection in detections
                )
                st.success(
                    f"AI 인식 {len(detections)}개: **{detected_labels}** "
                    f"({confidence_text})"
                )
                suggested_keywords = [YOLO_TO_DETAIL_MAP[detection["label"]] for detection in detections]
                suggested_keyword = next(
                    (keyword for keyword in suggested_keywords if keyword), ""
                )
            else:
                st.warning("⚠️ 음식 자동 감지 실패 (수동 선택)")
                suggested_keyword = ""

            keyword = st.text_input(
                f"음식 검색 (사진 {index + 1})",
                value=suggested_keyword,
                key=f"keyword_{index}",
            )
            options = search_foods(keyword, limit=20)
            if not options:
                st.info("음식명을 입력하면 최대 20개의 후보가 표시됩니다.")
                return None

            food_name = st.selectbox(
                f"상세 음식 선택 (사진 {index + 1})",
                options=options,
                key=f"food_{index}",
            )
            item = get_nutrition_by_name(food_name)
            portion = st.number_input(
                f"섭취 수량 ({item['serving_basis']})",
                min_value=0.5,
                max_value=5.0,
                value=1.0,
                step=0.5,
                key=f"portion_{index}",
            )
            record = build_meal_record(food_name, portion, meal_slot)

            def display_value(value, unit):
                return f"정보 없음" if value is None else f"{value}{unit}"

            st.caption(
                f"🔥 **{display_value(record['칼로리(kcal)'], ' kcal')}** | "
                f"탄수화물 {display_value(record['탄수화물(g)'], 'g')} | "
                f"단백질 {display_value(record['단백질(g)'], 'g')} | "
                f"지방 {display_value(record['지방(g)'], 'g')} | "
                f"나트륨 {display_value(record['나트륨(mg)'], 'mg')}"
            )
            return record


def render_meal_analysis():
    st.title("📷 AI 다중 음식 사진 분석 & 식단 등록")
    st.caption("여러 장의 음식 사진을 한 번에 올리고 각각의 메뉴와 수량을 확인한 뒤 일괄 등록하세요.")
    if st.session_state.last_added_message:
        st.success(st.session_state.last_added_message)
        if st.button("알림 닫기"):
            st.session_state.last_added_message = None
            st.rerun()

    images = _load_images()
    if not images:
        return
    st.divider()
    st.subheader(f"🔍 총 {len(images)}장의 사진이 감지되었습니다. 각각의 정보를 확인하세요.")
    meal_slot = st.selectbox(
        "🕒 식사 구분 (선택한 모든 음식에 일괄 적용)",
        ["아침", "점심", "저녁", "간식/야식"],
        index=1,
    )
    records = [
        _render_food_card(index, len(images), title, image, meal_slot)
        for index, (title, image) in enumerate(images)
    ]
    records = [record for record in records if record is not None]
    if not records:
        return
    st.divider()
    total_calories = sum(record["칼로리(kcal)"] for record in records)
    label = f"🚀 위 {len(records)}개 음식 일괄 등록하기 (총 {total_calories:,.1f} kcal)"
    if st.button(label, type="primary", width="stretch"):
        add_meal_records(records)
        names = ", ".join(record["음식명"] for record in records)
        st.session_state.last_added_message = (
            f"✅ **[일괄 등록 성공]** 총 {len(records)}개 품목({names})이 "
            f"오늘의 **[{meal_slot}]** 식단으로 정상 저장되었습니다! (대시보드에서 확인 가능)"
        )
        st.rerun()
