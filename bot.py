import os
import time
import json
import telebot
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
    
    messages = [
        {"role": "system", "content": "당신은 개발 및 코딩뿐만 아니라 실시간 정보도 검색하여 친절하게 알려주는 AI 어시스턴트입니다. 항상 한국어로 친절하게 답변해 주세요."},
        {"role": "user", "content": user_text}
    ]

    try:
        # 1단계: 툴 호출 판별 (스트리밍 없이 우선 호출)
        try:
            response = client.chat.completions.create(
                model="local-model",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
        except Exception as tool_err:
            # 툴 사용 호출 실패 시(LM Studio 미지원 모델 등), 일반 답변 스트리밍으로 우회
            print(f"Tool Calling API 호출 실패 (일반 답변으로 우회): {str(tool_err)}")
            tool_calls = None
            response_message = None

        # 2단계: 툴 호출 처리
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "search_web":
                    search_query = function_args.get("query")
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=sent_message.message_id,
                        text=f"🔍 '{search_query}'에 대해 웹 검색 중..."
                    )
                    
                    # 검색 실행
                    search_result = search_web(search_query)
                    
                    # 툴 결과 추가
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": search_result
                    })
            
            # 검색 후 최종 답변 생성 상태 알림
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sent_message.message_id,
                text="💬 검색 결과를 종합하여 답변을 정리하고 있습니다..."
            )
        elif response_message and response_message.content:
            # 툴을 타지 않고 바로 일반 답변이 나온 경우 1차 응답 바로 전송 후 리턴
            used_model = "local-model"
            final_text = f"{response_message.content}\n\n🤖 [Model: {used_model}]"
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sent_message.message_id,
                text=final_text
            )
            return

        # 3단계: 최종 스트리밍 응답 (검색 결과 결합)
        final_response = client.chat.completions.create(
            model="local-model",
            messages=messages,
            temperature=0.7,
            stream=True
        )

        full_reply = ""
        last_updated_text = ""
        update_interval = 1.0
        last_update_time = time.time()

        for chunk in final_response:
            if chunk.choices and chunk.choices[0].delta.content:
                full_reply += chunk.choices[0].delta.content
                
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
        
        used_model = "local-model"
        final_text = f"{full_reply}\n\n🤖 [Model: {used_model}]"
        
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
