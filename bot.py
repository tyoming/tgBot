import sys
import asyncio
import logging

from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database
import keyboards
import scheduler
import states

dp = Dispatcher()


@dp.message(F.text, Command('start'))
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        f'Привет, {message.from_user.full_name}!\n'
        f'Я буду напоминать о важных заметках, чтобы вы ничего не забыли.\n'
        f'Чтобы увидеть функционал бота, напиши /help',
        reply_markup=keyboards.get_start_keyboard()
    )


@dp.message(F.text, Command('help'))
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        '/all - просмотреть все заметки.\n'
        '/read - прочитать заметку.\n'
        '/add - добавить заметку.\n'
        '/delete - удалить заметку.\n'
        '/end - конец ввода содержания заметки.\n'
        '/cancel - отмена последнего действия (чтения, добавления и удаления заметки).'
    )


@dp.message(F.text, Command('cancel'))
async def cmd_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'now' in data:
        data['now'].delete()
    await message.reply(
        'Действие было отменено.'
    )
    await state.clear()


async def main() -> None:
    while True:
        try:
            if database.one("SHOW TABLES FROM bot LIKE 'resources'"):
                break
        except:
            logging.exception('Wait creating of mysql database and table')
            await asyncio.sleep(10)

    dp.include_routers(states.router)

    await states.bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(scheduler.check_resources())
    await dp.start_polling(states.bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
