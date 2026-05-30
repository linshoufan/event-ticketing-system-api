import httpx
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from app.core.config import settings

@dataclass
class EventInfo:
    event_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    checkin_radius_meters: int
    event_start_time: datetime
    event_end_time: datetime

class ExternalServiceError(Exception):
    def __init__(self, service: str, message: str, status_code: int | None = None):
        self.service = service
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")

def _parse_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

class EventClient:
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self._client = httpx.Client(
            base_url=base_url or settings.event_service_url,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def get_event(self, event_id: str) -> EventInfo:
        try:
            response = self._client.get(f"/v1/events/{event_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            message = exc.response.text
            raise ExternalServiceError("EventService", message, status_code=status) from exc
        except httpx.RequestError as exc:
            raise ExternalServiceError("EventService", f"network error: {exc}") from exc

        data = response.json().get("data", {})
        return EventInfo(
            event_id=data["eventId"],
            name=data["name"],
            location=data["location"],
            latitude=float(data["latitude"]) if data.get("latitude") is not None else 0.0,
            longitude=float(data["longitude"]) if data.get("longitude") is not None else 0.0,
            checkin_radius_meters=int(float(data["checkinRadiusMeters"])) if data.get("checkinRadiusMeters") is not None else 0,
            event_start_time=_parse_iso(data["eventStartTime"]),
            event_end_time=_parse_iso(data["eventEndTime"]),
        )

_event_client: Optional[EventClient] = None

def get_event_client() -> EventClient:
    global _event_client
    if _event_client is None:
        _event_client = EventClient()
    return _event_client
