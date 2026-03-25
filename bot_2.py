import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI
from docx import Document
import os


# 🔑 ключи
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# 📁 папка для файлов
os.makedirs("downloads", exist_ok=True)

# 🌍 языки пользователей
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

    # 🌍 выбор языка
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
    elif lang == "uz":
        system_prompt = "Faqat o'zbek tilida javob ber."

    # 📸 ФОТО
    if message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_path = file.file_path

        image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
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

            reply = response.choices[0].message.content
            await message.answer(reply)

        except Exception as e:
            print(e)
            await message.answer("Ошибка фото 😢")

        return

    # 📄 ДОКУМЕНТЫ
    if message.document:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        file_name = message.document.file_name

        local_path = f"downloads/{file_name}"
        await bot.download_file(file_path, local_path)

        try:
            if file_name.endswith(".docx"):
                doc = Document(local_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            else:
                await message.answer("Пока только .docx 😢")
                return

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Кратко объясни:\n{text[:3000]}"}
                ]
            )

            reply = response.choices[0].message.content
            await message.answer(reply)

        except Exception as e:
            print(e)
            await message.answer("Ошибка документа 😢")

        return

    # 💬 ТЕКСТ
    user_text = message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        )

        reply = response.choices[0].message.content
        await message.answer(reply)

    except Exception as e:
        print(e)

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
