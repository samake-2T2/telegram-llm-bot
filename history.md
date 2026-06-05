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
