def test_create_returns_the_stored_client(api):
    response = api.post(
        "/clients",
        json={
            "name": "  Aurora Studio  ",
            "email": "hello@aurora.test",
            "company": "Aurora SAS",
            "address": "12 rue des Lilas\n75011 Paris",
        },
    )
    body = response.get_json()

    assert response.status_code == 201
    assert body["id"]
    assert body["name"] == "Aurora Studio"
    assert body["company"] == "Aurora SAS"
    assert body["address"] == "12 rue des Lilas\n75011 Paris"


def test_name_and_email_are_required(api):
    response = api.post("/clients", json={})
    body = response.get_json()

    assert response.status_code == 400
    assert set(body["errors"]) == {"name", "email"}


def test_email_must_look_like_an_address(api):
    response = api.post(
        "/clients", json={"name": "Aurora", "email": "not-an-email"}
    )

    assert response.status_code == 400
    assert "email" in response.get_json()["errors"]


def test_name_length_is_capped(api):
    response = api.post(
        "/clients", json={"name": "a" * 121, "email": "hello@aurora.test"}
    )

    assert response.get_json()["errors"]["name"].startswith("Maximum")


def test_list_is_sorted_by_name(api, make_client):
    make_client(name="Zephyr")
    make_client(name="Aurora")

    names = [row["name"] for row in api.get("/clients").get_json()]

    assert names == ["Aurora", "Zephyr"]


def test_search_looks_at_name_company_and_email(api, make_client):
    make_client(name="Aurora Studio", email="hello@aurora.test")
    make_client(name="Beta", company="Northwind", email="team@beta.test")
    make_client(name="Gamma", email="billing@corvid.test")

    def found(term):
        rows = api.get(f"/clients?search={term}").get_json()
        return [row["name"] for row in rows]

    assert found("aurora") == ["Aurora Studio"]
    assert found("NORTH") == ["Beta"]
    assert found("corvid") == ["Gamma"]
    assert found("nobody") == []


def test_update_replaces_every_field(api, make_client):
    client = make_client(company="Old company")

    response = api.put(
        f"/clients/{client['id']}",
        json={"name": "Aurora Labs", "email": "new@aurora.test"},
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["name"] == "Aurora Labs"
    assert body["email"] == "new@aurora.test"
    assert body["company"] is None


def test_delete_removes_the_client(api, make_client):
    client = make_client()

    assert api.delete(f"/clients/{client['id']}").status_code == 204
    assert api.get(f"/clients/{client['id']}").status_code == 404


def test_a_client_with_invoices_cannot_be_deleted(api, make_invoice):
    invoice = make_invoice()

    response = api.delete(f"/clients/{invoice['client_id']}")

    assert response.status_code == 409
    assert api.get(f"/clients/{invoice['client_id']}").status_code == 200


def test_unknown_client_answers_in_json(api):
    response = api.get("/clients/999")

    assert response.status_code == 404
    assert response.get_json()["message"] == "This client does not exist."
