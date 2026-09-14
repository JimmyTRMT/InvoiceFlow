import re

import pytest

INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>")
STYLE_ATTRIBUTE = re.compile(r"\sstyle=")
RAW_COLOUR = re.compile(r"\b(?:bg|text|border)-(?:slate|rose|amber)-\d")


@pytest.fixture
def invoice_id(make_invoice):
    return make_invoice()["id"]


@pytest.fixture
def pages(invoice_id):
    return [
        "/",
        "/clients",
        "/invoices",
        "/invoices/new",
        f"/invoices/{invoice_id}",
        f"/invoices/{invoice_id}/edit",
    ]


def test_every_page_renders(client, pages):
    for path in pages:
        assert client.get(path).status_code == 200, path


# Scripts come from files and colours from tokens, never from the markup.
def test_pages_keep_behaviour_and_colour_out_of_the_markup(client, pages):
    for path in pages:
        html = client.get(path).get_data(as_text=True)

        assert not INLINE_SCRIPT.search(html), path
        assert not STYLE_ATTRIBUTE.search(html), path
        assert not RAW_COLOUR.search(html), path


def test_the_edit_page_is_the_form_in_edit_mode(client, invoice_id):
    html = client.get(f"/invoices/{invoice_id}/edit").get_data(as_text=True)

    assert f'data-invoice-id="{invoice_id}"' in html
    assert "Save changes" in html
    assert "Create invoice" not in html


def test_the_new_page_is_the_form_in_create_mode(client):
    html = client.get("/invoices/new").get_data(as_text=True)

    assert 'data-invoice-id=""' in html
    assert "Create invoice" in html


def test_unknown_invoice_pages_render_the_error_page(client):
    for path in ("/invoices/999", "/invoices/999/edit", "/nowhere"):
        response = client.get(path)

        assert response.status_code == 404, path
        assert response.mimetype == "text/html", path


def test_unknown_api_paths_answer_in_json(client):
    response = client.get("/api/nowhere")

    assert response.status_code == 404
    assert response.is_json


def test_health_check(client):
    assert client.get("/api/health").status_code == 200
