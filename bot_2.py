import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
from docx import Document

print("🚀 BOT STARTED")

# 🔑 ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TELEGRAM_TOKEN =", TELEGRAM_TOKEN)
print("OPENAI_API_KEY =", OPENAI_API_KEY)

# ❗ жёсткая проверка
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY не найден")

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
    print("📩 /start")
    await message.answer("Выберите язык 👇", reply_markup=kb)

# основной обработчик
@dp.message()
async def handle(message: types.Message):
    print("📩 MESSAGE:", message.text)

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
   import base64

if message.photo:
    try:
        print("📸 PHOTO")

        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        # скачать файл
        file_path = file.file_path
        local_path = f"downloads/{photo.file_id}.jpg"
        await bot.download_file(file_path, local_path)

        # конвертировать в base64
        with open(local_path, "rb") as f:
            image_bytes = f.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Опиши изображение"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
        )

        reply = response.choices[0].message.content or "Хатолик 😢"
        await message.answer(reply)

    except Exception as e:
        print("❌ PHOTO ERROR:", e)
        await message.answer("Ошибка фото 😢")

    return

    # 📄 ДОКУМЕНТ
    if message.document:
        try:
            print("📄 DOC")

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
            print("❌ DOC ERROR:", e)
            await message.answer("Ошибка документа 😢")
        return

    # 💬 ТЕКСТ
    try:
        print("💬 TEXT запрос в OpenAI")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ]
        )

        reply = response.choices[0].message.content or "Пустой ответ 😢"
        await message.answer(reply)

    except Exception as e:
        print("❌ TEXT ERROR:", e)

        if "quota" in str(e):
            await message.answer("❌ Нет баланса OpenAI")
        else:
            await message.answer("Ошибка 😢")

# запуск
async def main():
    print("🤖 Бот запущен...")

    await bot.delete_webhook(drop_pending_updates=True)  # 🔥 КЛЮЧЕВОЕ

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
