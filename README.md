# InvoiceFlow

A small web application for freelancers to create, track and export
invoices. It keeps a list of clients, builds invoices with several line
items, computes the totals, and shows what is outstanding, paid or
overdue.

This repository is a work in progress. The backend skeleton is in place
and serves a health check endpoint; the features are added step by step.

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

## Running the app

```
python run.py
```

The server starts on http://127.0.0.1:5000 and the health check is
available at http://127.0.0.1:5000/api/health

## Project structure

```
InvoiceFlow/
    app/
        __init__.py      application factory
        config.py        settings read from the environment
        errors.py        JSON error handlers
        extensions.py    shared SQLAlchemy instance
        api/
            health.py    health check endpoint
    .env.example         every variable the app reads
    requirements.txt     pinned dependencies
    run.py               development entry point
```
