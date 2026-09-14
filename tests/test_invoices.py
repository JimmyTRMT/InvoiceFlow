import re
from datetime import date

from app.extensions import db
from app.models import Invoice
from app.services.invoices import generate_invoice_number


def test_totals_are_computed_by_the_server(make_invoice):
    invoice = make_invoice(subtotal=1, tax_amount=1, total=1)

    assert invoice["subtotal"] == 1000.0
    assert invoice["tax_amount"] == 200.0
    assert invoice["total"] == 1200.0


# 1.5 x 0.39 is 0.585: half up gives 0.59, banker's rounding 0.58.
def test_line_totals_round_half_up(make_invoice):
    invoice = make_invoice(
        tax_rate=0,
        line_items=[{"description": "Hours", "quantity": 1.5,
                     "unit_price": 0.39}],
    )

    assert invoice["line_items"][0]["line_total"] == 0.59
    assert invoice["total"] == 0.59


def test_tax_rounds_half_up(make_invoice):
    invoice = make_invoice(
        tax_rate=10,
        line_items=[{"description": "Stamp", "quantity": 1,
                     "unit_price": 0.05}],
    )

    assert invoice["tax_amount"] == 0.01
    assert invoice["total"] == 0.06


def test_numbers_follow_each_other_within_a_year(make_client, make_invoice):
    client_id = make_client()["id"]
    first = make_invoice(client_id)
    second = make_invoice(client_id)
    year = date.today().year

    assert first["number"] == f"INV-{year}-001"
    assert second["number"] == f"INV-{year}-002"


def test_numbering_restarts_with_the_issue_year(make_client, make_invoice):
    client_id = make_client()["id"]
    make_invoice(client_id)

    older = make_invoice(
        client_id, issue_date="2019-03-01", due_date="2019-04-01"
    )

    assert older["number"] == "INV-2019-001"


# A text MAX would rank 999 above 1000 and hand out a duplicate.
def test_numbering_compares_sequences_as_numbers(app, make_client):
    client_id = make_client()["id"]
    for number in ("INV-2031-999", "INV-2031-1000"):
        db.session.add(Invoice(
            number=number,
            client_id=client_id,
            issue_date=date(2031, 1, 1),
            due_date=date(2031, 2, 1),
        ))
    db.session.commit()

    assert generate_invoice_number(date(2031, 6, 1)) == "INV-2031-1001"


def test_due_date_cannot_precede_the_issue_date(
    api, make_client, invoice_data
):
    payload = invoice_data(
        make_client()["id"], issue_date="2026-05-10", due_date="2026-05-01"
    )

    response = api.post("/invoices", json=payload)

    assert response.status_code == 400
    assert "due_date" in response.get_json()["errors"]


def test_an_invoice_needs_at_least_one_line(api, make_client, invoice_data):
    payload = invoice_data(make_client()["id"], line_items=[])

    response = api.post("/invoices", json=payload)

    assert response.get_json()["errors"]["line_items"]


# The form relies on this shape to point at the exact row that failed.
def test_line_errors_are_indexed_by_row(api, make_client, invoice_data):
    payload = invoice_data(make_client()["id"], line_items=[
        {"description": "Fine", "quantity": 1, "unit_price": 10},
        {"description": "Broken", "quantity": 0, "unit_price": 10},
    ])

    errors = api.post("/invoices", json=payload).get_json()["errors"]

    assert list(errors) == ["line_items[1].quantity"]


def test_unknown_client_is_a_validation_error(api, invoice_data):
    response = api.post("/invoices", json=invoice_data(999))

    assert response.status_code == 400
    assert "client_id" in response.get_json()["errors"]


def test_overdue_cannot_be_stored_as_a_status(
    api, make_client, invoice_data
):
    payload = invoice_data(make_client()["id"], status="overdue")

    response = api.post("/invoices", json=payload)

    assert "status" in response.get_json()["errors"]


def test_update_keeps_the_number_and_replaces_the_lines(
    api, make_invoice, invoice_data
):
    invoice = make_invoice()
    payload = invoice_data(
        invoice["client_id"],
        issue_date="2020-01-15",
        due_date="2020-02-15",
        tax_rate=10,
        notes="Updated terms",
        line_items=[
            {"description": "Design sprint", "quantity": 2,
             "unit_price": 500},
            {"description": "Extra day", "quantity": 1, "unit_price": 400},
        ],
    )

    body = api.put(f"/invoices/{invoice['id']}", json=payload).get_json()

    assert body["number"] == invoice["number"]
    assert [line["description"] for line in body["line_items"]] == [
        "Design sprint", "Extra day",
    ]
    assert body["subtotal"] == 1400.0
    assert body["tax_amount"] == 140.0
    assert body["total"] == 1540.0
    assert body["notes"] == "Updated terms"


def test_mark_paid_records_the_date_once(api, make_invoice):
    invoice = make_invoice(status="sent")

    first = api.post(f"/invoices/{invoice['id']}/mark-paid").get_json()
    second = api.post(f"/invoices/{invoice['id']}/mark-paid").get_json()

    assert first["status"] == "paid"
    assert first["paid_at"] is not None
    assert second["paid_at"] == first["paid_at"]


def test_leaving_paid_clears_the_payment_date(
    api, make_invoice, invoice_data
):
    invoice = make_invoice(status="paid")
    assert invoice["paid_at"] is not None

    payload = invoice_data(invoice["client_id"], status="sent")
    body = api.put(f"/invoices/{invoice['id']}", json=payload).get_json()

    assert body["status"] == "sent"
    assert body["paid_at"] is None


def test_delete_removes_the_invoice_and_its_lines(api, make_invoice):
    invoice = make_invoice()

    assert api.delete(f"/invoices/{invoice['id']}").status_code == 204
    assert api.get(f"/invoices/{invoice['id']}").status_code == 404


def test_list_is_newest_first_and_light(api, make_client, make_invoice):
    client_id = make_client()["id"]
    older = make_invoice(client_id, issue_date="2025-01-01",
                         due_date="2025-02-01")
    newer = make_invoice(client_id)

    rows = api.get("/invoices").get_json()

    assert [row["id"] for row in rows] == [newer["id"], older["id"]]
    assert "line_items" not in rows[0]
    assert rows[0]["client"]["name"] == "Aurora Studio"


def test_list_filters_by_status_and_client(api, make_client, make_invoice):
    aurora = make_client()["id"]
    beta = make_client(name="Beta")["id"]
    make_invoice(aurora, status="draft")
    make_invoice(aurora, status="sent")
    make_invoice(beta, status="sent")

    def count(query):
        return len(api.get(f"/invoices?{query}").get_json())

    assert count("status=sent") == 2
    assert count(f"client_id={beta}") == 1
    assert count(f"status=sent&client_id={aurora}") == 1
    assert count("status=paid") == 0
    assert count("client_id=abc") == 3


def test_list_limit_is_applied(api, make_client, make_invoice):
    client_id = make_client()["id"]
    for _ in range(3):
        make_invoice(client_id)

    assert len(api.get("/invoices?limit=2").get_json()) == 2
    assert len(api.get("/invoices?limit=0").get_json()) == 3


def test_number_format(make_invoice):
    assert re.fullmatch(r"INV-\d{4}-\d{3,}", make_invoice()["number"])
