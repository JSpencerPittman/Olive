from flask import Flask, render_template, jsonify, redirect, session, request
from pathlib import Path
from olive.file.file import FileTree
from olive.parse.struct.description import find_structs
from app.struct_search.struct_ref import (
    ReferencingStructDescription,
    ReferencingStructDescriptionSet,
)
from typing import Optional

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

ft = FileTree(Path(__file__).parent.parent.parent)
ft.index_files()


class StructView(object):
    def __init__(self, idx: int):
        self.idx = idx
        self.selection: Optional[str] = None
        self.struct_desc: Optional[ReferencingStructDescription] = None

    def make_selection(self, selection: str, struct_desc: ReferencingStructDescription):
        self.selection = selection
        self.struct_desc = struct_desc

    def to_json(self) -> dict:
        return {
            "idx": self.idx,
            "selection": self.selection,
            "desc": None if self.struct_desc is None else self.struct_desc.to_json(),
        }


class StructViewManager(object):
    def __init__(self):
        self._views = [StructView(0)]
        self._struct_descs = ReferencingStructDescriptionSet()
        self._last_idx = 0

    def add_struct_desc(self, struct_desc: ReferencingStructDescription):
        self._struct_descs.add_struct(struct_desc)

    def make_selection(self, idx: int, selection: str):
        self._views[idx].make_selection(
            selection, self._struct_descs.get_struct(selection)
        )

    def get_view(self, idx: int) -> StructView:
        return self._views[idx]

    def add_view(self, selection: Optional[str]) -> int:
        new_view_idx = self._last_idx + 1
        new_view = StructView(new_view_idx)
        if selection is not None:
            for struct_desc in self._struct_descs:
                if struct_desc.name == selection:
                    new_view.make_selection(selection, struct_desc)

        self._views.append(new_view)
        self._last_idx = new_view_idx
        return new_view_idx

    def state_to_json(self):
        return {
            "views": sorted(
                [view.to_json() for view in self._views], key=lambda v: v["idx"]
            ),
            "struct_descs": sorted(
                [
                    struct.to_json()
                    for struct in self._struct_descs
                    if struct.name is not None
                ],
                key=lambda s: s["name"],
            ),
        }


view_manager = StructViewManager()


@app.route("/")
def index():
    print(view_manager.state_to_json())
    print(len(view_manager._views))
    return render_template("struct_search.html", state=view_manager.state_to_json())


@app.route("/search")
def search():
    query = request.args.get("q", "")
    matches = [match.to_json() for match in ft.search(query, 10)]
    response = {"matches": matches}
    return jsonify(response)


@app.route("/set-proj-dir", methods=["POST"])
def set_proj_dir():
    session["proj-dir"] = request.form["proj-dir"]
    return redirect("/")


@app.route("/parse-structs")
def parse_structs():
    path = request.args.get("path")
    if path is not None:
        for struct in find_structs(path):
            view_manager.add_struct_desc(
                ReferencingStructDescription.from_reg_struct_desc(struct)
            )
    return redirect("/")


@app.route("/make-selection")
def make_selection():
    view_idx = int(request.args.get("view_idx"))
    selection = request.args.get("selection")
    view_manager.make_selection(view_idx, selection)

    assert selection is not None
    return jsonify(view_manager.get_view(view_idx).to_json())


@app.route("/new-view")
def add_view():
    selection = request.args.get("selection")
    print("SELECTION:", selection)
    view_manager.add_view(selection)
    return jsonify({})
