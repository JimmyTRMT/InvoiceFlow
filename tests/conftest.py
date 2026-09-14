from datetime import date, timedelta

import pytest

from app import create_app
from app.extensions import db

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"


# Talks to /api and repeats the CSRF token on every write, like api.js.
class ApiClient:
    def __init__(self, client, token):
        self._client = client
        self._headers = {CSRF_HEADER: token}

    def get(self, path):
        return self._client.get(f"/api{path}")

    def post(self, path, json=None):
        return self._client.post(
            f"/api{path}", json=json, headers=self._headers
        )

    def put(self, path, json):
        return self._client.put(
            f"/api{path}", json=json, headers=self._headers
        )

    def delete(self, path):
        return self._client.delete(f"/api{path}", headers=self._headers)


def days_from_today(days):
    return (date.today() + timedelta(days=days)).isoformat()


# Each test gets its own in-memory database, so no test sees another's rows.
@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# Any page hands out the token cookie, exactly as the browser receives it.
@pytest.fixture
def api(client):
    client.get("/")
    return ApiClient(client, client.get_cookie(CSRF_COOKIE).value)


@pytest.fixture
def invoice_data():
    def build(client_id, **overrides):
        payload = {
            "client_id": client_id,
            "issue_date": days_from_today(0),
            "due_date": days_from_today(30),
            "status": "draft",
            "tax_rate": 20,
            "line_items": [
                {"description": "Design sprint", "quantity": 2,
                 "unit_price": 500},
            ],
        }
        payload.update(overrides)
        return payload

    return build


@pytest.fixture
def make_client(api):
    def make(**overrides):
        payload = {"name": "Aurora Studio", "email": "hello@aurora.test"}
        payload.update(overrides)
        response = api.post("/clients", json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return make


@pytest.fixture
def make_invoice(api, make_client, invoice_data):
    def make(client_id=None, **overrides):
        if client_id is None:
            client_id = make_client()["id"]
        payload = invoice_data(client_id, **overrides)
        response = api.post("/invoices", json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return make
