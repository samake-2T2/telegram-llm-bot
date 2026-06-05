import os
import telebot
from openai import OpenAI
from dotenv import load_dotenv

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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "안녕하세요! 로컬 LLM 텔레그램 봇입니다. 질문을 입력해 주세요.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # 로컬 서버(포트 1974)에 연결하여 답변 요청
        response = client.chat.completions.create(
            model="local-model", # 로드된 모델이 자동 선택됩니다.
            messages=[
                {"role": "system", "content": "당신은 개발 및 코딩을 돕는 유능한 AI 어시스턴트입니다. 항상 한국어로 친절하게 답변해 주세요."},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
        )
        
        reply_content = response.choices[0].message.content
        bot.reply_to(message, reply_content)
        
    except Exception as e:
        bot.reply_to(message, f"로컬 LLM 응답 실패 (포트 1974번 연결 확인 필요): {str(e)}")

if __name__ == "__main__":
    print(f"로컬 LLM API 주소: {LM_STUDIO_API_URL}")
    print("텔레그램 봇 폴링 서비스를 시작합니다...")
    bot.infinity_polling()
