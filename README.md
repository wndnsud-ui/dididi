# CaloDetect / AI 맞춤형 식단 다이어리 & 대시보드

**Streamlit + Ultralytics YOLOv8** 기반의 음식 사진 분석 및 영양 통계 대시보드입니다.
여러 장의 음식 사진을 한 번에 분석하고 메뉴와 섭취량을 확인한 뒤 식단 기록으로
등록할 수 있습니다. 등록된 데이터는 대시보드에서 칼로리, 탄수화물, 단백질, 지방
추이와 식사 히스토리로 확인할 수 있습니다.

## 가장 빠른 실행 — Windows

1. ZIP 압축을 풉니다.
2. 폴더 안의 **`01_SETUP_AND_RUN.bat`** 을 더블클릭합니다.
3. 최초 1회 실행 시:
   - `.venv` 가상환경 생성
   - pip 업데이트
   - 필요한 Python 패키지 설치
   - `yolov8n.pt` 모델 준비
   - Streamlit 앱 실행
4. 브라우저에서 자동으로 페이지가 열립니다.
5. 자동으로 열리지 않으면 `http://localhost:8501` 접속

두 번째 실행부터는 **`02_RUN_ONLY.bat`** 만 더블클릭하면 됩니다.

## 필요한 것

- Python 3.10 이상 권장
- 최초 설치 시 인터넷 연결
- Windows / macOS / Linux

## macOS / Linux

터미널에서 프로젝트 폴더로 이동한 뒤:

```bash
chmod +x 01_SETUP_AND_RUN.sh 02_RUN_ONLY.sh
./01_SETUP_AND_RUN.sh
```

이후 실행은:

```bash
./02_RUN_ONLY.sh
```

## 직접 명령어로 실행하고 싶은 경우

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 주요 기능

- 음식 사진 여러 장 업로드 또는 `samples/` 샘플 이미지 선택
- YOLOv8의 객체 인식 결과를 음식 메뉴 후보로 변환
- 메뉴와 섭취 수량 확인 및 수정
- 여러 음식 기록 일괄 등록
- 일일 목표 칼로리 기준의 칼로리 추이 차트
- 식사 구분별 섭취량 및 탄·단·지 비율 차트
- 전체 식단 히스토리 확인 및 CSV 다운로드
- 시연을 위한 가상 식단 데이터 생성 및 전체 데이터 초기화

## 프로젝트 구조

```text
dididi/
├─ app.py
├─ requirements.txt
├─ 01_SETUP_AND_RUN.bat
├─ 02_RUN_ONLY.bat
├─ 01_SETUP_AND_RUN.sh
├─ 02_RUN_ONLY.sh
├─ .streamlit/
│  └─ config.toml
├─ app_pages/
│  ├─ dashboard.py
│  └─ meal_analysis.py
├─ components/
│  └─ sidebar.py
├─ data/
│  └─ nutrition.py
├─ services/
│  ├─ detector.py
│  └─ meal_service.py
├─ yolov8n.pt
└─ samples/
   └─ README.txt
```

최초 실행 후에는 `.venv/` 가상환경 폴더가 생성됩니다.
`yolov8n.pt`가 없는 경우 Ultralytics가 모델을 다운로드할 수 있으므로
최초 실행에는 인터넷 연결이 필요합니다.

## 샘플 이미지

`samples/` 폴더 안에 `.jpg`, `.jpeg`, `.png` 음식 사진을 넣으면
앱에서 시연용 사진으로 다중 선택할 수 있습니다.

샘플 사진을 넣지 않아도 앱에서 **내 컴퓨터에서 여러 장 업로드**를 선택해
바로 테스트할 수 있습니다.

## 데이터 및 실행 참고

앱을 실행하면 시연을 위해 가상 식단 데이터 30건이 기본으로 표시됩니다.
사이드바에서 가상 데이터를 추가 생성하거나 전체 데이터를 비울 수 있습니다.
현재 식단 기록은 Streamlit 세션 상태에 저장되므로 앱을 종료하면 초기화됩니다.

## 현재 AI 인식 범위 관련 주의

기본 `yolov8n.pt`는 일반 객체 탐지 모델입니다.
현재 앱은 YOLO가 감지한 일반 라벨을 상세 음식 메뉴에 매핑하는 방식이므로
한국 음식 메뉴 자체를 정밀 분류하는 전용 모델은 아닙니다.

예를 들어 YOLO의 `bowl` 탐지를 비빔밥·제육덮밥·김치찌개·라면 후보로 연결한 뒤
사용자가 상세 메뉴를 확인/수정하는 구조입니다.

따라서 현재 버전은 **대시보드/UI/프로세스 시연용 MVP**에 적합합니다.
향후 한국 음식 데이터셋으로 학습한 모델의 `best.pt`를 연결하면
실제 프로젝트 모델로 확장할 수 있습니다.
