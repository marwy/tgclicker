from tortoise.models import Model
from tortoise import fields
import datetime


class Users(Model):
    # Айди внутри игры
    id = fields.IntField(pk=True)
    # Телеграмм айди
    telegram_id = fields.IntField(null=True)
    # Никнейм пользователя
    name = fields.CharField(max_length=255, null=True)
    # Количество очков
    money = fields.IntField(null=True, default=0)
    # Очки/клик
    money_in_click = fields.IntField(null=True, default=1)
    # Очки/сек
    money_in_sec = fields.IntField(null=True, default=1)
    # Максимальное время автокликера
    max_afk_time = fields.TimeDeltaField(default=datetime.timedelta(hours=1))
    # Время когда пользователь запускает автокликер
    start_afk_time = fields.DatetimeField(null=True)
    # Работает ли автокликер
    afk_worked = fields.BooleanField(default=False)
    # Дата регистрации (Для топа и статистики)
    created_date = fields.DatetimeField(auto_now_add=True)
    # Сколько пользователь купил очков за клик
    buy_money_in_click = fields.IntField(null=True, default=1)
    # Сколько пользователь купил очков в секунду
    buy_money_in_sec = fields.IntField(null=True, default=1)
    # Сколько пользователь купил максимальное время автокликера
    buy_max_afk_time = fields.IntField(null=True, default=1)
    # Id аватарки
    avatar = fields.CharField(max_length=255, null=True)
    # Не реализовано :(((
    role = fields.CharField(max_length=255, null=True)