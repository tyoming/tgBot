import database
from config import bot_token

from aiogram import Bot, types, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
router = Router()


class CreateEvent(StatesGroup):
    choosing_dt = State()
    choosing_name = State()
    sending_message = State()


class DeleteEvent(StatesGroup):
    waiting_name_to_delete = State()


class ReadEvent(StatesGroup):
    waiting_name_to_read = State()


async def print_notes(chat_id: int, item: database.Resource):
    for note in item.notes:
        if note.type == 'text':
            await bot.copy_message(from_chat_id=note.from_chat_id, chat_id=chat_id, message_id=note.id)
        elif note.type == 'media':
            album_builder = MediaGroupBuilder()
            for file_id, caption in note.media_id_caption:
                album_builder.add_photo(media=file_id, caption=caption)
            await bot.send_media_group(chat_id=chat_id, media=album_builder.build())
        else:
            await bot.send_document(chat_id=chat_id, document=note.id, caption=note.caption)


@router.message(StateFilter(None), F.text, Command('all'))
async def cmd_handler(message: types.Message):
    resources = database.resources_with_id(str(message.chat.id))
    if not resources:
        await message.reply(
            'У вас нет заметок.'
        )
        return
    for item in resources:
        await message.reply(
            f'Время и дата: {item.dt}\n'
            f'Название: {item.name}\n'
        )
        await print_notes(message.chat.id, item)


@router.message(StateFilter(None), F.text, Command('read'))
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        'Введите название заметки, которую вы хотите прочитать.'
    )
    await state.set_state(ReadEvent.waiting_name_to_read)


@router.message(ReadEvent.waiting_name_to_read, F.text)
async def cmd_handler(message: types.Message, state: FSMContext):
    resources = database.resources_with_id(str(message.chat.id))
    if not resources:
        await message.reply(
            'У вас нет заметок.'
        )
        await state.clear()
        return
    resource = database.exist_with_id_name(str(message.chat.id), message.html_text)
    if resource is not None:
        data = database.Resource(str(message.chat.id), resource.dt, message.html_text)
        await message.reply(
            f'Время и дата: {resource.dt}\n'
            f'Название: {message.html_text}'
        )
        await print_notes(message.chat.id, data)
        await state.clear()
        return
    await message.reply(
        'Заметки с таким названием не существует.'
    )
    await state.clear()


@router.message(ReadEvent.waiting_name_to_read)
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        'Название должно быть текстовым сообщением.\n'
    )
    await state.clear()


@router.message(CreateEvent.sending_message, F.text, Command('end'))
async def cmd_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['now'].save()
    await message.reply(
        'Заметка была добавлена.'
    )
    await state.clear()


@router.message(StateFilter(None), F.text, Command('add'))
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        'Введите время и дату заметки, которую вы хотите добавить.\n'
        'Пример: 08:59 01/12/2019'
    )
    await state.set_state(CreateEvent.choosing_dt)


@router.message(CreateEvent.choosing_dt, F.text)
async def cmd_handler(message: types.Message, state: FSMContext):
    flag, dt = database.get_dt(message.html_text)
    if flag:
        await message.reply(
            'Введите название заметки, которую вы хотите добавить.'
        )
        await state.update_data(dt=dt)
        await state.set_state(CreateEvent.choosing_name)
    else:
        await message.reply(
            'Неверный формат ввода.\n'
            'Пример: 08:59 01/12/2019\n'
            'Повторите запрос.'
        )


@router.message(CreateEvent.choosing_dt)
async def cmd_handler(message: types.Message):
    await message.reply(
        'Время и дата заметки должны быть текстовым сообщением.\n'
        'Повторите запрос.'
    )


@router.message(CreateEvent.choosing_name, F.text)
async def cmd_handler(message: types.Message, state: FSMContext):
    if database.exist_with_id_name(str(message.chat.id), message.html_text) is not None:
        await message.reply(
            'Заметка с таким названием уже существует.\n'
            'Повторите запрос.'
        )
        return
    data = await state.get_data()
    now = database.Resource(str(message.chat.id), data['dt'], message.html_text)
    await state.update_data(now=now)
    await message.reply(
        'Введите содержание заметки.\n'
        'После ввода заметки введите /end'
    )
    await state.set_state(CreateEvent.sending_message)


@router.message(CreateEvent.choosing_name)
async def cmd_handler(message: types.Message):
    await message.reply(
        'Название заметки должно быть текстовым сообщением.\n'
        'Повторите запрос.'
    )


@router.message(CreateEvent.sending_message, F.text)
async def cmd_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['now'].notes.append(database.Note(dict(
        type='text',
        id=message.message_id,
        from_chat_id=message.chat.id
    )))
    await state.set_data(data)


@router.message(CreateEvent.sending_message, F.photo)
async def cmd_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.media_group_id is None or not data['now'].notes or data['now'].notes[-1].id != message.media_group_id:
        data['now'].notes.append(database.Note(dict(
            type='media',
            id=message.media_group_id,
            media_id_caption=[]
        )))
    data['now'].notes[-1].media_id_caption.append((message.photo[-1].file_id, message.caption))
    await state.set_data(data)


@router.message(CreateEvent.sending_message, F.document)
async def cmd_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['now'].notes.append(database.Note(dict(
        type='document',
        id=message.document.file_id,
        caption=message.caption
    )))
    await state.set_data(data)


@router.message(CreateEvent.sending_message)
async def cmd_handler(message: types.Message):
    await message.reply(
        'Неверный формат ввода.\n'
        'Для ввода доступны: текст, фото, видео, документы.\n'
        'Повторите запрос.'
    )


@router.message(StateFilter(None), F.text, Command('delete'))
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        'Введите название заметки, которую вы хотите удалить.'
    )
    await state.set_state(DeleteEvent.waiting_name_to_delete)


@router.message(DeleteEvent.waiting_name_to_delete, F.text)
async def cmd_handler(message: types.Message, state: FSMContext):
    resources = database.resources_with_id(str(message.chat.id))
    if not resources:
        await message.reply(
            'У вас нет заметок.'
        )
        await state.clear()
        return
    resource = database.exist_with_id_name(str(message.chat.id), message.html_text)
    if resource is not None:
        data = database.Resource(str(message.chat.id), resource.dt, message.html_text)
        data.delete()
        await message.reply(
            'Заметка была удалена.'
        )
        await state.clear()
        return
    await message.reply(
        'Заметки с таким названием не существует.\n'
    )
    await state.clear()


@router.message(DeleteEvent.waiting_name_to_delete)
async def cmd_handler(message: types.Message, state: FSMContext):
    await message.reply(
        'Название заметки должно быть текстовым сообщением.\n'
    )
    await state.clear()