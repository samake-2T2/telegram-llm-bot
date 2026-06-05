import os
import time
import json
import re
import telebot
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# .env 파일 로드
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LM_STUDIO_API_URL = os.getenv("LM_STUDIO_API_URL", "http://localhost:1974/v1")

if not TELEGRAM_BOT_TOKEN or "YOUR_TELEGRAM" in TELEGRAM_BOT_TOKEN:
    print("경고: .env 파일에 올바른 TELEGRAM_BOT_TOKEN을 설정해야 합니다.")

# 텔레그램 봇 객체 초기화
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# LM Studio 클라이언트 초기화 (포트 1974 연동)
client = OpenAI(base_url=LM_STUDIO_API_URL, api_key="lm-studio")

# XML 스타일의 <tool_call> 텍스트 파싱 헬퍼 함수
def parse_text_tool_calls(content: str):
    """모델이 출력한 XML 형태의 <tool_call> 텍스트를 파싱하여 함수명과 매개변수를 추출합니다."""
    try:
        # function명 추출
        func_match = re.search(r"<function=(\w+)>", content)
        if not func_match:
            return None
        func_name = func_match.group(1)
        
        # parameter 추출 (<parameter=name>value</parameter>)
        param_matches = re.findall(r"<parameter=(\w+)>\s*(.*?)\s*</parameter>", content, re.DOTALL)
        args = {}
        for param_name, param_value in param_matches:
            args[param_name] = param_value.strip()
            
        return {
            "name": func_name,
            "arguments": args
        }
    except Exception as e:
        print(f"텍스트 기반 툴 콜 파싱 실패: {str(e)}")
        return None

# 최종 답변 내 잔여 시스템 태그 클리닝 헬퍼 함수
def clean_tool_tags(text: str) -> str:
    """답변 내에 남아있는 <tool_call>이나 <tool_call> 등의 시스템 태그를 모두 제거합니다."""
    # <tool_call>...</tool_call> 패턴 제거
    text = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL)
    # <tool_response>...</tool_response> 패턴 제거
    text = re.sub(r"<tool_response>.*?</tool_response>", "", text, flags=re.DOTALL)
    # 개별 잔여 태그 청소
    text = re.sub(r"</?(tool_call|tool_response|function|parameter)[^>]*>", "", text)
    return text.strip()

# 웹 검색 함수 정의
def search_web(query: str, max_results: int = 5) -> str:
    """DuckDuckGo를 통해 웹에서 실시간 정보를 검색합니다."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
            if not results:
                return "검색 결과가 없습니다."
            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. 제목: {r['title']}\nURL: {r['href']}\n내용: {r['body']}\n")
            return "\n".join(formatted)
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "안녕하세요! 로컬 LLM 텔레그램 봇입니다. 질문을 입력하거나 /model 명령어를 입력하여 로드된 모델을 확인해 보세요.")

@bot.message_handler(commands=['model'])
def show_model_info(message):
    try:
        # LM Studio 서버로부터 로드된 모델 리스트 조회
        models_data = client.models.list()
        model_names = [model.id for model in models_data.data]
        if model_names:
            models_str = "\n".join([f"• {m}" for m in model_names])
            bot.reply_to(message, f"현재 활성화된 로컬 모델 목록:\n{models_str}")
        else:
            bot.reply_to(message, "현재 로드된 모델이 없습니다. LM Studio에서 모델을 로드해 주세요.")
    except Exception as e:
        bot.reply_to(message, f"LM Studio 서버에서 모델 정보를 가져오는 데 실패했습니다 (포트 1974번 확인): {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    # 사용자에게 대기 메시지 전송
    sent_message = bot.reply_to(message, "💬 답변을 생성하는 중입니다...")
    
    # 툴 정의
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "실시간 정보, 뉴스, 현재 날씨 등 최신 인터넷 정보가 필요한 질문에 대해 웹 검색을 수행합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색엔진에 입력할 검색어 (예: '오늘 서울 날씨', 'Qwen 3.5 출시일')"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    # 기본 모델 표시용 변수
    used_model = "local-model"
    
    # 현재 날짜 및 시각 구하기
    current_time_str = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    messages = [
        {
            "role": "system", 
            "content": (
                "당신은 실시간 정보를 검색하여 답변하는 AI 어시스턴트입니다.\n"
                f"현재 시스템 일시는 [{current_time_str}] 입니다. 모든 시간/날짜 기준은 이 일시를 따르며, 절대 과거 연도(예: 2024년)로 착각하거나 임의로 지어내지 마십시오.\n"
                "항상 한국어로만 답변하고, 도구 호출 시 검색어(query)도 반드시 한국어로 작성하십시오. 한자(중국어)를 절대 사용하지 마십시오.\n"
                "웹 검색 결과를 바탕으로 답변할 때는 실시간 기온, 강수 확률 등 구체적인 수치를 생략 없이 상세히 포함하십시오.\n"
                "만약 검색 결과에 날씨 등의 정확한 정보가 부족하다면, 임의로 추측(환각)하지 말고 '현재 검색 결과로는 정확한 수치를 확인하기 어렵다'고 사실대로 말하십시오."
            )
        },
        {"role": "user", "content": user_text}
    ]

    try:
        # 1차 스트리밍 호출 시도 (API 레벨의 tools 규격 에러 대비 예외 처리)
        try:
            response = client.chat.completions.create(
                model="local-model",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                stream=True
            )
        except Exception as api_err:
            print(f"API tools 파라미터 미지원 또는 실패로 인해 일반 스트리밍으로 우회: {str(api_err)}")
            response = client.chat.completions.create(
                model="local-model",
                messages=messages,
                temperature=0.7,
                stream=True
            )

        full_reply = ""
        last_updated_text = ""
        update_interval = 1.0
        last_update_time = time.time()
        
        has_tool_call = False
        
        # 1차 스트리밍 감시 루프
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content_chunk = chunk.choices[0].delta.content
                full_reply += content_chunk
                
                # 모델명 정보 업데이트
                if hasattr(chunk, "model") and chunk.model:
                    used_model = chunk.model
                
                # 툴 호출 태그 시작 감지
                if "<tool_call>" in full_reply and not has_tool_call:
                    has_tool_call = True
                    # 태그 텍스트 노출 차단을 위해 대기 안내로 화면 업데이트 차단
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=sent_message.message_id,
                        text="💬 검색이 필요하여 도구를 가동하고 있습니다..."
                    )
                
                # 툴 호출 태그 완료 감지
                if has_tool_call and "</tool_call>" in full_reply:
                    text_tool_call = parse_text_tool_calls(full_reply)
                    if text_tool_call:
                        function_name = text_tool_call["name"]
                        function_args = text_tool_call["arguments"]
                        
                        if function_name == "search_web":
                            search_query = function_args.get("query")
                            bot.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=sent_message.message_id,
                                text=f"🔍 '{search_query}'에 대해 웹 검색 중..."
                            )
                            
                            # 검색 실행
                            search_result = search_web(search_query)
                            
                            # 툴 호출 및 응답 결과 히스토리 병합
                            messages.append({"role": "assistant", "content": full_reply})
                            messages.append({
                                "role": "user",
                                "content": f"도구(search_web) 검색 결과:\n{search_result}\n\n위 검색 결과를 바탕으로 사용자의 질문에 한국어로 명확하게 답변해 주세요. 정보가 부족하다면 추측하지 말고 검색된 내용 안에서만 답변하십시오."
                            })
                            
                            # 검색 완료 알림
                            bot.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=sent_message.message_id,
                                text="💬 검색 결과를 종합하여 답변을 정리하고 있습니다..."
                            )
                            break # 1차 스트리밍 탈출 및 2단계 생성으로 진행
                    else:
                        # 파싱이 안 되었거나 오탐일 경우 일반 텍스트로 복귀
                        has_tool_call = False
                
                # 일반 대화 스트리밍 전송 (툴 콜이 감지되지 않았을 때만 화면 갱신)
                if not has_tool_call:
                    current_time = time.time()
                    if current_time - last_update_time > update_interval:
                        if full_reply.strip() and full_reply != last_updated_text:
                            try:
                                bot.edit_message_text(
                                    chat_id=message.chat.id,
                                    message_id=sent_message.message_id,
                                    text=full_reply + " ✍️..."
                                )
                                last_updated_text = full_reply
                                last_update_time = current_time
                            except Exception:
                                pass

        # 2단계: 툴 콜을 실행했던 경우, 검색 결과 기반으로 2차 최종 답변 스트리밍 수행
        if has_tool_call:
            final_response = client.chat.completions.create(
                model="local-model",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            full_reply = ""
            last_updated_text = ""
            last_update_time = time.time()
            
            for chunk in final_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_reply += content_chunk
                    
                    if hasattr(chunk, "model") and chunk.model:
                        used_model = chunk.model
                        
                    current_time = time.time()
                    if current_time - last_update_time > update_interval:
                        if full_reply.strip() and full_reply != last_updated_text:
                            try:
                                bot.edit_message_text(
                                    chat_id=message.chat.id,
                                    message_id=sent_message.message_id,
                                    text=full_reply + " ✍️..."
                                )
                                last_updated_text = full_reply
                                last_update_time = current_time
                            except Exception:
                                pass

        # 최종 전송 전 시스템 태그 찌꺼기 완벽 필터링
        final_clean_reply = clean_tool_tags(full_reply)
        final_text = f"{final_clean_reply}\n\n🤖 [Model: {used_model}]"
        
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_message.message_id,
            text=final_text
        )

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_message.message_id,
            text=f"로컬 LLM 처리 중 실패 (연결 확인 필요): {str(e)}"
        )

if __name__ == "__main__":
    print(f"로컬 LLM API 주소: {LM_STUDIO_API_URL}")
    print("텔레그램 봇 폴링 서비스를 시작합니다...")
    bot.infinity_polling()
