# 로컬 LLM 연동 텔레그램 봇 (Telegram LLM Bot)

이 프로젝트는 로컬 하드웨어에서 구동되는 LM Studio API를 연동하여 동작하는 스마트 텔레그램 AI 봇입니다.

---

## 🛠️ 기술 스택 (Tech Stack)

* **언어 (Language):** Python 3.x
* **봇 API (Telegram API):** `pyTelegramBotAPI (telebot)`
* **LLM 클라이언트 (LLM Client):** `OpenAI Python Client` (v2.41.0+)
* **환경 변수 관리 (Config):** `python-dotenv`
* **검색 라이브러리 (Search Library):** `duckduckgo-search` (실시간 인터넷 검색 연동)
* **로컬 LLM 백엔드 (Backend):** `LM Studio` (v1.x, 포트 1974번 연동)

---

## 🌟 주요 기능 (Key Features)

1. **실시간 답변 스트리밍 (Real-time Streaming):**
   * 답변 전체가 완성될 때까지 기다리지 않고, 실시간으로 답변이 출력되는 과정을 타이핑 효과와 함께 볼 수 있습니다.
2. **실시간 웹 검색 (Tool Calling / Function Calling):**
   * 실시간 정보나 최신 뉴스를 물어볼 경우, LLM이 판단하여 DuckDuckGo 검색엔진에서 정보를 긁어와 종합적으로 신뢰도 높은 답변을 내놓습니다.
3. **활성화 모델 조회:**
   * `/model` 명령어를 통해 현재 LM Studio 로컬 서버에 활성화되어 로드된 LLM 모델의 이름을 실시간으로 조회할 수 있습니다.
4. **가볍고 빠른 한국어 최적화:**
   * Qwen 3.5 및 Llama 등 최신 로컬 GGUF 모델과 유기적으로 연동됩니다.

---

## ⚙️ 실행 및 구동 방법 (How to Run)

### 1. 로컬 가상환경 설정 및 라이브러리 설치
```bash
# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정
프로젝트 루트 폴더에 `.env` 파일을 생성하고 아래 형식을 입력합니다.
```env
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
LM_STUDIO_API_URL=http://localhost:1974/v1
```

### 3. LM Studio 로컬 모델 구동
1. LM Studio를 실행하고 원하는 GGUF 모델(예: `Qwen_Qwen3.5-9B-Q4_K_M.gguf`)을 로드합니다.
2. 우측 패널의 **Hardware Settings**에서 **GPU Offload** 설정을 활성화하여 Metal 가속 속도를 확보합니다.
3. LM Studio 로컬 서버 가동 상태(기본 포트 1974번)를 확인합니다.

### 4. 텔레그램 봇 구동
```bash
python bot.py
```
