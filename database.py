import logging
import pytz
import datetime
import json
from mysql.connector import connect
from config import database_data


def run(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            connection.commit()


def one(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            res = cursor.fetchone()
            return res


def all(*args):
    with connect(**database_data) as connection:
        with connection.cursor() as cursor:
            cursor.execute(*args)
            res = cursor.fetchall()
            return res


class Note:
    def __init__(self, data: dict):
        self.type = data['type']
        self.id = data['id']
        if self.type == 'text':
            self.from_chat_id = data['from_chat_id']
        elif self.type == 'media':
            self.media_id_caption = data['media_id_caption']
        elif self.type == 'document':
            self.caption = data['caption']
        else:
            logging.exception('Wrong Message.type')

    def to_dict(self):
        if self.type == 'text':
            data = dict(
                type=self.type,
                id=self.id,
                from_chat_id=self.from_chat_id,
            )
        elif self.type == 'media':
            data = dict(
                type=self.type,
                id=self.id,
                media_id_caption=self.media_id_caption
            )
        else:
            data = dict(
                type=self.type,
                id=self.id,
                caption=self.caption
            )
        return data


def get_dt(message: str):
    try:
        time, date = message.split(' ', maxsplit=1)
        dt = datetime.datetime.strptime(time + ' ' + date, '%H:%M %d/%m/%Y')
        dt = pytz.timezone('Europe/Moscow').localize(dt)
        dt = dt.strftime('%H:%M %d/%m/%Y')
        return True, dt
    except ValueError:
        return False, None


def remember(dt: datetime.datetime, delta: datetime.timedelta):
    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    return abs(dt - now - delta) <= datetime.timedelta(seconds=30)


class Resource:
    def __init__(self, resource_id: str, dt: str, name: str):
        self.resource_id = resource_id
        self.dt = dt
        self.name = name
        data = one("SELECT data FROM resources WHERE id = %s AND dt = %s AND name = %s",
                   (resource_id, dt, name))
        if data is not None:
            data = json.loads(data[0])
        else:
            run("INSERT INTO resources (id, dt, name, data) VALUES (%s, %s, %s, %s)",
                (resource_id, dt, name, '{}'))
            data = dict(notes=[])

        self.notes = [Note(i) for i in data['notes']]

    def save(self):
        data = dict(
            resource_id=self.resource_id,
            dt=self.dt,
            name=self.name,
            notes=[item.to_dict() for item in self.notes]
        )
        run("UPDATE resources SET data = %s WHERE id = %s AND dt = %s AND name = %s",
            (json.dumps(data), self.resource_id, self.dt, self.name))

    def delete(self):
        run("DELETE FROM resources WHERE id = %s and dt = %s AND name = %s",
            (self.resource_id, self.dt, self.name))


def resources_with_id(resource_id: str):
    resources = []
    for dt, name in all("SELECT dt, name FROM resources WHERE id = %s",
                        (resource_id,)):
        resources.append(Resource(resource_id, dt, name))
    return resources


def exist_with_id_name(resource_id: str, name: str):
    dt = one("SELECT dt FROM resources WHERE id = %s AND name = %s",
             (resource_id, name))
    if dt is None:
        return None
    return Resource(resource_id, dt[0], name)