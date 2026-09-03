# CaloDetect / AI 맞춤형 식단 다이어리 & 대시보드

이 폴더는 **Streamlit + Ultralytics YOLOv8** 기반 음식 사진 분석 대시보드를
최대한 바로 실행할 수 있도록 구성한 실행 세트입니다.

## 가장 빠른 실행 — Windows

1. ZIP 압축을 풉니다.
2. 폴더 안의 **`01_SETUP_AND_RUN.bat`** 을 더블클릭합니다.
3. 최초 1회:
   - `.venv` 가상환경 생성
   - pip 업데이트
   - 필요한 Python 패키지 설치
   - `yolov8n.pt` 모델 다운로드/준비
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

## 프로젝트 구조

```text
calo_detect_streamlit_ready/
├─ app.py
├─ requirements.txt
├─ 01_SETUP_AND_RUN.bat
├─ 02_RUN_ONLY.bat
├─ 01_SETUP_AND_RUN.sh
├─ 02_RUN_ONLY.sh
├─ .streamlit/
│  └─ config.toml
└─ samples/
   └─ README.txt
```

최초 실행 후에는 프로젝트 루트에 `yolov8n.pt`가 생성될 수 있고,
`.venv/` 가상환경 폴더도 생성됩니다.

## 샘플 이미지

`samples/` 폴더 안에 `.jpg`, `.jpeg`, `.png` 음식 사진을 넣으면
앱에서 시연용 사진으로 다중 선택할 수 있습니다.

샘플 사진을 넣지 않아도 앱에서 **내 컴퓨터에서 여러 장 업로드**를 선택해
바로 테스트할 수 있습니다.

## 현재 AI 인식 범위 관련 주의

기본 `yolov8n.pt`는 일반 객체 탐지 모델입니다.
현재 앱은 YOLO가 감지한 일반 라벨을 상세 음식 메뉴에 매핑하는 방식이므로
한국 음식 메뉴 자체를 정밀 분류하는 전용 모델은 아닙니다.

예를 들어 YOLO의 `bowl` 탐지를 비빔밥·제육덮밥·김치찌개·라면 후보로 연결한 뒤
사용자가 상세 메뉴를 확인/수정하는 구조입니다.

따라서 지금 버전은 **대시보드/UI/프로세스 시연용 MVP**로 적합하며,
향후 한국 음식 데이터셋으로 학습한 모델의 `best.pt`를 연결하면
실제 프로젝트 모델로 확장할 수 있습니다.

# dididi
