from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_start_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text='/all'), types.KeyboardButton(text='/read'),
                types.KeyboardButton(text='/add'), types.KeyboardButton(text='/delete'),
                types.KeyboardButton(text='/end'), types.KeyboardButton(text='/cancel'))
    builder.adjust(2, 2, 2)
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder='Ожидаю вашу команду.'
    )