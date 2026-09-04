import streamlit as st
from ultralytics import YOLO

from data.nutrition import YOLO_TO_DETAIL_MAP

MODEL_PATH = "yolov8n.pt"


@st.cache_resource
def load_yolo():
    return YOLO(MODEL_PATH)


def detect_foods(image, confidence=0.25):
    model = load_yolo()
    results = model(image, conf=confidence, iou=0.5, max_det=20, verbose=False)
    detections = []

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        label = model.names[class_id]
        if label not in YOLO_TO_DETAIL_MAP:
            continue

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append({
            "class_id": class_id,
            "label": label,
            "confidence": round(float(box.conf[0]) * 100, 1),
            "bbox": {
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2),
            },
        })

    return detections
