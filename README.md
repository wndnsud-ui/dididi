# AI 맞춤형 식단 다이어리 & 대시보드

이 프로젝트는 이미지 속 식단을 인식하고, 영양 정보를 요약해 보여주는 Streamlit 기반 웹 애플리케이션입니다.

## 프로젝트 개요

- 음식 이미지 입력 후 5차 YOLOv8 기반 객체 인식 수행
- 인식된 음식명을 한글 라벨로 변환
- 영양 정보(칼로리, 탄수화물, 단백질, 지방, 당류, 나트륨)를 계산
- 월별/일별 식단 기록 대시보드 제공
- 식단 관리 및 추천 기능 포함

## 사용 기술

- Python
- Streamlit
- PyTorch
- torchvision
- Ultralytics YOLO
- Plotly
- Pandas
- Pillow

## 폴더 구조

- `app.py` : 메인 Streamlit 애플리케이션
- `5차data.yaml` : 5차 59개 클래스 및 데이터셋 라벨 설정 파일
- `best.pt` : 5차 59종 한식 모델
- `CaloDetect_nutrition_all_matched.csv` : 음식별 영양 정보 데이터
- `requirements.txt` : Python 의존성 패키지 목록

## 실행 전 준비

Python 3.9 이상 권장

1. 가상환경 생성

```bash
python -m venv .venv
```

2. Windows에서 가상환경 활성화

```bash
.\.venv\Scripts\activate
```

3. 라이브러리 설치

```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며, 프로젝트 UI가 표시됩니다.

## 주요 설정

- `app.py`에서 모델 로딩 경로와 임계값을 조정할 수 있습니다.
- `5차data.yaml`에서 5차 클래스 이름 및 데이터 경로를 수정할 수 있습니다.
- `CaloDetect_nutrition_all_matched.csv`의 음식명과 영양값을 수정하면 앱의 영양 계산에 반영됩니다.
- 앱 실행 시 `best.pt`의 클래스 수와 순서를 `5차data.yaml`과 자동으로 비교합니다.
- `requirements.txt`에 필요한 패키지가 추가되면 바로 설치됩니다.

## 참고사항

- `best.pt`, `5차data.yaml`, `CaloDetect_nutrition_all_matched.csv`가 프로젝트 폴더에 있어야 정상 실행됩니다.
- 현재 앱은 앙상블을 사용하지 않고 `best.pt` 단일 모델만 사용합니다.
- GPU 환경이 있으면 추론 속도가 더 빨라집니다.
- 라이브러리 추가 또는 버전 변경이 필요하면 `requirements.txt`를 수정한 뒤 설치를 다시 수행하면 됩니다.

## 영양 CSV 형식

`CaloDetect_nutrition_all_matched.csv`는 다음 컬럼을 사용합니다.

```text
food_name,category,unit,cal,carbs,protein,fat,sugar,sodium
```

- `food_name` : 앱에서 표시할 음식명입니다. 모델의 클래스명과 다르면 자동 감지 후 메뉴 선택에서 별도 확인이 필요합니다.
- `category` : 음식 분류 표시값입니다.
- `unit` : 섭취 수량의 단위입니다. 예: `100g`, `1인분`, `개`
- `cal`, `carbs`, `protein`, `fat`, `sugar`, `sodium` : `unit` 기준 영양값입니다.
- CSV의 숫자값이 비어 있거나 숫자로 변환되지 않으면 해당 값은 `0`으로 처리됩니다.
- CSV 파일의 수정 시간이 캐시 키에 포함되어 있어 파일을 저장한 뒤 앱을 새로고침하면 변경값이 다시 로드됩니다.

## 변경 이력

1. 기존 모델 구조 확인
	- 기존 앱은 `best.pt`, `best1.pt`, `yolov8n.pt`를 조합하는 3중 앙상블 구조였습니다.
	- 150종, 55종, COCO 모델의 클래스 체계와 라벨 매핑이 함께 사용되고 있었습니다.

2. 5차 모델 적용
	- 5차 학습 모델을 기준 모델로 선정했습니다.
	- `5차best.pt`를 `best.pt`로 교체해 앱의 기본 모델 경로를 통일했습니다.
	- 교체 전 모델은 작업 중 `best_original.pt`로 백업했으며, 정리 단계에서 프로젝트 폴더에서 삭제했습니다.

3. 앙상블 제거
	- `best1.pt` 55종 보조 모델을 제거했습니다.
	- `yolov8n.pt` COCO 보조 모델을 제거했습니다.
	- 외부 앙상블 점수 계산과 모델 간 중복 제거 로직을 제거했습니다.
	- 현재 이미지는 `best.pt` 단일 모델만 추론합니다.

4. 5차 YAML 클래스 검증 추가
	- `5차data.yaml`의 `nc`와 `names`를 읽어 모델의 클래스 수와 비교합니다.
	- 모델 내부 클래스 이름과 YAML의 클래스 순서가 다르면 앱 실행 중 오류를 발생시킵니다.
	- 검증 결과 59개 클래스와 순서가 일치하는 것을 확인했습니다.

5. 영양 데이터 CSV 전환
	- `app.py`에 직접 작성되어 있던 하드코딩 영양 데이터 전체를 삭제했습니다.
	- `CaloDetect_nutrition_all_matched.csv`를 읽어 `NUTRITION_DB`를 생성하도록 변경했습니다.
	- 수동 메뉴 선택, 자동 인식 후 영양 계산, 가상 데이터 생성이 모두 CSV 데이터를 사용합니다.
	- 카테고리와 인분 단위를 바꿀 때는 모델 파일이나 YAML을 수정하지 않고 CSV만 수정하면 됩니다.

6. 캐시 갱신 보완
	- CSV 파일의 수정 시간을 `st.cache_data`의 입력값으로 사용합니다.
	- CSV를 수정한 뒤 Streamlit 화면을 새로고침하면 새 영양값이 적용됩니다.

## 현재 데이터 흐름

```text
이미지
  -> best.pt 단일 모델
  -> 5차data.yaml 클래스 검증
  -> 음식명 표시
  -> CaloDetect_nutrition_all_matched.csv 영양값 조회
  -> 섭취량 기준 영양 계산 및 식단 기록
```

## 빠른 설치 명령

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
