from __future__ import annotations

from typing import Any

import requests

from app.config import API_BASE_URL


class ApiError(Exception):
    pass


class AuthenticationError(ApiError):
    pass


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    def set_tokens(self, access_token: str | None, refresh_token: str | None = None) -> None:
        self.access_token = access_token
        if refresh_token is not None:
            self.refresh_token = refresh_token

        if access_token:
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def clear_tokens(self) -> None:
        self.access_token = None
        self.refresh_token = None
        self.session.headers.pop("Authorization", None)

    def login(self, username: str, password: str) -> dict[str, Any]:
        self.clear_tokens()
        payload = self._request(
            "POST",
            "auth/login/",
            json={"username": username, "password": password},
            retry_on_auth=False,
        )
        self.set_tokens(payload.get("access"), payload.get("refresh"))
        return payload

    def refresh_access_token(self) -> str:
        if not self.refresh_token:
            raise AuthenticationError("Tu sesion expiro. Inicia sesion nuevamente.")

        payload = self._request(
            "POST",
            "auth/refresh/",
            json={"refresh": self.refresh_token},
            retry_on_auth=False,
        )
        new_access = payload.get("access")
        if not new_access:
            raise AuthenticationError("No fue posible renovar la sesion.")
        self.set_tokens(new_access, self.refresh_token)
        return new_access

    def get(self, endpoint: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, *, json: dict[str, Any] | None = None) -> Any:
        return self._request("POST", endpoint, json=json)

    def put(self, endpoint: str, *, json: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", endpoint, json=json)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_on_auth: bool = True,
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, json=json, params=params, timeout=15)
        except requests.exceptions.ConnectionError as exc:
            raise ApiError("No se pudo conectar con el backend. Verifica que Django este corriendo.") from exc
        except requests.exceptions.Timeout as exc:
            raise ApiError("La API tardo demasiado en responder.") from exc
        except requests.RequestException as exc:
            raise ApiError(f"Error inesperado de red: {exc}") from exc

        if response.status_code == 401 and retry_on_auth and self.refresh_token:
            self.refresh_access_token()
            response = self.session.request(method, url, json=json, params=params, timeout=15)

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Any:
        if response.status_code == 204:
            return None

        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if 200 <= response.status_code < 300:
            return payload

        message = self._extract_error(payload) or f"Error HTTP {response.status_code}"
        if response.status_code == 401:
            raise AuthenticationError(message)
        raise ApiError(message)

    def _extract_error(self, payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            return payload
        if isinstance(payload, list):
            return "; ".join(str(item) for item in payload)
        if isinstance(payload, dict):
            for key in ("detail", "message", "error", "non_field_errors"):
                value = payload.get(key)
                if value:
                    if isinstance(value, list):
                        return "; ".join(str(item) for item in value)
                    return str(value)
            parts: list[str] = []
            for key, value in payload.items():
                if isinstance(value, list):
                    parts.append(f"{key}: {'; '.join(str(item) for item in value)}")
                else:
                    parts.append(f"{key}: {value}")
            return " | ".join(parts)
        return str(payload)
