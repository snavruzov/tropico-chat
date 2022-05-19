import asyncio
import json
import math
import time
from typing import Optional, List

import requests
from loguru import logger

from api.tools import get_ip_info
from core.config import MEDIA_URL
from db.models import UserChat, UserInfo, WelcomeChat, IntroChat, OperatorTG
from db.repositories.base import BaseRepository, BaseDatabase

GET_USER_CHAT_ID = """
    SELECT id, name, created_at, email, phone, city, lang, session_id, context, is_default
    FROM tropico_chat WHERE session_id = :session_id LIMIT 1;
"""

GET_USER_LAST_CHATS_QUERY = """
    SELECT id, name, created_at, message, direction, chat_id, avatar
    FROM tropico_messages WHERE chat_id = :chat_id AND status='APPROVED' AND created_at >= :timedelta 
    ORDER BY id DESC LIMIT 15;
"""

GET_USER_LAST_CHATS_EXISTS = """
    SELECT id
    FROM tropico_messages WHERE chat_id = :chat_id AND status='APPROVED' AND created_at >= :timedelta LIMIT 1;
"""

GET_CHAT_INTRO_QUERY = """
    SELECT id, message, quick_replies, lang
    FROM tropico_intro WHERE lang=:lang LIMIT 1;
"""

GET_AGENT_LAST_CHAT_QUERY = """
    SELECT id, name, created_at, message, direction, chat_id, avatar
    FROM tropico_messages WHERE chat_id = :chat_id AND status='APPROVED' AND direction='OUT' ORDER BY id DESC LIMIT 1;
"""

GET_WELCOME_CHAT_QUERY = """
    SELECT id, name, created_at, message, lang
    FROM tropico_welcomes WHERE lang = :lang LIMIT 1;
"""

CREATE_USER_CHAT = """
    INSERT INTO tropico_chat (name, city, lang, session_id, email, phone, context, is_default, ip, country)
    VALUES (:name, :city, :lang, :session_id, :email, :phone, :context, :is_default, :ip, :country) 
    ON CONFLICT (session_id) DO 
    UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    phone=EXCLUDED.phone,
    is_default=EXCLUDED.is_default 
    RETURNING id, name, created_at, email, phone, city, lang, session_id, context, is_default;
"""

UPDATE_USER_UTM = """
    UPDATE tropico_chat SET context=:context WHERE session_id=:session_id;
"""

CREATE_CHAT_MESSAGE = """
    INSERT INTO tropico_messages (name, message, chat_id, created_at, avatar)
    VALUES (:name, :message, :chat_id, :created_at, :avatar)
    RETURNING id, name, created_at, message, direction, chat_id, avatar;
"""

CREATE_CHAT_OUT_MESSAGE = """
    INSERT INTO tropico_messages (name, message, chat_id, direction, created_at, avatar)
    VALUES (:name, :message, :chat_id, :direction, :created_at, :avatar)
    RETURNING id, name, created_at, message, direction, chat_id, avatar;
"""

CREATE_OPERATOR_TG = """
    INSERT INTO tropico_operators (name, chat_id)
    VALUES (:name, :chat_id)
    RETURNING id, name, chat_id;
"""

LIST_OPERATOR_TG = """
    SELECT id, name, chat_id FROM tropico_operators WHERE status=0;
"""


class CouchRepository(BaseRepository):

    def __init__(self, db: BaseDatabase) -> None:
        super().__init__(db)


class TaskRepository(BaseRepository):

    def __init__(self, db: BaseDatabase) -> None:
        super().__init__(db)

    async def launch_task(self, *, request, task):
        pass


class UserRepository(object):

    def __init__(self, dbs: BaseDatabase, session_id: str, lang: Optional[str] = 'en',
                 x_forwarded_for: Optional[str] = None, query_params: str = None) -> None:
        self.dbs = dbs
        self.db = dbs.db
        self.redis = dbs.redis
        self.query_params = query_params

        if lang and len(lang.split(',')) > 1:
            lang = lang[:2]
            if lang not in ['en', 'ru']:
                lang = 'en' \
                       ''
        self.lang_ = lang
        self.session_id_ = session_id
        if x_forwarded_for:
            ip = list(map(str.strip, filter(lambda x: len(x) > 5, x_forwarded_for.split(','))))
            if ip and len(ip) > 0:
                self.ip_ = ip[0]
        else:
            self.ip_ = '82.215.106.137'

    async def __chat_info(self) -> UserInfo:
        chat_db = await self.db.fetch_one(query=GET_USER_CHAT_ID, values={"session_id": self.session_id_})

        if chat_db:
            if self.query_params and not chat_db['context']:
                qp = str(self.query_params)
                context_ = '{"utm": "' + qp + '"}'
                await self.db.fetch_one(query=UPDATE_USER_UTM, values={"session_id": self.session_id_,
                                                                       "context": context_})
            return UserInfo(**chat_db)

    async def __check_info(self) -> UserInfo:
        chat_db = await self.db.fetch_one(query=GET_USER_CHAT_ID, values={"session_id": self.session_id_})

        if chat_db:
            return UserInfo(**chat_db)

    async def __create_info(self, email_: Optional[str], phone_: Optional[str], name: str = None) -> UserInfo:
        ip_info = get_ip_info(self.ip_)
        city = 'nowhere'
        country = 'nowhere'
        if ip_info:
            city = ip_info.get('city')
            country = ip_info.get('country')

        is_default = False
        if not name:
            is_default = True
            name = f"{city}-{math.ceil(time.time())}"

        logger.debug(f"Name: {name}")
        if self.query_params:
            qp = str(self.query_params)
            context_ = '{"utm": "' + qp + '"}'
        else:
            context_ = None
        chat_db = await self.db.fetch_one(query=CREATE_USER_CHAT,
                                          values={"name": name, "city": city,
                                                  "lang": self.lang_,
                                                  "session_id": self.session_id_,
                                                  "email": email_,
                                                  "phone": phone_,
                                                  "context": context_,
                                                  "ip": self.ip_,
                                                  "country": country,
                                                  "is_default": is_default})

        return UserInfo(**chat_db)

    async def __get_chat_id(self) -> UserInfo:
        ch_info = await self.__chat_info()
        if not ch_info:
            ch_info = await self.__create_info(None, None)

        return ch_info

    async def __chat_history(self):
        ch_info = await self.__get_chat_id()
        chat_record = await self.db.fetch_all(query=GET_USER_LAST_CHATS_QUERY,
                                              values={"chat_id": ch_info.id, "timedelta": int(time.time())-86400})

        if not chat_record or len(chat_record) == 0:
            welcome_chat = await self.__get_chat_welcome()
            chat_record = [{"id": 1,
                            "name": welcome_chat.name,
                            "chat_id": 0,
                            "direction": "OUT",
                            "message": welcome_chat.message,
                            "avatar": f"{MEDIA_URL}agent/anna.jpg",
                            "created_at": int(time.time())}]

        return [UserChat(**chat_db) for chat_db in chat_record]

    async def __chat_intro(self, chat_info: UserInfo) -> IntroChat:
        chat_intro = await self.db.fetch_one(query=GET_CHAT_INTRO_QUERY, values={"lang": self.lang_})
        chat_record = await self.db.fetch_one(query=GET_USER_LAST_CHATS_EXISTS,
                                              values={"chat_id": chat_info.id, "timedelta": int(time.time()) - 86400})
        if chat_record:
            last_agent_db = await self.db.fetch_one(query=GET_AGENT_LAST_CHAT_QUERY,
                                                    values={"chat_id": chat_info.id})
        else:
            last_agent_db = None

        if last_agent_db:
            last_agent = UserChat(**last_agent_db)
        else:
            last_agent = UserChat(**{"id": 1,
                                     "name": "Anna",
                                     "chat_id": 0,
                                     "message": "",
                                     "avatar": f"{MEDIA_URL}agent/anna.jpg",
                                     "created_at": int(time.time())})

        quick_reps = json.loads(chat_intro['quick_replies'])
        intro_ch = IntroChat(**{"message": chat_intro['message'],
                                "quick_replies": quick_reps,
                                "lang": chat_intro['lang'],
                                "name": last_agent.name,
                                "avatar": last_agent.avatar})
        return intro_ch

    async def __get_chat_welcome(self) -> WelcomeChat:
        chat_record = await self.db.fetch_one(query=GET_WELCOME_CHAT_QUERY, values={"lang": self.lang_})
        return WelcomeChat(**chat_record)

    async def __create_message(self, name_, message_, chat_info: UserInfo, avatar: Optional[str] = None):
        created_at = int(time.time())
        await self.redis.publish(self.session_id_, json.dumps({"channel_id": self.session_id_,
                                                               "name": name_, "message": message_,
                                                               "direction": "IN", "avatar": None,
                                                               "created_at": created_at}))
        await self.db.fetch_one(query=CREATE_CHAT_MESSAGE,
                                values={"name": name_, "chat_id": chat_info.id,
                                        "message": message_, "created_at": created_at,
                                        "avatar": avatar})

    async def __pass_chat_info(self, chat_info: UserInfo) -> None:
        created_at = int(time.time())
        is_default = chat_info.is_default
        chat_intro = await self.__chat_intro(chat_info)
        await asyncio.sleep(1)
        await self.redis.publish(self.session_id_, json.dumps({"channel_id": self.session_id_,
                                                               "name": "-", "message": '',
                                                               "direction": "SYS",
                                                               "is_default": is_default,
                                                               "intro": chat_intro.dict(),
                                                               "created_at": created_at}))

    async def initial_pass_chat_info(self, ch_info):
        await self.__pass_chat_info(chat_info=ch_info)

    async def get_last_chat_history(self) -> List[UserChat]:
        return await self.__chat_history()

    async def get_chat_info(self) -> UserInfo:
        return await self.__chat_info()

    async def check_chat_info(self) -> UserInfo:
        return await self.__check_info()

    async def set_chat_info(self, *, email: str, phone: str, name: str) -> UserInfo:
        data_to_send = {"channel_id": self.session_id_, "name": name, "phone": phone, "email": email}
        requests.post("http://bitrix_chat:8000/bitrix/deal", json=data_to_send)

        return await self.__create_info(email, phone, name=name)

    async def set_chat_message(self, *, message: str) -> None:
        chat_info = await self.__get_chat_id()
        await self.__create_message(name_='-', message_=message, chat_info=chat_info)

        utm_ctx = chat_info.context
        if utm_ctx:
            utm_ctx = json.loads(utm_ctx)
            utm_ctx = utm_ctx.get('utm')
        else:
            utm_ctx = ''

        data_to_send = {"channel_id": self.session_id_, "lang": self.lang_, "message": message, "url": utm_ctx}
        requests.post("http://bitrix_chat:8000/bitrix/publish", json=data_to_send)

    async def set_wp_chat_message(self, *, message: str, name: str, phone: str) -> None:
        chat_info = await self.__get_chat_id()
        await self.__create_message(name_='-', message_=message, chat_info=chat_info)
        if chat_info.is_default:
            await self.__create_info('', phone_=phone, name=name)


class AgentRepository(BaseRepository):

    def __init__(self, db: BaseDatabase) -> None:
        super().__init__(db)

    async def _chat_info(self, session_id) -> UserInfo:
        chat_db = await self.db.fetch_one(query=GET_USER_CHAT_ID, values={"session_id": session_id})

        if chat_db:
            return UserInfo(**chat_db)

    async def set_chat_message(self, *, name, message, channel, avatar: Optional[str] = None) -> None:
        ch_info = await self._chat_info(session_id=channel)

        if ch_info:
            chat_db = await self.db.fetch_one(query=CREATE_CHAT_OUT_MESSAGE,
                                              values={"name": name,
                                                      "chat_id": ch_info.id,
                                                      "message": message,
                                                      "avatar": avatar,
                                                      "created_at": int(time.time()),
                                                      "direction": 'OUT'})
            chm = UserChat(**chat_db)
            await self.redis.publish(channel, json.dumps({"channel_id": channel,
                                                          "name": name, "message": message,
                                                          "direction": 'OUT',
                                                          "avatar": avatar,
                                                          "created_at": chm.created_at}))


class OperatorsRepository(BaseRepository):

    def __init__(self, db: BaseDatabase) -> None:
        super().__init__(db)

    async def set_operator_tg_info(self, *, name, user_id) -> None:
        await self.db.fetch_one(query=CREATE_OPERATOR_TG, values={"name": name, "chat_id": user_id})

    async def get_operator_tgs(self) -> List[OperatorTG]:
        chat_operators = await self.db.fetch_all(query=LIST_OPERATOR_TG)
        return [OperatorTG(**chat_db) for chat_db in chat_operators]
