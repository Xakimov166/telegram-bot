import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import OpenAI

print("BOT STARTED")

# 🔑 ключи
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TOKEN:", TOKEN)
print("OPENAI:", OPENAI_API_KEY)

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = OpenAI(api_key=OPENAI_API_KEY)

# старт
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Я AI бот 🤖 Напиши мне что-нибудь")

# основной обработчик
@dp.message()
async def chat(message: types.Message):
    try:
        user_text = message.text

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты полезный ассистент"},
                {"role": "user", "content": user_text}
            ]
        )

        reply = response.choices[0].message.content
        await message.answer(reply)

    except Exception as e:
        print("ERROR:", e)
        await message.answer(f"Ошибка: {e}")

# запуск
async def main():
    try:
        print("Бот запущен 🚀")

        # ❗ обязательно
        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(bot)

    except Exception as e:
        print("CRASH:", e)

if __name__ == "__main__":
    asyncio.run(main())
