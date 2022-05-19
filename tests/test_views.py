import json
import os
import time
from typing import List, Optional

import pytest
from fastapi import FastAPI
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.testclient import TestClient

from api import tools
from db.models import UserInfo, UserChat
from db.repositories.models import UserRepository, AgentRepository


class MockUserRepository:
    fake_chat_info = UserInfo(**{"id": 1, "name": "FooBar",
                                 "created_at": "2022-04-01 09:15:12",
                                 "email": "foo@bar.com", "phone": "+123456789", "city": "London",
                                 "lang": "en", "session_id": "f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc",
                                 "is_default": False})

    fake_chat_message = [{"id": 1, "name": "Anna", 'created_at': int(time.time()), 'message': 'Hello Bob',
                          'direction': 'OUT', 'chat_id': 1, 'avatar': ''},
                         {"id": 2, "name": "-", 'created_at': int(time.time()), 'message': 'Hello Anne',
                          'direction': 'IN', 'chat_id': 1, 'avatar': ''}]

    async def _chat_info(self):
        return self.fake_chat_info

    async def _chat_history(self) -> List[UserChat]:
        return [UserChat(**chat_db) for chat_db in self.fake_chat_message]

    async def _create_message(self, name_, message_, avatar: Optional[str] = None):
        pass


class MockAgentRepository:

    async def set_chat_message(self, *, name, message, channel, avatar: Optional[str] = None) -> None:
        pass


class TestChatRequests:

    @pytest.mark.asyncio
    async def test_user_chat_history(self, app, client, monkeypatch):
        async def mock_get_last_chat_history(*args, **kwargs):
            return await MockUserRepository()._chat_history()

        monkeypatch.setattr(UserRepository, 'get_last_chat_history', mock_get_last_chat_history)

        response = await client.get(app.url_path_for("chat-history"),
                                    headers={"x-session-id": "f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc",
                                             "user-agent": "Mozilla/5.0"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_user_form_submit(self, app, client, monkeypatch):
        async def mock_set_chat_info(*args, **kwargs):
            return await MockUserRepository()._chat_info()

        monkeypatch.setattr(UserRepository, 'set_chat_info', mock_set_chat_info)
        user_form = {'name': 'FooBar', 'email': 'foo@bar.com', 'phone': '+123456789898'}
        response = await client.post(app.url_path_for("form-update"), json=user_form,
                                     headers={"x-session-id": "f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc",
                                              "user-agent": "Mozilla/5.0"})

        assert response.status_code == 201

        user_form_no_phone = {'name': 'FooBar', 'email': 'foo@bar.com'}
        response = await client.post(app.url_path_for("form-update"), json=user_form_no_phone,
                                     headers={"x-session-id": "f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc"})

        assert response.status_code == HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_user_publish(self, app, client, monkeypatch):
        os.environ["TESTING"] = "1"

        async def mock_set_chat_message(*args, **kwargs):
            await MockUserRepository()._create_message(name_='Bob', message_='Hello Test')

        monkeypatch.setattr(UserRepository, 'set_chat_message', mock_set_chat_message)
        user_form = {'message': 'Hello Bob'}
        response = await client.post(app.url_path_for("user-publish"), json=user_form,
                                     headers={"x-session-id": "f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc",
                                              "user-agent": "Mozilla/5.0"})

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_chat_websocket(self, app: FastAPI, monkeypatch):
        os.environ["TESTING"] = "1"
        client = TestClient(app)

        async def mock_get_chat_info(*args, **kwargs):
            return await MockUserRepository()._chat_info()

        monkeypatch.setattr(UserRepository, 'check_chat_info', mock_get_chat_info)

        with client.websocket_connect(app.url_path_for("chat-ws", channel='f9eb7ff2-eed0-4c0a-83ba-b0503b59a5cc'),
                                      headers={"user-agent": "Mozilla/5.0"}) as websocket:
            websocket.close()


class TestTools:
    def test_json_fixer(self, glued_json):
        fixed_json_str = tools.json_fixer(glued_json)
        assert len(fixed_json_str) == 2

    def test_json_fixer_dict(self, glued_json):
        fixed_json_str = tools.json_fixer(glued_json)
        for js in fixed_json_str:
            assert isinstance(json.loads(js), dict)

    def test_json_fixer_dict_element(self, glued_json):
        fixed_json_str = tools.json_fixer(glued_json)
        for js in fixed_json_str:
            data = json.loads(js)
            assert data['foo'] in ['bar', 'zulu']

