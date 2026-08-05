# InvoiceFlow

A small web application for freelancers to create, track and export
invoices. It keeps a list of clients, builds invoices with several line
items, computes the totals, and shows what is outstanding, paid or
overdue.

This repository is a work in progress. The backend skeleton, the
database models and the clients API are in place; the features are added
step by step.

## Prerequisites

- Python 3.10 or newer
- git

## Setup

Run these commands from the project folder.

Create a virtual environment:

```
python -m venv .venv
```

Activate it on Windows (PowerShell):

```
.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```
source .venv/bin/activate
```

Install the dependencies:

```
pip install -r requirements.txt
```

Create your local configuration file from the example:

```
copy .env.example .env
```

On macOS or Linux use this instead:

```
cp .env.example .env
```

Create the database file and its tables:

```
flask --app run.py init-db
```

## Running the app

```
python run.py
```

The server starts on http://127.0.0.1:5000 and the health check is
available at http://127.0.0.1:5000/api/health

## The API so far

| Method | Path                | What it does                        |
| ------ | ------------------- | ----------------------------------- |
| GET    | /api/health         | Confirm the API is running          |
| GET    | /api/clients        | List clients, `?search=` to filter  |
| POST   | /api/clients        | Create a client                     |
| GET    | /api/clients/`<id>` | Read one client                     |
| PUT    | /api/clients/`<id>` | Replace the details of a client     |
| DELETE | /api/clients/`<id>` | Delete a client that has no invoice |

`PUT` replaces the whole record, so send every field: any field left out
is cleared.

Anything other than GET, HEAD or OPTIONS needs a CSRF token. The server
sets it in a `csrf_token` cookie on the first response, and the request
has to repeat it in the `X-CSRF-Token` header. With curl that means
keeping a cookie jar:

```
curl -c jar.txt http://127.0.0.1:5000/api/health
curl -b jar.txt -X POST http://127.0.0.1:5000/api/clients -H "Content-Type: application/json" -H "X-CSRF-Token: PASTE_THE_COOKIE_VALUE" -d "{\"name\":\"Aurora Studio\",\"email\":\"hello@aurora.example\"}"
```

## Project structure

```
InvoiceFlow/
    app/
        __init__.py      application factory
        cli.py           flask commands, such as init-db
        config.py        settings read from the environment
        database.py      schema creation and session helpers
        errors.py        JSON error handlers
        exceptions.py    errors the API answers with a status code
        extensions.py    shared SQLAlchemy instance
        security.py      CSRF protection
        validation.py    reusable field validators
        api/
            clients.py   client endpoints
            health.py    health check endpoint
        models/
            client.py    client table
            invoice.py   invoice table and statuses
            line_item.py line items of an invoice
            mixins.py    timestamps and serialisation helpers
            types.py     exact decimal column type
        services/
            clients.py   client rules and persistence
    .env.example         every variable the app reads
    requirements.txt     pinned dependencies
    run.py               development entry point
```
