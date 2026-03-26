import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
from docx import Document

print("BOT STARTED")

# 🔑 ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TOKEN:", TELEGRAM_TOKEN)
print("OPENAI:", OPENAI_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = OpenAI(api_key=OPENAI_API_KEY)

# 📁 папка
os.makedirs("downloads", exist_ok=True)

# 🌍 языки
user_languages = {}

# клавиатура
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Русский 🇷🇺")],
        [KeyboardButton(text="English 🇬🇧")],
        [KeyboardButton(text="O'zbek 🇺🇿")]
    ],
    resize_keyboard=True
)

# старт
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Выберите язык 👇", reply_markup=kb)

# основной обработчик
@dp.message()
async def handle(message: types.Message):
    user_id = message.from_user.id

    # выбор языка
    if message.text in ["Русский 🇷🇺", "English 🇬🇧", "O'zbek 🇺🇿"]:
        if "Русский" in message.text:
            user_languages[user_id] = "ru"
            await message.answer("Вы выбрали русский 🇷🇺")
        elif "English" in message.text:
            user_languages[user_id] = "en"
            await message.answer("You selected English 🇬🇧")
        else:
            user_languages[user_id] = "uz"
            await message.answer("Siz o'zbek tilini tanladingiz 🇺🇿")
        return

    # проверка языка
    lang = user_languages.get(user_id)
    if not lang:
        await message.answer("Сначала выбери язык 👇", reply_markup=kb)
        return

    # системный промпт
    if lang == "ru":
        system_prompt = "Отвечай только на русском языке."
    elif lang == "en":
        system_prompt = "Answer only in English."
    else:
        system_prompt = "Faqat o'zbek tilida javob ber."

    try:
        # 💬 ТЕКСТ
        if message.text:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message.text}
                ]
            )

            reply = response.choices[0].message.content
            await message.answer(reply)
            return

        # 📸 ФОТО
        if message.photo:
            await message.answer("Фото получено 📸 (обработка пока отключена)")
            return

        # 📄 ДОКУМЕНТ
        if message.document:
            await message.answer("Документ получен 📄 (обработка пока отключена)")
            return

    except Exception as e:
        print("ERROR:", e)
        await message.answer(f"Ошибка: {e}")

# запуск
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
