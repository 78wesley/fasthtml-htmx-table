from fasthtml.common import *
from CustomTable import CustomTable

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

    table = CustomTable(
        RECORDS,
        route_base="",
        table_id="record-container",
        columns=["id", "name", "email"],
        options={
            "search": True,
            "order": True,
            "pagination": True,
            "total": True,
            "live_search": True,
            "select_box": True,
            "delete": True,
            "top_options": [1, 5, 10, 20, 30, 40, 50],
            "top_default": 5,
        },
    )
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

    table = CustomTable(
        ADMIN_RECORDS,
        route_base="/admin",
        table_id="admin-container",
        columns=["id", "name", "email"],
        options={"search": True, "order": True, "pagination": True, "total": False, "live_search": True, "select_box": True, "delete": True, "infinite_scroll": True},
    )
    return table.render(request)


serve()
