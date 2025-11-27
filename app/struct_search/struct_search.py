from flask import Flask, render_template, jsonify, redirect, session, request
from pathlib import Path
from olive.file.file import FileTree
from olive.parse.struct.description import find_structs
from app.struct_search.struct_ref import (
    ReferencingStructDescription,
    ReferencingStructDescriptionSet,
)

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

ft = FileTree(Path(__file__).parent.parent.parent)
ft.index_files()
struct_descs = ReferencingStructDescriptionSet()
sel_state = {
    "left": {"selected": bool, "selection": None},
    "right": {"selected": bool, "selection": None},
}


@app.route("/")
def index():
    structs = sorted(
        [struct.to_json() for struct in struct_descs if struct.name is not None],
        key=lambda s: s["name"],
    )
    return render_template("struct_search.html", structs=structs, sel_state=sel_state)


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
            struct_descs.add_struct(
                ReferencingStructDescription.from_reg_struct_desc(struct)
            )
    return redirect("/")


@app.route("/make-selection")
def make_selection():
    side = request.args.get("side")
    selection = request.args.get("selection")
    if side is not None and selection is not None:
        sel_state[side]["selected"] = True
        sel_state[side]["selection"] = selection

    selection = struct_descs.get_struct(selection)
    assert selection is not None
    return jsonify(selection.to_json())
