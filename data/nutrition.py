from data.nutrition_loader import (
    get_food_names,
    get_nutrition_by_code,
    get_nutrition_by_name,
    load_nutrition_db,
    search_foods,
)

YOLO_TO_DETAIL_MAP = {
    "pizza": "피자",
    "sandwich": "샌드위치",
    "hot dog": "핫도그",
    "bowl": "",
    "apple": "사과",
    "banana": "바나나",
    "orange": "오렌지",
    "broccoli": "브로콜리",
    "cake": "케이크",
    "donut": "도넛",
    "cup": "",
    "bottle": "",
}
