import os
import re
import sqlite3
import uuid
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    WebAppInfo
)

# Ваши данные
BOT_TOKEN = "8984282221:AAHQg9oUfzoGDZM_acrv8K-LEW4Eo9UrA14"
ADMIN_ID = 8064940088
LAVA_SHOP_ID = "YOUR_LAVA_SHOP_ID"  # Замените на ваш Shop ID от Lava
WEBSITE_URL = "https://ваш-сайт.kz"   # Укажите адрес вашего сайта
TG_CHANNEL_URL = "https://t.me/ваш_канал" # Укажите ссылку на ваш ТГ-канал

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            product TEXT,
            amount REAL,
            address TEXT,
            phone TEXT,
            status TEXT,
            track_number TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN track_number TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

# ==================== СОСТОЯНИЯ (FSM) ====================
class OrderStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_screenshot = State()

class AdminStates(StatesGroup):
    waiting_for_track = State()  # Ожидание ввода трек-номера
    waiting_for_custom_message = State()  # Ожидание ввода личного сообщения покупателю

# Главное меню с сайтом и ТГ-каналом
def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌐 Открыть наш сайт", web_app=WebAppInfo(url=WEBSITE_URL))],
            [KeyboardButton(text="📢 Наш Telegram-канал")],
            [KeyboardButton(text="📄 Оферта и Политика"), KeyboardButton(text="📦 Условия доставки")]
        ],
        resize_keyboard=True
    )

# Текст-пример для ввода адреса
ADDRESS_EXAMPLE_TEXT = (
    "📦 **Введите ваши данные для доставки Казпочтой.**\n\n"
    "⚠️ *Указывайте данные внимательно по следующему примеру:*\n"
    "▫️ **ФИО:** Иванов Иван Иванович\n"
    "▫️ **Область / Город:** СКО, г. Петропавловск\n"
    "▫️ **Улица, дом, квартира:** ул. Абая, д. 10, кв. 15\n"
    "▫️ **Почтовый индекс:** 150000\n\n"
    "✍️ Напишите ваши данные в одном сообщении ниже:"
)

# ==================== СТАРТ И ССЫЛКИ С САЙТА ====================

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    args = command.args

    if args == "nike":
        await state.update_data(product="👟 Кроссовки Nike Air (45 000 тг)", amount=45000.0)
        await state.set_state(OrderStates.waiting_for_address)
        await message.answer(
            f"🛍 Вы выбрали: **Кроссовки Nike Air (45 000 тг)**\n\n{ADDRESS_EXAMPLE_TEXT}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return
        
    elif args == "hoodie":
        await state.update_data(product="👕 Худи Oversize (25 000 тг)", amount=25000.0)
        await state.set_state(OrderStates.waiting_for_address)
        await message.answer(
            f"🛍 Вы выбрали: **Худи Oversize (25 000 тг)**\n\n{ADDRESS_EXAMPLE_TEXT}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Приветствие с информацией о канале и правилами (без возврата)
    start_text = (
        "👋 **Добро пожаловать в наш официальный магазин!**\n\n"
        "🌐 Весь каталог товаров доступен на нашем сайте. Выбирайте нужную вещь и нажимайте кнопку заказа — бот поможет быстро всё оформить!\n\n"
        "📢 **Наш Telegram-канал:** Подписывайтесь, чтобы следить за новинками и скидками!\n"
        f"👉 [Перейти в канал]({TG_CHANNEL_URL})\n\n"
        "📌 **Важная информация:**\n"
        "• Все товары отправляются Казпочтой по указанным вами данным.\n"
        "• ⚠️ **Обмен и возврат товара не предусмотрен.** Пожалуйста, сверяйте размеры и данные перед оплатой.\n\n"
        "Воспользуйтесь меню ниже для навигации:"
    )
    await message.answer(start_text, reply_markup=main_menu_kb(), parse_mode="Markdown", disable_web_page_preview=True)

@router.message(F.text == "📢 Наш Telegram-канал")
async def show_channel(message: Message):
    await message.answer(
        f"📢 Подписывайтесь на наш официальный Telegram-канал:\n{TG_CHANNEL_URL}",
        disable_web_page_preview=True
    )

@router.message(F.text == "📄 Оферта и Политика")
async def show_terms(message: Message):
    text = (
        "📜 **Договор оферты и Политика конфиденциальности**\n\n"
        "1. Общие положения: Магазин осуществляет дистанционную продажу товаров.\n"
        "2. Оплата и Доставка: Заказ передается в доставку после 100% предоплаты и предоставления чека.\n"
        "3. Возврат: Продажа является окончательной, возврат и обмен товаров надлежащего качества не производится."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📦 Условия доставки")
async def show_delivery_returns(message: Message):
    text = (
        "🚚 **Условия доставки**\n\n"
        "• Доставка осуществляется службой **Казпочта**.\n"
        "• Сроки доставки: от 3 до 14 рабочих дней в зависимости от региона.\n"
        "• После отправки администратор вышлет вам трек-номер (талон) для отслеживания."
    )
    await message.answer(text, parse_mode="Markdown")

# ==================== АДРЕС И ТЕЛЕФОН ====================

@router.message(OrderStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 10:
        await message.answer(
            "⚠️ **Слишком короткий адрес.**\n Пожалуйста, укажите полные данные (ФИО, Город/Область, Улица, Дом/Квартира и Индекс):"
        )
        return
        
    await state.update_data(address=address)
    await state.set_state(OrderStates.waiting_for_phone)
    await message.answer(
        "📞 **Введите ваш номер телефона для связи:**\n"
        "(Пример: `+77011234567` или `87771234567`)",
        parse_mode="Markdown"
    )

@router.message(OrderStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?[0-9]{10,15}$', clean_phone):
        await message.answer("⚠️ Неверный формат номера. Введите корректный номер телефона:")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()
    
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    
    pay_link = f"https://pay.lava.kz/pay?shopId={LAVA_SHOP_ID}&amount={data['amount']}&orderId={order_id}"
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (order_id, user_id, product, amount, address, phone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (order_id, message.from_user.id, data['product'], data['amount'], data['address'], phone, "pending_screenshot"))
    conn.commit()
    conn.close()

    pay_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить счет в Lava", url=pay_link)]
    ])

    await state.update_data(order_id=order_id)
    await state.set_state(OrderStates.waiting_for_screenshot)
    
    await message.answer(
        f"📋 **Заказ успешно создан!**\n\n"
        f"🆔 Номер заказа: `{order_id}`\n"
        f"🛍 Товар: {data['product']}\n"
        f"💰 Сумма к оплате: {data['amount']} KZT\n\n"
        f"1️⃣ Нажмите кнопку ниже и оплатите счет через Lava.\n"
        f"2️⃣ После оплаты **отправьте скриншот чека (фотографию)** прямо сюда в чат!",
        reply_markup=pay_kb,
        parse_mode="Markdown"
    )

# ==================== СКРИНШОТ ОТ КЛИЕНТА ====================

@router.message(OrderStates.waiting_for_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    product = data.get("product")
    address = data.get("address")
    phone = data.get("phone")
    
    photo_file_id = message.photo[-1].file_id
    
    await message.answer(
        "⏳ Скриншот успешно отправлен администратору на проверку!\n"
        "Ожидайте подтверждения и трек-номера для отслеживания.",
        reply_markup=main_menu_kb()
    )
    await state.clear()

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{order_id}")
        ]
    ])

    username = f"@{message.from_user.username}" if message.from_user.username else "нет никнейма"
    
    admin_caption = (
        f"🚨 **Новый чек по заказу!**\n\n"
        f"🆔 ID заказа: `{order_id}`\n"
        f"👤 Покупатель: {username} (ID: `{message.from_user.id}`)\n"
        f"🛍 Товар: {product}\n"
        f"📍 Адрес: {address}\n"
        f"📞 Телефон: {phone}\n\n"
        f"Проверьте поступление денег и выберите действие:"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=admin_caption,
        reply_markup=admin_kb,
        parse_mode="Markdown"
    )

@router.message(OrderStates.waiting_for_screenshot)
async def wrong_screenshot_type(message: Message):
    await message.answer("⚠️ Пожалуйста, отправьте именно **фотографию (скриншот)** чека об оплате.")

# ==================== УПРАВЛЕНИЕ АДМИНА (КНОПКИ ТРЕКА И ОТВЕТА) ====================

@router.callback_query(F.data.startswith(("confirm_", "reject_")))
async def admin_decision(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора.", show_alert=True)
        return

    action, order_id = callback.data.split("_", 1)
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, product, status FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        await callback.answer("Заказ не найден в базе.", show_alert=True)
        return
        
    user_id, product, status = row

    if action == "confirm":
        cursor.execute("UPDATE orders SET status = 'paid' WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()

        # Две кнопки у админа после подтверждения оплаты
        admin_actions_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Ввести трек Казпочты", callback_data=f"settrack_{order_id}")],
            [InlineKeyboardButton(text="💬 Написать покупателю", callback_data=f"reply_{order_id}")]
        ])

        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n**✅ Оплата подтверждена!**",
            reply_markup=admin_actions_kb,
            parse_mode="Markdown"
        )
        await callback.answer("Оплата подтверждена!")

        try:
            await bot.send_message(
                user_id,
                f"🎉 **Ваш заказ `{order_id}` подтвержден!**\n\n"
                f"Оплата за товар *{product}* успешно получена. Ожидайте отправки посылки и трек-номера.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    elif action == "reject":
        cursor.execute("UPDATE orders SET status = 'rejected' WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()

        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n**❌ Заказ отклонен**",
            parse_mode="Markdown"
        )
        await callback.answer("Заказ отклонен.")

        try:
            await bot.send_message(
                user_id,
                f"❌ **К сожалению, ваш заказ `{order_id}` отклонен.**\n\n"
                f"Чек не прошел проверку.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

# 1. Ввод трек-номера
@router.callback_query(F.data.startswith("settrack_"))
async def prompt_for_track(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    order_id = callback.data.split("_", 1)[1]
    await state.set_state(AdminStates.waiting_for_track)
    await state.update_data(order_id=order_id)
    
    await callback.message.answer(
        f"✍️ Введите **трек-номер Казпочты** (или талончик) для заказа `{order_id}`:\n"
        f"(Отправьте текст следующим сообщением)",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_track, F.from_user.id == ADMIN_ID)
async def save_and_send_track(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    track_number = message.text.strip()
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET track_number = ? WHERE order_id = ?", (track_number, order_id))
    cursor.execute("SELECT user_id, product FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user_id, product = row
        try:
            await bot.send_message(
                user_id,
                f"📦 **Ваш заказ отправлен!**\n\n"
                f"🆔 Номер заказа: `{order_id}`\n"
                f"🛍 Товар: {product}\n"
                f"📮 Трек-номер (талон) Казпочты: `{track_number}`\n\n"
                f"Вы можете отслеживать перемещение посылки на официальном сайте или в приложении Казпочты.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
            
        await message.answer(
            f"✅ Трек-номер `{track_number}` успешно отправлен покупателю по заказу `{order_id}`!",
            parse_mode="Markdown"
        )
    else:
        await message.answer("⚠️ Ошибка: заказ не найден.")
        
    await state.clear()

# 2. Написать произвольное сообщение покупателю
@router.callback_query(F.data.startswith("reply_"))
async def prompt_for_reply(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    order_id = callback.data.split("_", 1)[1]
    await state.set_state(AdminStates.waiting_for_custom_message)
    await state.update_data(order_id=order_id)
    
    await callback.message.answer(
        f"💬 Напишите сообщение для покупателя по заказу `{order_id}`:\n"
        f"(Отправьте текст следующим сообщением)",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_custom_message, F.from_user.id == ADMIN_ID)
async def send_custom_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    custom_text = message.text.strip()
    
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user_id = row[0]
        try:
            await bot.send_message(
                user_id,
                f"📩 **Сообщение от магазина по заказу `{order_id}`:**\n\n{custom_text}",
                parse_mode="Markdown"
            )
            await message.answer(f"✅ Сообщение успешно доставлено покупателю по заказу `{order_id}`!")
        except Exception:
            await message.answer("❌ Не удалось доставить сообщение покупателю (возможно, он заблокировал бота).")
    else:
        await message.answer("⚠️ Ошибка: заказ не найден.")
        
    await state.clear()

async def main():
    dp.include_router(router)
    print("🤖 Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())