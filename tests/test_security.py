from conftest import CSRF_COOKIE, CSRF_HEADER

CLIENT = {"name": "Aurora Studio", "email": "hello@aurora.test"}


def test_write_without_token_is_refused(client):
    client.get("/")
    response = client.post("/api/clients", json=CLIENT)

    assert response.status_code == 403
    assert "CSRF" in response.get_json()["message"]


def test_write_with_a_forged_token_is_refused(client):
    client.get("/")
    response = client.post(
        "/api/clients", json=CLIENT, headers={CSRF_HEADER: "forged"}
    )

    assert response.status_code == 403


def test_header_alone_is_not_enough_without_the_cookie(app):
    fresh = app.test_client()
    response = fresh.post(
        "/api/clients", json=CLIENT, headers={CSRF_HEADER: "anything"}
    )

    assert response.status_code == 403


def test_reads_need_no_token(app):
    response = app.test_client().get("/api/clients")

    assert response.status_code == 200


def test_matching_token_lets_the_write_through(api):
    assert api.post("/clients", json=CLIENT).status_code == 201


# The script has to read the cookie back, so HttpOnly would break it.
def test_token_cookie_is_readable_and_strict(client):
    response = client.get("/")
    cookie = next(
        header for header in response.headers.getlist("Set-Cookie")
        if header.startswith(f"{CSRF_COOKIE}=")
    )

    assert "SameSite=Strict" in cookie
    assert "HttpOnly" not in cookie


def test_token_is_not_reissued_once_present(client):
    client.get("/")
    second = client.get("/")

    assert not any(
        header.startswith(f"{CSRF_COOKIE}=")
        for header in second.headers.getlist("Set-Cookie")
    )


def test_control_characters_are_stripped(api):
    response = api.post(
        "/clients",
        json={"name": "Aurora\x00 Studio\x1b", "email": "hello@aurora.test"},
    )

    assert response.get_json()["name"] == "Aurora Studio"


def test_markup_is_stored_as_plain_text(api):
    name = "<script>alert(1)</script>"
    api.post("/clients", json={"name": name, "email": "x@y.test"})

    assert api.get("/clients").get_json()[0]["name"] == name


def test_a_body_that_is_not_an_object_is_rejected(api):
    response = api.post("/clients", json=["not", "an", "object"])

    assert response.status_code == 400
