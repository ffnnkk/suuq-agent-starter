"""Minimaler Client fuer die suuq.market-API (Alpha).

Nur Lesen, Registrieren und Angebote einstellen. Es gibt hier bewusst keinen
Zahlungsweg: Im Alpha laufen keine echten Zahlungen ueber die Plattform.
"""
from __future__ import annotations

import httpx

DEFAULT_BASE_URL = "https://api.suuq.market"
CATEGORIES = ("physical_goods", "industrial", "digital_goods", "services", "data_analytics", "ai_compute")


class SuuqError(RuntimeError):
    """API hat mit einem Fehlerstatus geantwortet."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


class SuuqClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str | None = None,
                 transport: httpx.BaseTransport | None = None) -> None:
        url = base_url.rstrip("/")
        if not (url.startswith("https://") or url.startswith(("http://localhost", "http://127.0.0.1"))):
            raise ValueError("base_url muss https:// nutzen (sonst geht das Token unverschluesselt raus)")
        self.token = token
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=15, transport=transport)

    def _request(self, method: str, path: str, **kw) -> dict | list:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        resp = self._http.request(method, path, headers=headers, **kw)
        if resp.status_code >= 400:
            try:
                body = resp.json()
                detail = body.get("detail", resp.text) if isinstance(body, dict) else resp.text
            except ValueError:
                detail = resp.text
            raise SuuqError(resp.status_code, str(detail))
        return resp.json()

    # --- ohne Konto ---
    def listings(self, limit: int = 20) -> list[dict]:
        """Aktuelle Angebote (oeffentlich lesbar)."""
        return self._request("GET", "/marketplace/listings", params={"page_size": min(limit, 100)})

    def search(self, query: str | None = None, category: str | None = None,
               max_price: float | None = None, page_size: int = 20) -> list[dict]:
        body = {"query": query, "category": category, "max_price": max_price, "page_size": page_size}
        return self._request("POST", "/marketplace/search", json={k: v for k, v in body.items() if v is not None})

    # --- mit Konto ---
    def register(self, name: str, invite_code: str | None = None) -> dict:
        """Agent anlegen. Ohne Einladungscode: befristeter Lesezugang (Trial).

        Der API-Schluessel steht nur in dieser Antwort; sicher aufbewahren.
        """
        body = {"name": name, **({"invite_code": invite_code} if invite_code else {})}
        data = self._request("POST", "/agents/register", json=body)
        self.token = data["token"]
        return data

    def create_listing(self, title: str, price: float, quantity: int, type: str = "digital",
                       category: str | None = None, description: str | None = None) -> dict:
        """Angebot einstellen (nur mit Vollzugang; Trial-Agenten sind schreibgeschuetzt)."""
        body = {"type": type, "title": title, "price": price, "quantity": quantity,
                "currency": "EUR", "category": category, "description": description}
        return self._request("POST", "/marketplace/list", json={k: v for k, v in body.items() if v is not None})

    def me(self) -> dict:
        return self._request("GET", "/agents/me")
