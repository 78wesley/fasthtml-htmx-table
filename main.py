from fasthtml.common import *


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


class CustomTable:
    def __init__(self, data, route_base="", container_id="record-container"):
        self.data = data
        self.route_base = route_base
        self.container_id = container_id

    def render(self, request: Request):
        params = request.query_params
        q = params.get("q", "").lower()
        page = int(params.get("page", "1"))
        top = int(params.get("top", "10"))

        # Filter and paginate data
        data = self.data
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
                    hx_get=f"{self.route_base}/list",  # Keep fetching from {route_base}/list
                    hx_target=f"#{self.container_id}",  # Only update the table content
                    hx_trigger="keyup changed delay:300ms",
                    hx_push_url="false",  # Prevent the URL from changing
                ),
                Select(
                    *[Option(str(x), selected=(x == top)) for x in [10, 20, 50, 100]],
                    id="top",
                    name="top",
                    hx_get=f"{self.route_base}/list",  # Fetch from {route_base}/list for pagination change
                    hx_target=f"#{self.container_id}",
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
                f"{self.route_base}/list?q={q}&top={top}&page={p}",
                f"{self.container_id}",
                hx_push_url=f"{self.route_base}?q={q}&top={top}&page={p}",
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


RECORDS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 200)]

table_view = CustomTable(RECORDS, route_base="", container_id="record-container")


@rt("")
def index(request: Request):
    return Titled(
        "Record Viewer",
        Container(A("View Admin", href="/admin", type="button"), Div(id="record-container", hx_get="/list?" + request.url.query, hx_trigger="load", hx_target="this")),
    )


@rt("/list")
def table_data(request: Request):
    return table_view.render(request)


OTHER_RECORDS = [{"id": i, "name": f"Admin {i}", "email": f"admin{i}@example.com"} for i in range(1, 400)]
admin_table = CustomTable(OTHER_RECORDS, route_base="/admin", container_id="admin-container")


@rt("/admin")
def admin_page(request: Request):
    return Titled(
        "Admin Viewer", Container(A("Go Back", href="/", type="button"), Div(id="admin-container", hx_get="/admin/list?" + request.url.query, hx_trigger="load", hx_target="this"))
    )


@rt("/admin/list")
def admin_data(request):
    return admin_table.render(request)


serve()
