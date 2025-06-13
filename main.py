import json
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

with open("results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

class QuizState(StatesGroup):
    current = State()
    answers = State()

@dp.message(F.text.lower() == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Начать путь Судьбы", callback_data="start_quiz")]
    ])
    await message.answer(
        "Ты пробудился у причала Сейда Нин. Стражник молчит, но взгляд его ясен: твой путь начинается.\n\n"
        "Желаешь узнать, кто ты есть на самом деле?",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback, state: FSMContext):
    await state.update_data(current=0, answers=[])
    await send_question(callback.message, state)
    await callback.answer()

async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data["current"]
    q = questions[current]
    keyboard = InlineKeyboardBuilder()
    for i, opt in enumerate(q["options"], 1):
        keyboard.button(text=str(i), callback_data=f"answer_{i-1}")
    keyboard.adjust(len(q["options"]))
    text = (
        f"<b>Вопрос {current+1} из {len(questions)}</b>\n\n"
        f"{q['text']}\n\n" +
        "\n".join([f"<b>{i+1}.</b> {opt['text']}" for i, opt in enumerate(q['options'])])
    )
    await message.edit_text(text, reply_markup=keyboard.as_markup())

@dp.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback, state: FSMContext):
    data = await state.get_data()
    current = data["current"]
    selected = int(callback.data.split("_")[1])
    q = questions[current]
    answer = q["options"][selected]
    answers = data["answers"]
    answers.append({"scale": answer["scale"], "value": answer["value"]})
    await state.update_data(answers=answers)

    if current + 1 >= len(questions):
        await show_result(callback, state)
    else:
        await state.update_data(current=current + 1)
        await send_question(callback.message, state)
    await callback.answer()

async def show_result(callback, state: FSMContext):
    data = await state.get_data()
    answers = data["answers"]
    scores = {"IE": 0, "SN": 0, "TF": 0, "JP": 0}
    for ans in answers:
        scores[ans["scale"]] += ans["value"]

    result_type = ""
    result_type += "I" if scores["IE"] < 0 else "E"
    result_type += "S" if scores["SN"] < 0 else "N"
    result_type += "T" if scores["TF"] < 0 else "F"
    result_type += "J" if scores["JP"] < 0 else "P"

    result = results[result_type]

    await callback.message.answer(
        f"<b>🧭 Твой Путь завершён!</b>\n\n"
        f"<b>{result['title']}</b>\n\n"
        f"{result['description']}"
    )

    user = callback.from_user
    await bot.send_message(
        ADMIN_ID,
        f"🧙‍♂️ <b>Новый результат:</b>\n"
        f"<b>{result_type}</b> — {result['title']}\n"
        f"👤 @{user.username or user.full_name} ({user.id})"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Снова испытать себя", callback_data="start_quiz")]
    ])
    await callback.message.answer("Пожелаешь пройти путь заново?", reply_markup=keyboard)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
