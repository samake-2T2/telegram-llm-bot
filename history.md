# 프로젝트 작업 이력 (History)

이 프로젝트의 업데이트 및 개선 작업 내역입니다.

## 2026-06-06
### 1. 실시간 답변 스트리밍(Streaming) 도입
* **배경:** 로컬 LLM 응답 생성 속도 특성상 답변 전체가 생성될 때까지 대기 시간이 길어 사용자 경험이 저하되는 문제 발생.
* **해당 파일:** [bot.py](file:///Users/2t2/Desktop/개인/telegram-llm-bot/bot.py)
* **상세 작업:**
  * OpenAI API 호출 시 `stream=True` 옵션 적용.
  * 텔레그램의 API 요청 제한(Rate Limit)을 우회하기 위해 `1.0초` 간격으로 응답 메시지를 실시간 편집(`edit_message_text`)하도록 구성.
  * 첫 토큰 출력 시점부터 사용자에게 결과가 보여짐에 따라 체감 속도가 비약적으로 향상됨.

### 2. 하드웨어 맞춤 최신 모델 다운로드 가이드 추가
* **배경:** 최신 Qwen3.5 모델 구동 요구사항 충족 및 16GB RAM의 Apple M1 하드웨어에 최적화된 모델 탐색.
* **상세 작업:**
  * LM Studio 환경에 맞춤화된 `Qwen_Qwen3.5-9B-Q4_K_M.gguf` 모델을 허깅페이스로부터 다운로드 연동 완료.
  * Apple Silicon Mac 기기에서 속도를 극대화할 수 있는 Metal GPU Offload 활성화 가이드 제공.

### 3. 실시간 웹 검색(Tool Calling) 연동
* **배경:** 로컬 LLM의 데이터 컷오프(Cut-off) 한계 극복 및 최신 정보/뉴스/날씨 등 실시간 질문 대응 필요.
* **해당 파일:** [bot.py](file:///Users/2t2/Desktop/개인/telegram-llm-bot/bot.py), [requirements.txt](file:///Users/2t2/Desktop/개인/telegram-llm-bot/requirements.txt)
* **상세 작업:**
  * 무료 웹 검색 패키지인 `duckduckgo-search` 연동.
  * OpenAI API의 Function Calling (`tools`) 규격을 사용해 LLM에 `search_web` 검색 함수 제공.
  * 1단계 툴 호출 판별(`stream=False`)을 통해 검색이 필요한지 판단 후, 검색 결과가 존재하면 2단계 최종 생성에서 결합하여 스트리밍(`stream=True`)으로 전달하도록 설계.
  * 툴 호출 미지원 구버전 모델에 대한 fallback(예외) 우회 구문 탑재.

### 4. XML 형태 툴 호출 강제 파싱 버그 수정 (Fallback Parsing)
* **배경:** Qwen 계열 등 일부 로컬 LLM이 OpenAI 표준 `tool_calls` JSON 규격 대신 답변 텍스트 내에 직접 XML 스타일(`<tool_call>...</tool_call>`)로 툴을 호출하는 비표준 응답 포맷을 뱉어 봇이 오동작하는 문제 해결.
* **해당 파일:** [bot.py](file:///Users/2t2/Desktop/개인/telegram-llm-bot/bot.py)
* **상세 작업:**
  * 정규식 기반 텍스트 툴 호출 파싱기 `parse_text_tool_calls(content)` 함수 개발.
  * 1차 답변 내에 `<tool_call>` 문자열이 포함될 경우, 강제로 정규식 파싱을 수행하여 툴 이름과 매개변수를 추출해 내도록 보완.
  * 텍스트 툴 호출도 임의의 `tool_call_id`를 부여하여 OpenAI 규격에 맞게 툴 결과(tool role) 메시지로 히스토리에 병합하는 Fallback 파싱 메커니즘을 확립하여 봇의 동작 강인성 확보.
