from pathlib import Path
from zipfile import ZipFile

import cv2
import torch
import yaml
from torchvision.ops import nms
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
WEIGHTS = [
    ROOT / "best.pt",
    ROOT / "best (2).pt",
    ROOT / "7차best.pt",
]
DATA_YAML = ROOT / "data.yaml"
INPUT_DIR = ROOT / "predict_images"
EXTRACT_DIR = ROOT / "zip_images"
OUTPUT_DIR = ROOT / "runs" / "ensemble_predict"

CONF_THRES = 0.25
IOU_NMS = 0.6
IMG_SIZE = 640
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_names():
    with open(DATA_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    names = data.get("names", {})
    if isinstance(names, dict):
        return {int(k): v for k, v in names.items()}
    return {i: name for i, name in enumerate(names)}


def extract_images_from_zip():
    zip_files = sorted(ROOT.glob("*.zip"))
    if not zip_files:
        return []

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    extracted = []

    for zip_path in zip_files:
        with ZipFile(zip_path) as zf:
            for member in zf.namelist():
                member_path = Path(member)
                if member_path.suffix.lower() not in IMAGE_EXTS:
                    continue

                target = EXTRACT_DIR / member_path.name
                if not target.exists():
                    with zf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                extracted.append(target)

    return sorted(set(extracted))


def find_input_images():
    INPUT_DIR.mkdir(exist_ok=True)
    image_paths = sorted(
        p for p in INPUT_DIR.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    if image_paths:
        return image_paths

    image_paths = extract_images_from_zip()
    if image_paths:
        print(
            "predict_images 폴더에 이미지가 없어서 zip 안의 jpg/png를 사용합니다. "
            "직접 찍은 테스트 이미지는 predict_images 폴더에 넣으면 됩니다."
        )
        return image_paths

    raise FileNotFoundError(
        f"예측할 이미지가 없습니다.\n"
        f"이미지를 여기에 넣어주세요: {INPUT_DIR}\n"
        "또는 jpg/png가 들어있는 zip 파일을 현재 폴더에 넣어주세요."
    )


def ensemble_predictions(models, image_path):
    all_boxes = []
    all_scores = []
    all_classes = []

    for model in models:
        result = model.predict(
            source=str(image_path),
            conf=CONF_THRES,
            iou=IOU_NMS,
            imgsz=IMG_SIZE,
            verbose=False,
        )[0]

        if result.boxes is None or len(result.boxes) == 0:
            continue

        all_boxes.append(result.boxes.xyxy.cpu())
        all_scores.append(result.boxes.conf.cpu())
        all_classes.append(result.boxes.cls.cpu())

    if not all_boxes:
        return torch.zeros((0, 6), dtype=torch.float32)

    boxes = torch.cat(all_boxes)
    scores = torch.cat(all_scores)
    classes = torch.cat(all_classes)

    keep = []
    for cls in classes.unique():
        cls_idx = torch.where(classes == cls)[0]
        keep.append(cls_idx[nms(boxes[cls_idx], scores[cls_idx], IOU_NMS)])

    keep = torch.cat(keep) if keep else torch.empty(0, dtype=torch.long)
    detections = torch.cat([boxes[keep], scores[keep, None], classes[keep, None]], dim=1)
    return detections[detections[:, 4].argsort(descending=True)]


def draw_predictions(image_path, detections, names):
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"이미지를 읽지 못해서 건너뜁니다: {image_path}")
        return

    for x1, y1, x2, y2, conf, cls in detections.tolist():
        cls = int(cls)
        label = f"{names.get(cls, cls)} {conf:.2f}"
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 180, 255), 2)
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        text_w, text_h = text_size
        text_y = max(y1 - 8, text_h + 8)
        cv2.rectangle(
            image,
            (x1, text_y - text_h - 8),
            (x1 + text_w + 8, text_y + 4),
            (0, 180, 255),
            -1,
        )
        cv2.putText(
            image,
            label,
            (x1 + 4, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{image_path.stem}_ensemble{image_path.suffix}"
    cv2.imwrite(str(output_path), image)
    print(f"저장 완료: {output_path} / 탐지 {len(detections)}개")


def main():
    names = load_names()
    image_paths = find_input_images()
    models = [YOLO(str(weight)) for weight in WEIGHTS]

    print(f"예측 이미지 {len(image_paths)}개")
    print("3개 모델 앙상블 예측 시작")

    for image_path in image_paths:
        detections = ensemble_predictions(models, image_path)
        draw_predictions(image_path, detections, names)

    print(f"\n결과 폴더: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
