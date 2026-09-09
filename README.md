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
- 앱 실행 시 `best.pt`의 클래스 수와 순서를 `5차data.yaml`과 자동으로 비교합니다.
- `requirements.txt`에 필요한 패키지가 추가되면 바로 설치됩니다.

## 참고사항

- `best.pt`와 `5차data.yaml`이 프로젝트 폴더에 있어야 정상 실행됩니다.
- 현재 앱은 앙상블을 사용하지 않고 `best.pt` 단일 모델만 사용합니다.
- GPU 환경이 있으면 추론 속도가 더 빨라집니다.
- 라이브러리 추가 또는 버전 변경이 필요하면 `requirements.txt`를 수정한 뒤 설치를 다시 수행하면 됩니다.

## 빠른 설치 명령

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
