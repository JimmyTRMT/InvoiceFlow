from conftest import days_from_today

LATE = {"issue_date": days_from_today(-40), "due_date": days_from_today(-10)}


def test_a_sent_invoice_past_its_due_date_is_overdue(make_invoice):
    invoice = make_invoice(status="sent", **LATE)

    assert invoice["is_overdue"] is True
    assert invoice["effective_status"] == "overdue"
    assert invoice["status"] == "sent"


def test_a_late_draft_is_not_overdue(make_invoice):
    invoice = make_invoice(status="draft", **LATE)

    assert invoice["is_overdue"] is False
    assert invoice["effective_status"] == "draft"


def test_a_late_paid_invoice_is_not_overdue(make_invoice):
    invoice = make_invoice(status="paid", **LATE)

    assert invoice["effective_status"] == "paid"


def test_an_invoice_due_today_is_not_late_yet(make_invoice):
    invoice = make_invoice(
        status="sent",
        issue_date=days_from_today(-30),
        due_date=days_from_today(0),
    )

    assert invoice["is_overdue"] is False


def test_the_overdue_filter_matches_the_rule(api, make_client, make_invoice):
    client_id = make_client()["id"]
    late_sent = make_invoice(client_id, status="sent", **LATE)
    make_invoice(client_id, status="draft", **LATE)
    make_invoice(client_id, status="paid", **LATE)
    make_invoice(client_id, status="sent")

    rows = api.get("/invoices?status=overdue").get_json()

    assert [row["id"] for row in rows] == [late_sent["id"]]


def test_dashboard_on_an_empty_database(api):
    stats = api.get("/dashboard/stats").get_json()

    assert stats["outstanding_total"] == 0
    assert stats["paid_this_month"] == 0
    assert stats["overdue_count"] == 0


# Every figure agrees with the list filters, drafts included in none.
def test_dashboard_figures(api, make_client, make_invoice):
    client_id = make_client()["id"]
    make_invoice(client_id, status="sent", **LATE)
    make_invoice(client_id, status="sent")
    make_invoice(client_id, status="draft", **LATE)
    paid = make_invoice(client_id, status="sent", tax_rate=0)
    api.post(f"/invoices/{paid['id']}/mark-paid")

    stats = api.get("/dashboard/stats").get_json()
    overdue_rows = api.get("/invoices?status=overdue").get_json()

    assert stats["outstanding_total"] == 2400.0
    assert stats["paid_this_month"] == 1000.0
    assert stats["overdue_count"] == len(overdue_rows) == 1
