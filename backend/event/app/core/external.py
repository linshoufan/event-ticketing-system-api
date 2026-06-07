import httpx

from .config import settings


class TicketServiceError(Exception):
    pass


class TicketClient:
    def __init__(self, base_url: str | None = None, internal_key: str | None = None, timeout: float = 5.0):
        self._client = httpx.Client(
            base_url=base_url or settings.ticket_service_url,
            timeout=timeout,
            headers={"X-Internal-Key": internal_key or settings.internal_api_key},
        )

    def close(self) -> None:
        self._client.close()

    def delete_event_tickets(self, event_id: str) -> int:
        try:
            response = self._client.delete(f"/v1/internal/tickets/events/{event_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TicketServiceError(
                f"TicketService returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise TicketServiceError(f"TicketService network error: {exc}") from exc

        return int(response.json().get("data", {}).get("deletedCount", 0))


def get_ticket_client():
    client = TicketClient()
    try:
        yield client
    finally:
        client.close()

class TransactionServiceError(Exception):
    pass

class TransactionClient:
    def __init__(self, base_url: str | None = None, internal_key: str | None = None, timeout: float = 5.0):
        self._client = httpx.Client(
            base_url=base_url or settings.transaction_service_url,
            timeout=timeout,
            headers={"X-Internal-Key": internal_key or settings.internal_api_key},
        )
    def close(self) -> None:
        self._client.close()
    def delete_event_registrations(self, event_id: str) -> int:
        try:
            response = self._client.delete(f"/v1/internal/events/{event_id}/registrations")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TransactionServiceError(f"TransactionService HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise TransactionServiceError(f"TransactionService network error: {exc}") from exc
        return int(response.json().get("data", {}).get("deletedCount", 0))

def get_transaction_client():
    client = TransactionClient()
    try:
        yield client
    finally:
        client.close()