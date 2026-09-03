import streamlit as st
from ultralytics import YOLO

from data.nutrition import YOLO_TO_DETAIL_MAP


@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt")


def detect_food(image, confidence=0.25):
    model = load_yolo()
    results = model(image, conf=confidence)
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        label = model.names[class_id]
        if label in YOLO_TO_DETAIL_MAP:
            return label, float(box.conf[0]) * 100
    return None, 0.0
