from fasthtml.common import *
import re


class CustomTable:
    def __init__(self, data: list, columns: list, route_base: str = "", table_id: str = "record-container", options=None):
        self.data = data
        self.columns = columns
        self.route_base = route_base
        self.container_id = table_id
        self.options = {
            "search": True,
            "order": True,
            "pagination": True,
            "total": True,
            "live_search": True,
            "select_box": True,
            "delete": True,
            "top_options": [10, 20, 50, 100],
            "top_default": 10,
        }
        if options:
            self.options.update(options)

    def natural_sort_key(self, s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split("([0-9]+)", str(s))]

    def _sort_data(self, data, field, direction):
        if not data:
            return data
        reverse = direction == "desc"
        key_fn = lambda x: x[field] if isinstance(data[0][field], (int, float)) else self.natural_sort_key(x[field])
        return sorted(data, key=key_fn, reverse=reverse)

    def _sort_link(self, col, field, direction, q, top, skip):
        if not self.options["order"]:
            return Th(col.title())
        new_dir = "desc" if field == col and direction == "asc" else "asc"
        arrow = " ▼" if field == col and direction == "desc" else " ▲" if field == col else ""
        orderby = f"{col} {new_dir}"
        return Th(
            col.title() + arrow,
            hx_get=f"{self.route_base}/data?q={q}&top={top}&skip={skip}&orderby={orderby}",
            hx_target=f"#{self.container_id}",
            hx_push_url=f"{self.route_base}?q={q}&top={top}&skip={skip}&orderby={orderby}",
        )

    def _build_header(self, field, direction, q, top, skip):
        cols = [self._sort_link(c, field, direction, q, top, skip) for c in self.columns]
        if self.options["select_box"]:
            cols.insert(0, Th(Input(type="checkbox", onclick="toggleAll(this)"), width="1%"))
        return Thead(Tr(*cols))

    def _build_rows(self, current):
        if not current:
            return [Tr(Td("No records found", colspan=str(len(self.columns) + (1 if self.options["select_box"] else 0)), style="text-align: center"))]

        rows = []
        for r in current:
            row = [Td(r[col]) for col in self.columns]
            if self.options["select_box"]:
                row.insert(0, Td(Input(type="checkbox", value=r["id"], name="selected[]")))
            rows.append(Tr(*row))
        return rows

    def _build_form(self, q, top, field, direction):
        form_elems = []
        if self.options["search"]:
            form_elems.append(
                Input(
                    id="q",
                    name="q",
                    placeholder="Search...",
                    value=q,
                    hx_get=f"{self.route_base}/data",
                    hx_target=f"#{self.container_id}",
                    hx_trigger="keyup changed delay:300ms" if self.options["live_search"] else "change",
                    hx_push_url="false",
                    hx_include="[name='top'],[name='orderby']",
                )
            )
        if self.options["pagination"]:
            form_elems.append(
                Select(
                    *[Option(str(x), value=str(x), selected=(x == top)) for x in self.options["top_options"]],
                    id="top",
                    name="top",
                    hx_get=f"{self.route_base}/data",
                    hx_target=f"#{self.container_id}",
                    hx_trigger="change",
                    hx_push_url="false",
                    hx_include="[name='q'],[name='orderby']",
                )
            )
        form_elems.append(Input(type="hidden", name="orderby", value=f"{field} {direction}"))

        toolbar = []
        if self.options["delete"] and self.options["select_box"]:
            toolbar.append(
                Button("Delete Selected", type="button", hx_delete=f"{self.route_base}/data", hx_target=f"#{self.container_id}", hx_include="[name='selected[]']", cls="secondary")
            )

        return Form(Group(*form_elems), Div(*toolbar), method="get")

    def _build_pagination(self, total, top, skip, field, direction, q, current_page, pages):
        def page_link(s, label=None, extra_cls=""):
            page_num = (s // top) + 1
            lbl = label or (Strong(str(page_num)) if page_num == current_page else str(page_num))
            return AX(
                lbl,
                f"{self.route_base}/data?q={q}&top={top}&skip={s}&orderby={field} {direction}",
                self.container_id,
                hx_push_url=f"{self.route_base}?q={q}&top={top}&skip={s}&orderby={field} {direction}",
                cls=("active " if page_num == current_page else "") + extra_cls,
            )

        nav = []
        if skip >= top:
            nav.append(page_link(skip - top, "Previous"))
        else:
            nav.append(A("Previous", href="", cls="disabled"))

        def should_show(p):
            return p <= 2 or p > pages - 2 or abs(p - current_page) <= 1

        def ellipsis():
            return A("...", href="")

        last = 0
        for p in range(1, pages + 1):
            if should_show(p):
                if last and p - last > 1:
                    nav.append(ellipsis())
                nav.append(page_link((p - 1) * top))
                last = p

        if skip + top < total:
            nav.append(page_link(skip + top, "Next"))
        else:
            nav.append(A("Next", href="", cls="disabled"))

        return Nav(*nav, cls="pagination")

    def _script(self):
        if not self.options["select_box"]:
            return ""
        return Script(
            """
            function toggleAll(source) {
                var checkboxes = document.getElementsByName('selected[]');
                for (var i = 0; i < checkboxes.length; i++) {
                    checkboxes[i].checked = source.checked;
                    checkboxes[i].indeterminate = false;
                }
            }

            function updateHeaderCheckbox() {
                var headerCheckbox = document.querySelector('thead input[type="checkbox"]');
                var checkboxes = document.getElementsByName('selected[]');
                var checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
                if (checkedCount === 0) {
                    headerCheckbox.checked = false;
                    headerCheckbox.indeterminate = false;
                } else if (checkedCount === checkboxes.length) {
                    headerCheckbox.checked = true;
                    headerCheckbox.indeterminate = false;
                } else {
                    headerCheckbox.checked = false;
                    headerCheckbox.indeterminate = true;
                }
            }

            document.addEventListener('change', function(e) {
                if (e.target.name === 'selected[]') {
                    updateHeaderCheckbox();
                }
            });
            """
        )

    def render(self, request: Request):
        # Extract and process query params
        params = request.query_params
        q = params.get("q", "").lower()
        skip = int(params.get("skip", "0"))
        top = int(params.get("top", self.options["top_default"]))
        orderby = params.get("orderby", "id asc").split()
        field, direction = orderby if len(orderby) == 2 else (orderby[0], "asc")

        # Filter and sort
        data = self.data
        if self.options["search"] and q:
            data = [r for r in data if q in r["name"].lower() or q in r["email"].lower()]
        data = self._sort_data(data, field, direction)

        total = len(data)
        pages = max((total + top - 1) // top, 1)
        skip = min(max(0, skip), total - 1) if total > 0 else 0
        current = data[skip : skip + top]
        current_page = (skip // top) + 1

        header = self._build_header(field, direction, q, top, skip)
        rows = [header] + self._build_rows(current)
        table = Table(*rows, cls="striped")

        form = self._build_form(q, top, field, direction)

        info = P(f"Showing {skip + 1} to {min(skip + top, total)} of {total} records") if self.options["total"] else ""
        paginator = self._build_pagination(total, top, skip, field, direction, q, current_page, pages) if self.options["pagination"] else ""

        return Div(self._script(), form, table, Div(info, paginator, cls="table-footer") if info or paginator else "")
