from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class KeitaroError(Exception):
    def __init__(self, message: str, status_code: int = 502, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def _as_list(data: Any) -> list[dict[str, Any]]:
    if data is None:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "data", "campaigns", "offers", "streams", "domains", "groups"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "id" in data:
            return [data]
    return []


class KeitaroClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.keitaro_base_url).rstrip("/")
        self.api_key = api_key or settings.keitaro_api_key
        if not self.base_url or not self.api_key:
            raise KeitaroError(
                "Keitaro не настроен. Проверьте KEITARO_BASE_URL и KEITARO_API_KEY в .env",
                status_code=503,
            )
        self.api_root = f"{self.base_url}/admin_api/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.api_root}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise KeitaroError(f"Ошибка запроса к Keitaro: {exc}") from exc

        if response.status_code >= 400:
            details: Any
            try:
                details = response.json()
            except ValueError:
                details = response.text
            message = _error_message(details, response.status_code)
            raise KeitaroError(message, status_code=response.status_code, details=details)

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise KeitaroError("Keitaro вернул не JSON") from exc

    def list_domains(self) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/domains"))

    def list_groups(self, group_type: str = "campaigns") -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/groups", params={"type": group_type}))

    def list_traffic_sources(self) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/traffic_sources"))

    def list_offers(self) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/offers"))

    def create_domain(self, name: str) -> dict[str, Any]:
        return _as_entity(self.request("POST", "/domains", json={"name": name.strip()}), "домен")

    def create_group(self, name: str, group_type: str = "campaigns") -> dict[str, Any]:
        return _as_entity(
            self.request("POST", "/groups", json={"name": name.strip(), "type": group_type}),
            "группа",
        )

    def create_traffic_source(self, name: str) -> dict[str, Any]:
        return _as_entity(self.request("POST", "/traffic_sources", json={"name": name.strip()}), "источник")

    def get_offer(self, offer_id: int) -> dict[str, Any]:
        data = self.request("GET", f"/offers/{offer_id}")
        if not isinstance(data, dict):
            raise KeitaroError(f"Оффер {offer_id} не найден", status_code=404)
        return data

    def get_domain(self, domain_id: int) -> dict[str, Any]:
        data = self.request("GET", f"/domains/{domain_id}")
        if not isinstance(data, dict):
            raise KeitaroError(f"Домен {domain_id} не найден", status_code=404)
        return data

    def create_campaign(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self.request("POST", "/campaigns", json=payload)
        if not isinstance(data, dict):
            raise KeitaroError("Keitaro не вернул кампанию")
        return data

    def get_campaign(self, campaign_id: int) -> dict[str, Any]:
        data = self.request("GET", f"/campaigns/{campaign_id}")
        if not isinstance(data, dict):
            raise KeitaroError(f"Кампания {campaign_id} не найдена", status_code=404)
        return data

    def create_stream(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self.request("POST", "/streams", json=payload)
        if not isinstance(data, dict):
            raise KeitaroError("Keitaro не вернул поток")
        return data

    def get_campaign_streams(self, campaign_id: int) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", f"/campaigns/{campaign_id}/streams"))

    def update_stream(self, stream_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = self.request("PUT", f"/streams/{stream_id}", json=payload)
        if isinstance(data, dict):
            return data
        return {"id": stream_id}

    def list_stream_filters(self) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/stream_filters"))

    def list_stream_actions(self) -> list[dict[str, Any]]:
        return _as_list(self.request("GET", "/streams_actions"))


def _as_entity(data: Any, label: str) -> dict[str, Any]:
    if isinstance(data, list) and data:
        data = data[0]
    if isinstance(data, dict) and data.get("id") is not None:
        return data
    raise KeitaroError(f"Keitaro не вернул {label}")


def _error_message(details: Any, status_code: int) -> str:
    if isinstance(details, dict):
        for key in ("error", "message", "detail"):
            value = details.get(key)
            if isinstance(value, str) and value:
                return _localize_keitaro_message(value)
            if isinstance(value, list) and value:
                return str(value[0])
    if isinstance(details, str) and details:
        return _localize_keitaro_message(details)
    return f"Keitaro ответил HTTP {status_code}"


def _localize_keitaro_message(message: str) -> str:
    lowered = message.lower()
    if "no permission" in lowered and "offer" in lowered:
        return (
            "Нет доступа к этому офферу. Ключ API видит только офферы из разрешённых групп. "
            "Выберите оффер из списка."
        )
    if "no permission" in lowered:
        return f"Нет доступа в Keitaro: {message}"
    return message
