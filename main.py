import asyncio
import logging
import sys

from tortoise.functions import Lower
from datetime import datetime, timezone, timedelta

import aiogram.exceptions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, FSInputFile

# Сессия и сама модель базы данных
from data import db_session
from data.models import Users
# Токен тг бота
from config import BOT_TOKEN

dp = Dispatcher()


# Состояние для создания диалога для системы поиска по никнейму или id
class NameStates(StatesGroup):
    waiting_nick_or_id = State()


# Состояние для создания диалога для системы аватарки и её загрузки
class AvatarStates(StatesGroup):
    waiting_for_photo = State()


# /start команда
@dp.message(Command('start'))
@dp.message(F.text == 'Меню')
async def command_start_handler(message: Message) -> None:
    # Проверка есть ли человек в базе и если нет то создает в бд запись и приветствует пользователя
    if await Users.get_or_none(telegram_id=message.from_user.id):
        # Кнопки Reply
        kb = [
            [
                types.KeyboardButton(text="Кликер 🔘"),
                types.KeyboardButton(text="Автокликер 💯"),
                types.KeyboardButton(text="Профиль👻"),
                types.KeyboardButton(text="Магазин🛒"),
                types.KeyboardButton(text="Топ 📣"),
            ],
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                       input_field_placeholder="Приветик :3")
        # Фото логотип
        photo = FSInputFile('Picture/logo.jpg')
        await message.answer_photo(photo=photo, caption=f"Привет, давно не виделись! ♪～(´ε｀ )\n\n"
                                                        f"Скорей кликать! Вперёд, вперёд, вперёд!",
                                   reply_markup=keyboard)
    else:
        await Users.create(name=message.from_user.username, telegram_id=message.from_user.id, money=0)
        # Кнопки Reply
        kb = [
            [
                types.KeyboardButton(text="Кликер 🔘"),
                types.KeyboardButton(text="Автокликер 💯"),
                types.KeyboardButton(text="Профиль👻"),
                types.KeyboardButton(text="Магазин🛒"),
                types.KeyboardButton(text="Топ 📣"),
            ],
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                       input_field_placeholder="Приветик :3")
        # Фото логотип
        photo = FSInputFile('Picture/logo.jpg')
        await message.answer_photo(photo=photo, caption=f'Приветик!\n'
                                                        f'Я кликер-бот ヾ(＾-＾)ノ\n\n'
                                                        f'⋆ ˚｡⋆୨୧˚ ˚୨୧⋆｡˚ ⋆\n\n'
                                                        f'Нажми на кнопки снизу, '
                                                        f'чтобы перейти в интересующий тебя раздел 👇',
                                   reply_markup=keyboard)


# /help команда
@dp.message(Command('help'))
async def command_start_handler(message: Message) -> None:
    await message.answer(f"/start\n"
                         f"/help\n"
                         f"/restart\n"
                         f"/click\n"
                         f"/autoclicker\n"
                         f"/profile\n"
                         f"/shop\n"
                         f"/top\n"
                         f"/user @username or telegram_id\n")


@dp.message(F.text == 'Профиль игрока')
async def user_get_button(message: Message, state: FSMContext) -> None:
    # Кнопки Reply
    kb = [
        [
            types.KeyboardButton(text="Отмена"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Username или telegram id")
    await message.answer('Введите имя или id', reply_markup=keyboard)
    # Ставит состояние ожидание никнейма или тг айди для поиска
    await state.set_state(NameStates.waiting_nick_or_id)


@dp.message(NameStates.waiting_nick_or_id, F.text == 'Отмена')
async def cancel_name_search(message: types.Message, state: FSMContext):
    # Очищает состояние и перекидывает обратно в профиль
    await state.clear()
    await command_profile_handler(message)


@dp.message(NameStates.waiting_nick_or_id, F.text != 'Отмена')
async def name_search(message: types.Message, state: FSMContext):
    # Проверка сообщения на никнейм или тг айди
    if message.text.startswith('@'):
        user = await Users.annotate(name=Lower('name')).filter(name=message.text[1:].lower()).get_or_none()
    elif message.text.isnumeric():
        user = await Users.get_or_none(telegram_id=int(message.text))
    else:
        user = await Users.annotate(name=Lower('name')).filter(name=message.text.lower()).get_or_none()
    # Кнопки Reply
    kb = [
        [
            types.KeyboardButton(text="Меню"),
            types.KeyboardButton(text="Профиль игрока"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Приветик :3")
    if user:
        # Если у пользователя есть аватарка прикрипляет её
        if user.avatar:
            await message.answer_photo(photo=user.avatar, caption=f"@{user.name} | {user.telegram_id}\n"
                                                                  f"Очки: {user.money}\n"
                                                                  f"Очки/клик: {user.money_in_click}\n"
                                                                  f"Очки/секунду: {user.money_in_sec}\n"
                                                                  f"Максимальное афк время: {user.max_afk_time}",
                                       reply_markup=keyboard)
        else:
            await message.answer(f"@{user.name} | {user.telegram_id}\n"
                                 f"Очки: {user.money}\n"
                                 f"Очки/клик: {user.money_in_click}\n"
                                 f"Очки/секунду: {user.money_in_sec}\n"
                                 f"Максимальное афк время: {user.max_afk_time}", reply_markup=keyboard)
    else:
        await message.answer('Пользователь не найден', reply_markup=keyboard)
    await state.clear()


@dp.message(F.text.regexp(r'/u_(.*)'))
async def user_get_short(message: Message) -> None:
    # Поиск юзера с помощью конструкции /u_*tg_id* сделанно для топа игроков и просмотра их профиля
    if message.text[3:].isnumeric():
        user = await Users.get_or_none(telegram_id=int(message.text[3:]))
    else:
        user = None
    # Кнопки Reply
    kb = [
        [
            types.KeyboardButton(text="Меню")
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Приветик :3")
    if user:
        if user.avatar:
            await message.answer_photo(photo=user.avatar, caption=f"@{user.name} | {user.telegram_id}\n"
                                                                  f"Очки: {user.money}\n"
                                                                  f"Очки/клик: {user.money_in_click}\n"
                                                                  f"Очки/секунду: {user.money_in_sec}\n"
                                                                  f"Максимальное афк время: {user.max_afk_time}",
                                       reply_markup=keyboard)
        else:
            await message.answer(f"@{user.name} | {user.telegram_id}\n"
                                 f"Очки: {user.money}\n"
                                 f"Очки/клик: {user.money_in_click}\n"
                                 f"Очки/секунду: {user.money_in_sec}\n"
                                 f"Максимальное афк время: {user.max_afk_time}", reply_markup=keyboard)
    else:
        await message.answer('Пользователь не найден', reply_markup=keyboard)


# Команда /user
@dp.message(Command('user'))
async def user_get(message: Message) -> None:
    # Проверка какой тип написал игрок для поиска
    if message.text.startswith('/user @'):
        user = await Users.annotate(name_lower=Lower('name')).filter(name_lower=message.text[7:].lower()).first()
    elif message.text[6:].isnumeric():
        user = await Users.get_or_none(telegram_id=int(message.text[6:]))
    else:
        user = await Users.annotate(name_lower=Lower('name')).filter(name_lower=message.text[6:].lower()).first()
    # Кнопки Reply
    kb = [
        [
            types.KeyboardButton(text="Меню")
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Приветик :3")
    if user:
        if user.avatar:
            await message.answer_photo(photo=user.avatar, caption=f"@{user.name} | {user.telegram_id}\n"
                                                                  f"Очки: {user.money}\n"
                                                                  f"Очки/клик: {user.money_in_click}\n"
                                                                  f"Очки/секунду: {user.money_in_sec}\n"
                                                                  f"Максимальное афк время: {user.max_afk_time}",
                                       reply_markup=keyboard)
        else:
            await message.answer(f"@{user.name} | {user.telegram_id}\n"
                                 f"Очки: {user.money}\n"
                                 f"Очки/клик: {user.money_in_click}\n"
                                 f"Очки/секунду: {user.money_in_sec}\n"
                                 f"Максимальное афк время: {user.max_afk_time}", reply_markup=keyboard)
    else:
        await message.answer('Пользователь не найден', reply_markup=keyboard)


# Команда /top
@dp.message(Command('top'))
@dp.message(F.text == 'Топ 📣')
async def command_top(message: Message) -> None:
    # Получение топ 10 игроков по количеству очков
    top = await Users.all().order_by('-money').limit(10)
    res = ['Это топ игроков! Может быть и ты тут появишься (｡･ω･｡)', '', 'Статистика лучших игроков и их профили:',
           'Имя - очки - дата регистрации']
    for i in range(len(top)):
        res.append(f'{i + 1}. @{top[i].name} - {top[i].money} - {top[i].created_date.strftime("%Y.%m.%d")} '
                   f'/u_{top[i].telegram_id}')
    kb = [
        [
            types.KeyboardButton(text="Меню"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Какие же крутые люди")
    await message.answer('\n'.join(res), reply_markup=keyboard)


# Команда /clicker
@dp.message(Command('clicker'))
@dp.message(F.text == 'Кликер 🔘')
async def command_start_handler(message: Message) -> None:
    kb = [
        [
            types.KeyboardButton(text="👌Click"),
            types.KeyboardButton(text="Меню"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Хватит читать кликай давай")
    await message.answer(f"Кликай на кнопку и зарабатывай очки! ★\n\n"
                         f"Очки можно тратить в магазине, не забудь про это ꉂ(ˊᗜˋ*)", reply_markup=keyboard)


# Обработка кликов
@dp.message(F.text == '👌Click')
async def click_text(message: Message) -> None:
    user = await Users.get(telegram_id=message.from_user.id)
    kb = [
        [
            types.KeyboardButton(text="👌Click"),
            types.KeyboardButton(text="Меню"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Хватит читать кликай давай")
    user.money += user.money_in_click
    await user.save()
    await message.answer(f"+{user.money_in_click} очков\n"
                         f"Очки: {user.money}", reply_markup=keyboard)


# команда Профиль
@dp.message(Command('profile'))
@dp.message(F.text == 'Профиль👻')
async def command_profile_handler(message: Message) -> None:
    user = await Users.get(telegram_id=message.from_user.id)
    kb = [
        [
            types.KeyboardButton(text="Меню"),
            types.KeyboardButton(text="Установить аватарку"),
            types.KeyboardButton(text="Профиль игрока"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Вау магия")
    # Получение аватарки пользователя и её сохранение для топа
    profile_photo = await message.from_user.get_profile_photos()
    if user.avatar:
        await message.answer_photo(photo=user.avatar, caption=f"Это твой профиль! Вот твоя статистика:\n\n"
                                                              f"@{user.name} | {user.telegram_id}\n"
                                                              f"Очки: {user.money}\n"
                                                              f"Очки/клик: {user.money_in_click}\n"
                                                              f"Очки/секунду: {user.money_in_sec}\n"
                                                              f"Максимальное афк время: {user.max_afk_time}",
                                   reply_markup=keyboard)
    elif profile_photo.photos:
        photo = profile_photo.photos[0][0].file_id
        user.avatar = photo
        await user.save()
        await message.answer_photo(photo=photo, caption=f"Это твой профиль! Вот твоя статистика:\n\n"
                                                        f"@{user.name} | {user.telegram_id}\n"
                                                        f"Очки: {user.money}\n"
                                                        f"Очки/клик: {user.money_in_click}\n"
                                                        f"Очки/секунду: {user.money_in_sec}\n"
                                                        f"Максимальное афк время: {user.max_afk_time}",
                                   reply_markup=keyboard)
    else:
        await message.answer(f"Это твой профиль! Вот твоя статистика:\n\n"
                             f"@{user.name} | {user.telegram_id}\n"
                             f"Очки: {user.money}\n"
                             f"Очки/клик: {user.money_in_click}\n"
                             f"Очки/секунду: {user.money_in_sec}\n"
                             f"Максимальное афк время: {user.max_afk_time}", reply_markup=keyboard)


# Установка аватарки
@dp.message(F.text == 'Установить аватарку')
async def set_avatar(message: Message, state: FSMContext) -> None:
    kb = [
        [
            types.KeyboardButton(text="Отмена"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True,
                                   input_field_placeholder="Вау магия")
    await message.answer('Жду фото', reply_markup=keyboard)
    # Включение состояние ожидание фотографии
    await state.set_state(AvatarStates.waiting_for_photo)


# Отмена аватарки
@dp.message(AvatarStates.waiting_for_photo, F.text == 'Отмена')
async def cancel_user_photo(message: types.Message, state: FSMContext):
    # Очистка состояния
    await state.clear()
    await command_profile_handler(message)


# Сохранение аватарки
@dp.message(AvatarStates.waiting_for_photo, F.photo)
async def store_user_photo(message: types.Message, state: FSMContext):
    user = await Users.get(telegram_id=message.from_user.id)
    user.avatar = message.photo[-1].file_id
    await user.save()
    await message.answer("Фотография успешно сохранена!")
    await state.clear()
    await command_profile_handler(message)


# Команда /autoclicker
@dp.message(Command('autoclicker'))
@dp.message(F.text == 'Автокликер 💯')
async def command_autoclicker_handler(message: Message) -> None:
    user = await Users.get(telegram_id=message.from_user.id)
    # Inline кнопки
    builder = InlineKeyboardBuilder()
    # Проверка запускал ли пользователь автокликер
    if user.afk_worked:
        builder.add(types.InlineKeyboardButton(
            text=f"🔴Стоп 📣",
            callback_data="stop_autoclick")
        )
        builder.add(types.InlineKeyboardButton(
            text=f"🔃Рестарт",
            callback_data="restart_autoclick")
        )
        # Высчитывается сколько работает автокликер для вычесления дохода
        afk_time = datetime.now(timezone.utc) - user.start_afk_time
        # Проверяется на максимально допущенное время автокликера
        if afk_time > user.max_afk_time:
            await message.answer(f"Это автокликер\n"
                                 f"Откинься на спинку кресла и расслабься,  бот всё сделает за тебя (*˘︶˘*)\n"
                                 f"{user.money_in_sec} очки/секунду\n"
                                 f"+ {user.max_afk_time.seconds * user.money_in_sec} очков (MAX)\n"
                                 f"work time: 0 min",
                                 reply_markup=builder.as_markup())
        else:
            # Вычисляется сколько он еще будет работать
            work = user.max_afk_time - afk_time
            await message.answer(f"Это автокликер\n"
                                 f"Откинься на спинку кресла и расслабься,  бот всё сделает за тебя (*˘︶˘*)\n"
                                 f"{user.money_in_sec} очки/секунду\n"
                                 f"+{afk_time.seconds * user.money_in_sec} очков (макс.)\n"
                                 f"Время работы: {work.seconds // 60} мин.",
                                 reply_markup=builder.as_markup())
    else:
        builder.add(types.InlineKeyboardButton(
            text="🟢Старт",
            callback_data="start_autoclick")
        )
        await message.answer(f"Это автокликер\n"
                             f"Откинься на спинку кресла и расслабься,  бот всё сделает за тебя (*˘︶˘*)\n"
                             f"Сплю....", reply_markup=builder.as_markup())


# Обработка callback от inline кнопки автокликера. Запуск автокликера
@dp.callback_query(F.data == "start_autoclick")
async def start_autoclicker(callback: types.CallbackQuery):
    user = await Users.get(telegram_id=callback.from_user.id)
    user.start_afk_time = datetime.now(timezone.utc)
    user.afk_worked = True
    await user.save()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text=f"🔴Стоп 📣",
        callback_data="stop_autoclick")
    )
    builder.add(types.InlineKeyboardButton(
        text=f"🔃Рестарт",
        callback_data="restart_autoclick")
    )
    await callback.message.edit_text(f"Это автокликер\n"
                                     f"{user.money_in_sec} очков/сек.", reply_markup=builder.as_markup())


# Обработка callback от inline кнопки автокликера. Оставновка автокликера
@dp.callback_query(F.data == "stop_autoclick")
async def stop_autoclicker(callback: types.CallbackQuery):
    user = await Users.get(telegram_id=callback.from_user.id)
    afk_time = datetime.now(timezone.utc) - user.start_afk_time
    if afk_time > user.max_afk_time:
        afk_time = user.max_afk_time
    user.money += afk_time.seconds * user.money_in_sec
    user.afk_worked = False
    await user.save()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="🟢Старт",
        callback_data="start_autoclick")
    )
    await callback.message.edit_text(f"Autoclicker 3000\n"
                                     f"+{afk_time.seconds * user.money_in_sec} очков\n"
                                     f"Сплю....", reply_markup=builder.as_markup())


# Обработка callback от inline кнопки автокликера. Рестарт автокликера
@dp.callback_query(F.data == "restart_autoclick")
async def stop_autoclicker(callback: types.CallbackQuery):
    user = await Users.get(telegram_id=callback.from_user.id)
    afk_time = datetime.now(timezone.utc) - user.start_afk_time
    if afk_time > user.max_afk_time:
        afk_time = user.max_afk_time
    user.money += afk_time.seconds * user.money_in_sec
    user.start_afk_time = datetime.now(timezone.utc)
    user.afk_worked = True
    await user.save()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text=f"🔴СТоп 📣",
        callback_data="stop_autoclick")
    )
    builder.add(types.InlineKeyboardButton(
        text=f"🔃Рестарт",
        callback_data="restart_autoclick")
    )
    try:
        await callback.message.edit_text(f"Autoclicker 3000\n"
                                         f"{user.money_in_sec} очков/сек.\n"
                                         f"+{afk_time.seconds * user.money_in_sec} очков\n"
                                         f"Рестарт....", reply_markup=builder.as_markup())
    except aiogram.exceptions.TelegramBadRequest:
        await callback.answer('Рестарт')


# Команда /shop
@dp.message(Command('shop'))
@dp.message(F.text == 'Магазин🛒')
async def command_autoclicker_handler(message: Message) -> None:
    user = await Users.get(telegram_id=message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Очки/клик", callback_data="da"))
    price_click = int(100 * (1.05 ** user.buy_money_in_click))
    builder.add(types.InlineKeyboardButton(text=f"🟢{price_click}", callback_data="buy_money_click"))
    builder.add(types.InlineKeyboardButton(text="Очки/сек.", callback_data="da"))
    price_sec = int(100 * (1.05 ** user.buy_money_in_sec))
    builder.add(types.InlineKeyboardButton(text=f"🟢{price_sec}", callback_data="buy_money_sec"))
    builder.add(types.InlineKeyboardButton(text="Максимальное афк время", callback_data="da"))
    price_afk_time = int(100 * (1.05 ** user.buy_max_afk_time))
    builder.add(types.InlineKeyboardButton(text=f"🟢{price_afk_time}", callback_data="buy_max_afk"))
    builder.adjust(2)
    await message.answer(f"╭═════════💜═╮\n"
                         f"  Добро пожаловать\n"
                         f"   В магазинчик\n"
                         f"╰═💜═════════╯", reply_markup=builder.as_markup())


# Обработка callback при покупки в магазине
@dp.callback_query(F.data == "buy_money_click")
async def shop_money_click(callback: types.CallbackQuery) -> None:
    user = await Users.get(telegram_id=callback.from_user.id)
    price_click = int(100 * (1.05 ** user.buy_money_in_click))
    if price_click <= user.money:
        user.money -= price_click
        user.money_in_click += 1
        user.buy_money_in_click += 1
        await user.save()
        await callback.answer('Успешно купленно')
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Очки/клик", callback_data="da"))
        price_click = int(100 * (1.05 ** user.buy_money_in_click))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_click}", callback_data="buy_money_click"))
        builder.add(types.InlineKeyboardButton(text="Очки/сек.", callback_data="da"))
        price_sec = int(100 * (1.05 ** user.buy_money_in_sec))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_sec}", callback_data="buy_money_sec"))
        builder.add(types.InlineKeyboardButton(text="Максимальное афк время", callback_data="da"))
        price_afk_time = int(100 * (1.05 ** user.buy_max_afk_time))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_afk_time}", callback_data="buy_max_afk"))
        builder.adjust(2)
        await callback.message.edit_text(f"╭═════════💜═╮\n"
                                         f"  Добро пожаловать\n"
                                         f"   В магазинчик\n"
                                         f"╰═💜═════════╯", reply_markup=builder.as_markup())
    else:
        await callback.answer('Недостаточно средств')


# Обработка callback при покупки в магазине
@dp.callback_query(F.data == "buy_money_sec")
async def shop_money_click(callback: types.CallbackQuery) -> None:
    user = await Users.get(telegram_id=callback.from_user.id)
    price_click = int(100 * (1.05 ** user.buy_money_in_sec))
    if price_click <= user.money:
        user.money -= price_click
        user.money_in_sec += 1
        user.buy_money_in_sec += 1
        await user.save()
        await callback.answer('Успешно купленно')
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Очки/клик", callback_data="da"))
        price_click = int(100 * (1.05 ** user.buy_money_in_click))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_click}", callback_data="buy_money_click"))
        builder.add(types.InlineKeyboardButton(text="Очки/сек.", callback_data="da"))
        price_sec = int(100 * (1.05 ** user.buy_money_in_sec))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_sec}", callback_data="buy_money_sec"))
        builder.add(types.InlineKeyboardButton(text="Максимальное афк время", callback_data="da"))
        price_afk_time = int(100 * (1.05 ** user.buy_max_afk_time))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_afk_time}", callback_data="buy_max_afk"))
        builder.adjust(2)
        await callback.message.edit_text(f"╭═════════💜═╮\n"
                                         f"  Добро пожаловать\n"
                                         f"   В магазинчик\n"
                                         f"╰═💜═════════╯", reply_markup=builder.as_markup())
    else:
        await callback.answer('Недостаточно средств')


# Обработка callback при покупки в магазине
@dp.callback_query(F.data == "buy_max_afk")
async def shop_money_click(callback: types.CallbackQuery) -> None:
    user = await Users.get(telegram_id=callback.from_user.id)
    price_click = int(100 * (1.05 ** user.buy_max_afk_time))
    if price_click <= user.money:
        user.money -= price_click
        user.max_afk_time += timedelta(hours=1)
        user.buy_max_afk_time += 1
        await user.save()
        await callback.answer('Успешно купленно')
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="Очки/клик", callback_data="da"))
        price_click = int(100 * (1.05 ** user.buy_money_in_click))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_click}", callback_data="buy_money_click"))
        builder.add(types.InlineKeyboardButton(text="Очки/сек.", callback_data="da"))
        price_sec = int(100 * (1.05 ** user.buy_money_in_sec))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_sec}", callback_data="buy_money_sec"))
        builder.add(types.InlineKeyboardButton(text="Максимальное афк время", callback_data="da"))
        price_afk_time = int(100 * (1.05 ** user.buy_max_afk_time))
        builder.add(types.InlineKeyboardButton(text=f"🟢{price_afk_time}", callback_data="buy_max_afk"))
        builder.adjust(2)
        await callback.message.edit_text(f"╭═════════💜═╮\n"
                                         f"  Добро пожаловать\n"
                                         f"   В магазинчик\n"
                                         f"╰═💜═════════╯", reply_markup=builder.as_markup())
    else:
        await callback.answer('Недостаточно средств')


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Инцилизация базы данных
    await db_session.global_init("db/database.db", reset_db=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Логирование
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
