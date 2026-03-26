import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
from docx import Document

# 🔑 ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ❗ проверка ключей
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Нет TELEGRAM_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("❌ Нет OPENAI_API_KEY")

print("BOT STARTED")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# 📁 папка
os.makedirs("downloads", exist_ok=True)

# 🌍 язык
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

    # system prompt
    if lang == "ru":
        system_prompt = "Отвечай только на русском языке."
    elif lang == "en":
        system_prompt = "Answer only in English."
    else:
        system_prompt = "Faqat o'zbek tilida javob ber."

    # 📸 ФОТО
    if message.photo:
        try:
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)

            image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Опиши изображение"},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            )

            reply = response.choices[0].message.content or "Ошибка 😢"
            await message.answer(reply)

        except Exception as e:
            print("PHOTO ERROR:", e)
            await message.answer("Ошибка фото 😢")
        return

    # 📄 ДОКУМЕНТ
    if message.document:
        try:
            file = await bot.get_file(message.document.file_id)
            path = f"downloads/{message.document.file_name}"
            await bot.download_file(file.file_path, path)

            if not path.endswith(".docx"):
                await message.answer("Только .docx 😢")
                return

            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text[:3000]}
                ]
            )

            reply = response.choices[0].message.content or "Ошибка 😢"
            await message.answer(reply)

        except Exception as e:
            print("DOC ERROR:", e)
            await message.answer("Ошибка документа 😢")
        return

    # 💬 ТЕКСТ
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ]
        )

        reply = response.choices[0].message.content or "Ошибка 😢"
        await message.answer(reply)

    except Exception as e:
        print("TEXT ERROR:", e)

        if "quota" in str(e):
            await message.answer("❌ Нет баланса OpenAI")
        else:
            await message.answer("Ошибка 😢")

# запуск
async def main():
    print("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
