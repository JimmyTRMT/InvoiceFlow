# InvoiceFlow

A small web application for freelancers to create, track and export
invoices. It keeps a list of clients, builds invoices with several line
items, computes the totals, and shows what is outstanding, paid or
overdue.

This repository is a work in progress. The backend is complete and the
interface is being built page by page on top of it.

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

Open http://127.0.0.1:5000 in a browser. The health check of the API is
at http://127.0.0.1:5000/api/health

Tailwind CSS and the Inter font are loaded from a CDN, so the interface
needs an internet connection to look right. The application itself runs
entirely on your machine.

## The API so far

| Method | Path                | What it does                        |
| ------ | ------------------- | ----------------------------------- |
| GET    | /api/health         | Confirm the API is running          |
| GET    | /api/clients        | List clients, `?search=` to filter  |
| POST   | /api/clients        | Create a client                     |
| GET    | /api/clients/`<id>` | Read one client                     |
| PUT    | /api/clients/`<id>` | Replace the details of a client     |
| DELETE | /api/clients/`<id>` | Delete a client that has no invoice |

| Method | Path                            | What it does                |
| ------ | ------------------------------- | --------------------------- |
| GET    | /api/invoices                   | List invoices               |
| POST   | /api/invoices                   | Create an invoice           |
| GET    | /api/invoices/`<id>`            | Read one invoice with lines |
| PUT    | /api/invoices/`<id>`            | Replace an invoice          |
| POST   | /api/invoices/`<id>`/mark-paid  | Record the invoice as paid  |
| DELETE | /api/invoices/`<id>`            | Delete an invoice           |
| GET    | /api/dashboard/stats            | Outstanding, cashed, overdue |

The invoice list accepts `?status=draft|sent|paid|overdue`,
`?client_id=<id>` and `?limit=<n>`.

`PUT` replaces the whole record, so send every field: any field left out
is cleared.

Amounts are never read from the request. The server recomputes the line
totals, the subtotal, the tax and the grand total from the line items,
and it assigns the invoice number itself in the `INV-2026-001` form.
`overdue` is computed from the due date, so it cannot be set by hand.

The dashboard figures come from one aggregate query: everything not paid
counts as outstanding, only payments recorded during the current month
count as cashed, and the overdue count uses the same due date rule as
the invoice list.

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
        views.py         page routes
        static/
            css/         stylesheets
            js/          browser scripts
        templates/       page markup
        api/
            clients.py   client endpoints
            dashboard.py dashboard statistics endpoint
            health.py    health check endpoint
            invoices.py  invoice endpoints
        models/
            client.py    client table
            invoice.py   invoice table and statuses
            line_item.py line items of an invoice
            mixins.py    timestamps and serialisation helpers
            types.py     exact decimal column type
        services/
            clients.py   client rules and persistence
            dashboard.py aggregated figures
            invoices.py  invoice rules, totals and numbering
    .env.example         every variable the app reads
    requirements.txt     pinned dependencies
    run.py               development entry point
```
