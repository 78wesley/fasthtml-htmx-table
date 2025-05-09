# FastHTML HTMX Table Demo

A simple FastAPI application demonstrating dynamic table updates using HTMX and FastHTML.
It also pushes the query params to the root url and not the url that genereates the data.

## Requirements

-   Python 3.13
-   HTMX (included via CDN)
-   [uv package manager](https://github.com/astral-sh/uv)

## Running the Application

Start the server with:

```bash
uv run main.py
```

Access the application at `http://localhost:5001`
