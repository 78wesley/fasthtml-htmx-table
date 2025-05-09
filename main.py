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
    def __init__(self, data: list, route_base: str = "", table_id: str = "record-container"):
        self.data = data
        self.route_base = route_base
        self.container_id = table_id

    def natural_sort_key(self, s):
        """Natural sort helper function that splits on numbers"""
        return [int(text) if text.isdigit() else text.lower() for text in re.split("([0-9]+)", str(s))]

    def render(self, request: Request):
        params = request.query_params
        q = params.get("q", "").lower()
        skip = int(params.get("skip", "0"))
        top = int(params.get("top", "10"))
        orderby = params.get("orderby", "id asc").split()
        field, direction = orderby if len(orderby) == 2 else (orderby[0], "asc")

        # Filter and sort data
        data = self.data
        if q:
            data = [r for r in data if q in r["name"].lower() or q in r["email"].lower()]

        # Sort data with natural sorting
        reverse = direction == "desc"
        if not data:
            # Return empty list if no data
            pass
        elif isinstance(data[0][field], (int, float)):
            data = sorted(data, key=lambda x: x[field], reverse=reverse)
        else:
            data = sorted(data, key=lambda x: self.natural_sort_key(x[field]), reverse=reverse)

        total = len(data)
        pages = max((total + top - 1) // top, 1)
        skip = min(max(0, skip), total - 1) if total > 0 else 0
        current = data[skip : skip + top]
        current_page = (skip // top) + 1

        def sort_link(col: str, width: str = ""):
            new_direction = "desc" if field == col and direction == "asc" else "asc"
            new_orderby = f"{col} {new_direction}"
            return Th(
                col.title() + (" ▼" if field == col and direction == "desc" else " ▲" if field == col and direction == "asc" else ""),
                hx_get=f"{self.route_base}/data?q={q}&top={top}&skip={skip}&orderby={new_orderby}",
                hx_target=f"#{self.container_id}",
                hx_push_url=f"{self.route_base}?q={q}&top={top}&skip={skip}&orderby={new_orderby}",
                width=width,
            )

        # Add checkbox column to header
        header = Thead(Tr(Th(Input(type="checkbox", onclick="toggleAll(this)"), width="1%"), sort_link("id"), sort_link("name"), sort_link("email")))

        rows = [header]
        if not current:
            rows.append(Tr(Td("No records found", colspan="4", style="text-align: center")))
        else:
            for r in current:
                rows.append(Tr(Td(Input(type="checkbox", value=r["id"], name="selected[]")), Td(r["id"]), Td(r["name"]), Td(r["email"])))
        table = Table(*rows, cls="striped")

        # Add delete button
        delete_btn = Button(
            "Delete Selected", type="button", hx_delete=f"{self.route_base}/data", hx_target=f"#{self.container_id}", hx_include="[name='selected[]']", cls="secondary"
        )

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
                    hx_include="[name='top'],[name='orderby']",
                ),
                Select(
                    *[Option(str(x), selected=(x == top)) for x in [10, 20, 50, 100]],
                    id="top",
                    name="top",
                    hx_get=f"{self.route_base}/data",
                    hx_target=f"#{self.container_id}",
                    hx_trigger="change",
                    hx_push_url="false",
                    hx_include="[name='q'],[name='orderby']",
                ),
                Input(type="hidden", name="orderby", value=f"{field} {direction}"),
            ),
            delete_btn,
            method="get",
        )

        info = P(f"Showing {skip + 1} to {min(skip + top, total)} of {total} records")

        nav = []

        def page_link(skip_val, label=None, cls_extra=""):
            page_num = (skip_val // top) + 1
            lbl = label or (Strong(str(page_num)) if page_num == current_page else str(page_num))
            return AX(
                lbl,
                f"{self.route_base}/data?q={q}&top={top}&skip={skip_val}&orderby={field} {direction}",
                f"{self.container_id}",
                hx_push_url=f"{self.route_base}?q={q}&top={top}&skip={skip_val}&orderby={field} {direction}",
                cls=("active " if page_num == current_page else "") + cls_extra,
            )

        # Add JavaScript for toggle all functionality
        toggle_script = Script(
            """
            function toggleAll(source) {
                var checkboxes = document.getElementsByName('selected[]');
                for(var i=0; i<checkboxes.length; i++) {
                    checkboxes[i].checked = source.checked;
                }
            }
        """
        )

        def ellipsis():
            return A("...", href="")

        def should_show(p):
            return p <= 2 or p > pages - 2 or abs(p - current_page) <= 1

        # Previous link
        if skip >= top:
            nav.append(page_link(skip - top, label="Previous"))
        else:
            nav.append(A("Previous", href="", cls="disabled"))

        # Page numbers
        last = 0
        for p in range(1, pages + 1):
            if should_show(p):
                if last and p - last > 1:
                    nav.append(ellipsis())
                nav.append(page_link((p - 1) * top))
                last = p

        # Next link
        if skip + top < total:
            nav.append(page_link(skip + top, label="Next"))
        else:
            nav.append(A("Next", href="", cls="disabled"))

        paginator = Nav(*nav, cls="pagination")

        return Div(toggle_script, form, table, Div(info, paginator, cls="table-footer"))


RECORDS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 200)]
ADMIN_RECORDS = [{"id": i, "name": f"Admin {i}", "email": f"admin{i}@example.com"} for i in range(1, 400)]


@rt("")
def index(request: Request):
    return Titled(
        "Record Viewer",
        Group(A("Admin", href="/admin", type="button"), A("Reset data", hx_get="/reset/record-container", type="button", hx_swap="none")),
        Div(id="record-container", hx_get="/data?" + request.url.query, hx_trigger="load, record-container from:body", hx_target="this"),
    )


@rt("/reset/{id}")
def reset_data(id: str):
    if id == "record-container":
        global RECORDS
        RECORDS = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 200)]
    elif id == "admin-container":
        global ADMIN_RECORDS
        ADMIN_RECORDS = [{"id": i, "name": f"Admin {i}", "email": f"admin{i}@example.com"} for i in range(1, 400)]

    return Response(headers={"HX-Trigger": id})


@rt("/data", methods=["GET", "DELETE"])
def data(request: Request):
    if request.method == "DELETE":
        selected_ids = [int(id) for id in request.query_params.getlist("selected[]")]
        global RECORDS
        RECORDS = [record for record in RECORDS if record["id"] not in selected_ids]

    table = CustomTable(RECORDS, route_base="", table_id="record-container")
    return table.render(request)


@rt("/admin")
def admin(request: Request):
    return Titled(
        "Admin Record Viewer",
        Group(A("Go Back", href="/", type="button"), A("Reset data", hx_get="/reset/admin-container", type="button", hx_swap="none")),
        Div(id="admin-container", hx_get="/admin/data?" + request.url.query, hx_trigger="load, admin-container from:body", hx_target="this"),
    )


@rt("/admin/data", methods=["GET", "DELETE"])
def admin_data(request: Request):
    if request.method == "DELETE":
        selected_ids = [int(id) for id in request.query_params.getlist("selected[]")]
        global ADMIN_RECORDS
        ADMIN_RECORDS = [record for record in ADMIN_RECORDS if record["id"] not in selected_ids]
    admin_table = CustomTable(ADMIN_RECORDS, route_base="/admin", table_id="admin-container")
    return admin_table.render(request)


serve()
