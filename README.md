# InvoiceFlow

A small web application for freelancers to create, track and print
invoices. It keeps a list of clients, builds invoices with several line
items, computes the totals, and shows what is outstanding, paid or
overdue.

Flask and SQLAlchemy on the server, a JSON API in the middle, and plain
ES modules in the browser. No build step and no frontend framework.

## What it does

- Keep a searchable list of clients, created and edited in place
- Build an invoice from any number of line items, with a live total
- Reopen any invoice and change anything on it, number excepted
- Number invoices per year, in the `INV-2026-001` form
- Move an invoice between draft, sent and paid, either way
- Duplicate an invoice into a fresh draft dated today
- Filter the invoice list by status and by client, from the address bar
- Act on any row from its own menu, without leaving the list
- Print an invoice from a stylesheet made for paper
- Show what is outstanding, what was cashed this month and what is late

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

## Pages

| Path                  | What you can do there                       |
| --------------------- | ------------------------------------------- |
| /                     | The three figures and the six latest invoices |
| /invoices             | The whole list, with filters and a row menu |
| /invoices/new         | Build an invoice and watch the total add up |
| /invoices/`<id>`      | Read it, print it, move it, copy it, delete it |
| /invoices/`<id>`/edit | Change anything, lines included              |
| /clients              | Search, create, edit and delete a client    |

Every page loads its own ES module, asks the API for what it needs, and
renders rows by cloning a `<template>` declared in the markup. Nothing
is built as an HTML string, so a client name is always shown as text.

The creation and the edit page are the same template and the same
module. The presence of an id in the markup is what turns a `POST` into
a `PUT` and swaps the button label.

## Styling

The interface is dark by default. Every colour is a custom property
declared once at the top of `app.css`, and `tailwind-config.js` maps
those properties onto utility names, so a template writes `bg-surface`
or `text-muted` rather than a raw shade. The print stylesheet then
redefines the same properties for paper, which is why one block turns
the whole invoice back to black on white.

## The API

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
A stored status is `draft`, `sent` or `paid`. `overdue` is never stored:
it is derived from a sent invoice whose due date has passed. A draft
never reached the client, so it is neither late nor counted as owed.

The dashboard figures come from one aggregate query: a sent invoice that
is still unpaid counts as outstanding, only payments recorded during the
current month count as cashed, and the overdue count uses the same due
date rule as the invoice list.

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
            css/
                app.css      design tokens and components
                print.css    paper rules for one invoice
            js/
                tailwind-config.js tokens mapped to utility names
                api.js       fetch wrapper and CSRF header
                ui.js        money, dates, badges, toasts, dialogs, menus
                layout.js    off canvas sidebar
                dashboard.js figures and latest invoices
                invoices.js  list, filters and row menus
                invoice-actions.js status moves, copy and delete
                invoice-form.js    line items and live totals
                invoice-detail.js  one invoice and its actions
                clients.js   list, search and the client dialog
        templates/
            base.html          shell, navigation, toasts, dialog
            dashboard.html     landing page
            invoices.html      invoice list
            invoice_form.html  invoice creation and editing
            invoice_detail.html printable invoice
            clients.html       client management
            error.html         404 and 500 page
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
