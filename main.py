from fasthtml.common import *
import re


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
    def __init__(self, data: list, route_base: str = "", container_id: str = "record-container"):
        self.data = data
        self.route_base = route_base
        self.container_id = container_id

    def natural_sort_key(self, s):
        """Natural sort helper function that splits on numbers"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split("([0-9]+)", str(s))]

    def render(self, request: Request):
        params = request.query_params
        q = params.get("q", "").lower()
        page = int(params.get("page", "1"))
        top = int(params.get("top", "10"))
        sortby = params.get("sortby", "id")
        sorttype = params.get("sorttype", "asc")

        # Filter and sort data
        data = self.data
        if q:
            data = [r for r in data if q in r["name"].lower() or q in r["email"].lower()]

        # Sort data with natural sorting
        reverse = sorttype == "desc"
        if not data:
            # Return empty list if no data
            pass
        elif isinstance(data[0][sortby], (int, float)):
            # Use regular sorting for numbers
            data = sorted(data, key=lambda x: x[sortby], reverse=reverse)
        else:
            # Use natural sorting for strings
            data = sorted(data, key=lambda x: self.natural_sort_key(x[sortby]), reverse=reverse)

        total = len(data)
        pages = max((total + top - 1) // top, 1)
        page = min(max(1, page), pages)
        start = (page - 1) * top
        end = start + top
        current = data[start:end]

        def sort_link(col: str):
            new_type = "desc" if sortby == col and sorttype == "asc" else "asc"
            return Th(
                col.title() + (" ▼" if sortby == col and sorttype == "desc" else " ▲" if sortby == col and sorttype == "asc" else ""),
                hx_get=f"{self.route_base}/data?q={q}&top={top}&page={page}&sortby={col}&sorttype={new_type}",
                hx_target=f"#{self.container_id}",
                hx_push_url=f"{self.route_base}?q={q}&top={top}&page={page}&sortby={col}&sorttype={new_type}",
                width="10%",
            )

        header = Thead(Tr(sort_link("id"), sort_link("name"), sort_link("email")))
        rows = [header]
        if not current:
            rows.append(Tr(Td("No records found", colspan="3", style="text-align: center")))
        else:
            for r in current:
                rows.append(Tr(Td(r["id"]), Td(r["name"]), Td(r["email"])))
        table = Table(*rows, cls="striped")

        # Search + per-page (live update via HTMX)
        form = Form(
            Group(
                Input(
                    id="q",
                    name="q",
                    placeholder="Search...",
                    value=q,
                    hx_get=f"{self.route_base}/data",
                    hx_target=f"#{self.container_id}",
                    hx_trigger="keyup changed delay:300ms",
                    hx_push_url="false",
                    hx_include="[name='top'],[name='sortby'],[name='sorttype']",  # Include sort parameters
                ),
                Select(
                    *[Option(str(x), selected=(x == top)) for x in [10, 20, 50, 100]],
                    id="top",
                    name="top",
                    hx_get=f"{self.route_base}/data",
                    hx_target=f"#{self.container_id}",
                    hx_trigger="change",
                    hx_push_url="false",
                    hx_include="[name='q'],[name='sortby'],[name='sorttype']",  # Include sort parameters
                ),
                Input(type="hidden", name="sortby", value=sortby),  # Add hidden inputs for sort parameters
                Input(type="hidden", name="sorttype", value=sorttype),
            ),
            method="get",
        )

        info = P(f"Showing {start + 1} to {min(end, total)} of {total} records")

        nav = []

        def page_link(p, label=None, cls_extra=""):
            lbl = label or (Strong(str(p)) if p == page else str(p))
            return AX(
                lbl,
                f"{self.route_base}/data?q={q}&top={top}&page={p}&sortby={sortby}&sorttype={sorttype}",
                f"{self.container_id}",
                hx_push_url=f"{self.route_base}?q={q}&top={top}&page={p}&sortby={sortby}&sorttype={sorttype}",
                cls=("active " if p == page else "") + cls_extra,
            )

        def ellipsis():
            return A("...", href="", cls="disabled")

        def should_show(p):
            return p <= 2 or p > pages - 2 or abs(p - page) <= 1

        if page > 1:
            nav.append(page_link(page - 1, label="⟨ Prev", cls_extra="prev"))
        else:
            nav.append(A("⟨ Prev", href="", cls="disabled"))

        last = 0
        for p in range(1, pages + 1):
            if should_show(p):
                if last and p - last > 1:
                    nav.append(ellipsis())
                nav.append(page_link(p))
                last = p

        if page < pages:
            nav.append(page_link(page + 1, label="Next ⟩", cls_extra="next"))
        else:
            nav.append(A("Next ⟩", href="", cls="disabled"))

        paginator = Nav(*nav, cls="pagination")

        return Div(form, table, Div(info, paginator, cls="table-footer"))


RECORDS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 200)]
ADMIN_RECORDS = [{"id": i, "name": f"Admin {i}", "email": f"admin{i}@example.com"} for i in range(1, 400)]


@rt("")
def index(request: Request):
    return Titled(
        "Record Viewer",
        Container(A("Admin", href="/admin", type="button"), Div(id="record-container", hx_get="/data?" + request.url.query, hx_trigger="load", hx_target="this")),
    )


@rt("/data")
def data(request: Request):
    table = CustomTable(RECORDS, route_base="", container_id="record-container")
    return table.render(request)


@rt("/admin")
def admin(request: Request):
    return Titled(
        "Admin Record Viewer",
        Container(A("Go Back", href="/", type="button"), Div(id="admin-container", hx_get="/admin/data?" + request.url.query, hx_trigger="load", hx_target="this")),
    )


@rt("/admin/data")
def admin_data(request: Request):
    admin_table = CustomTable(ADMIN_RECORDS, route_base="/admin", container_id="admin-container")
    return admin_table.render(request)


serve()
