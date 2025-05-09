from fasthtml.common import *

RECORDS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 20000)]

app, rt = fast_app(
    hdrs=(
        Style(
            """
:root { --pico-font-size: 100%; }
.pagination a {
  margin: 0 0.25em;
  padding: 0.5em 0.75em;
  background: #333;
  color: #eee;
  border-radius: 4px;
  text-decoration: none;
}
.pagination a.active {
  background: #007bff;
  color: white;
}
.pagination .disabled {
  cursor: unset;
  opacity: 0.5;
}
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1em;
}
"""
        ),
    )
)


# Full-page route: responds to query params and loads /list behind-the-scenes
@rt("/")
def get(request):
    return Titled("Record Viewer", Container(Div(id="record-container", hx_get=f"/list?{request.url.query}", hx_trigger="load", hx_target="this")))


# HTMX route: renders only the table & filters
@rt("/list")
def get_filtered(request):
    params = request.query_params
    q = params.get("q", "").lower()
    page = int(params.get("page", "1"))
    top = int(params.get("top", "10"))

    # Filter and paginate data
    data = RECORDS
    if q:
        data = [r for r in data if q in r["name"].lower() or q in r["email"].lower()]
    total = len(data)
    pages = max((total + top - 1) // top, 1)
    page = min(max(1, page), pages)
    start = (page - 1) * top
    end = start + top
    current = data[start:end]

    # Info summary
    info = P(f"Showing {start + 1} to {min(end, total)} of {total} records", cls="table-info")

    # Search + per-page (live update via HTMX)
    form = Form(
        Group(
            Input(
                id="q",
                name="q",
                placeholder="Search...",
                value=q,
                hx_get="/list",  # Keep fetching from /list
                hx_target="#record-container",  # Only update the table content
                hx_trigger="keyup changed delay:300ms",
                hx_push_url="false",  # Prevent the URL from changing
            ),
            Select(
                *[Option(str(x), selected=(x == top)) for x in [10, 20, 50, 100]],
                id="top",
                name="top",
                hx_get="/list",  # Fetch from /list for pagination change
                hx_target="#record-container",
                hx_trigger="change",
                hx_push_url="false",  # Prevent the URL from changing on per-page change
                hx_include="[name='q']",
            ),
        ),
        method="get",  # Ensure it's a GET method to avoid a full-page reload
    )

    # Data table with dummy columns
    header = Tr(Th("ID"), Th("Name"), Th("Email"))
    rows = [header]
    for r in current:
        rows.append(Tr(Td(r["id"]), Td(r["name"]), Td(r["email"])))
    table = Table(*rows, cls="dark-table")

    # Pagination with truncation
    nav = []

    def page_link(p, label=None, cls_extra=""):
        lbl = label or (Strong(str(p)) if p == page else str(p))
        return AX(
            lbl,
            f"/list?q={q}&top={top}&page={p}",
            "record-container",
            hx_push_url=f"/?q={q}&top={top}&page={p}",
            cls=("active " if p == page else "") + cls_extra,
        )  # Prevent URL change

    def ellipsis():
        return A("...", href="", cls="disabled")

    def should_show(p):
        return p <= 2 or p > pages - 2 or abs(p - page) <= 1

    # Prev button
    if page > 1:
        nav.append(page_link(page - 1, label="⟨ Prev", cls_extra="prev"))
    else:
        nav.append(A("⟨ Prev", href="", cls="disabled"))

    # Page numbers with truncation
    last = 0
    for p in range(1, pages + 1):
        if should_show(p):
            if last and p - last > 1:
                nav.append(ellipsis())
            nav.append(page_link(p))
            last = p

    # Next button
    if page < pages:
        nav.append(page_link(page + 1, label="Next ⟩", cls_extra="next"))
    else:
        nav.append(A("Next ⟩", href="", cls="disabled"))

    paginator = Nav(*nav, cls="pagination")

    return Div(form, table, Div(info, paginator, cls="table-footer"))


serve()
