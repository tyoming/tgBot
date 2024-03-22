import asyncio
import logging
import datetime

import pytz

import database
import states


async def check_resources():
    while True:
        try:
            for resource_id, dt, name in database.all('SELECT id, dt, name FROM resources'):
                date_time = datetime.datetime.strptime(dt, '%H:%M %d/%m/%Y')
                date_time = pytz.timezone('Europe/Moscow').localize(date_time)
                if database.remember(date_time, datetime.timedelta(days=3)):
                    await states.bot.send_message(
                        chat_id=int(resource_id), text=
                        f'До конца дедлайна 3 дня '
                        f'\U0001F64C'
                        f'\U0001F9D8'
                        f'\U0001F308:\n'
                        f'Время и дата: {dt}\n'
                        f'Название: {name}\n'
                    )
                    await states.print_notes(int(resource_id), database.Resource(resource_id, dt, name))
                if database.remember(date_time, datetime.timedelta(days=1)):
                    await states.bot.send_message(
                        chat_id=int(resource_id), text=
                        f'До конца дедлайна 1 день '
                        f'\U000023F0'
                        f'\U0001F4A3'
                        f'\U0001F494:\n'
                        f'Время и дата: {dt}\n'
                        f'Название: {name}\n'
                    )
                    await states.print_notes(int(resource_id), database.Resource(resource_id, dt, name))
                if database.remember(date_time, datetime.timedelta(hours=1)):
                    await states.bot.send_message(
                        chat_id=int(resource_id), text=
                        f'До конца дедлайна 1 час '
                        f'\U000026B0\U0000FE0F'
                        f'\U00002620\U0000FE0F'
                        f'\U0001F56F\U0000FE0F:\n'
                        f'Время и дата: {dt}\n'
                        f'Название: {name}\n'
                    )
                    await states.print_notes(int(resource_id), database.Resource(resource_id, dt, name))
        except:
            logging.exception("Error in scheduler's working")
        await asyncio.sleep(60)
