import json

from app.config import API_BASE_URL
from app.services.api import ApiClient


class AppState:
    ACCESS_KEY = "vantti.access_token"
    REFRESH_KEY = "vantti.refresh_token"
    USER_KEY = "vantti.user"

    def __init__(self, page):
        self.page = page
        self.api = ApiClient(API_BASE_URL)
        self.access_token = None
        self.refresh_token = None
        self.user = None

    @property
    def storage(self):
        return self.page.session.store

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token)

    def restore_session(self) -> bool:
        access_token = self.storage.get(self.ACCESS_KEY)
        refresh_token = self.storage.get(self.REFRESH_KEY)
        user_raw = self.storage.get(self.USER_KEY)

        if not access_token or not refresh_token or not user_raw:
            self.logout(clear_storage=False)
            return False

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user = json.loads(user_raw)
        self.api.set_tokens(access_token, refresh_token)
        return True

    def login(self, username: str, password: str) -> dict:
        payload = self.api.login(username, password)
        self.access_token = payload.get("access")
        self.refresh_token = payload.get("refresh")
        self.user = payload.get("user") or {}

        self.storage.set(self.ACCESS_KEY, self.access_token)
        self.storage.set(self.REFRESH_KEY, self.refresh_token)
        self.storage.set(self.USER_KEY, json.dumps(self.user))
        return self.user

    def logout(self, clear_storage: bool = True) -> None:
        self.access_token = None
        self.refresh_token = None
        self.user = None
        self.api.clear_tokens()

        if clear_storage:
            for key in (self.ACCESS_KEY, self.REFRESH_KEY, self.USER_KEY):
                try:
                    self.storage.remove(key)
                except Exception:
                    pass
