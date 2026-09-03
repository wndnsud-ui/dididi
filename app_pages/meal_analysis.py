from pathlib import Path

import streamlit as st
from PIL import Image

from data.nutrition import NUTRITION_DB, YOLO_TO_DETAIL_MAP
from services.detector import detect_food
from services.meal_service import add_meal_records, build_meal_record

SAMPLE_DIR = Path("samples")


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
        image_column, info_column = st.columns([1, 1.5], gap="medium")
        with image_column:
            st.image(image, width="stretch")
        with info_column:
            detected_label, confidence = detect_food(image)
            if detected_label:
                st.success(f"AI 인식: **{detected_label}** ({confidence:.1f}%)")
                options = YOLO_TO_DETAIL_MAP[detected_label]
                label = f"상세 메뉴 확인/변경 (사진 {index + 1})"
            else:
                st.warning("⚠️ 음식 자동 감지 실패 (수동 선택)")
                options = list(NUTRITION_DB)
                label = f"메뉴 수동 선택 (사진 {index + 1})"

            food_key = st.selectbox(
                label,
                options=options,
                format_func=lambda key: f"{NUTRITION_DB[key]['name']} ({NUTRITION_DB[key]['category']})",
                key=f"menu_{index}",
            )
            item = NUTRITION_DB[food_key]
            portion = st.number_input(
                f"섭취 수량 ({item['unit']})",
                min_value=0.5,
                max_value=5.0,
                value=1.0,
                step=0.5,
                key=f"portion_{index}",
            )
            record = build_meal_record(food_key, portion, meal_slot)
            st.caption(
                f"🔥 **{record['칼로리(kcal)']} kcal** | 탄수화물 {record['탄수화물(g)']}g | "
                f"단백질 {record['단백질(g)']}g | 지방 {record['지방(g)']}g | "
                f"나트륨 {record['나트륨(mg)']}mg"
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
