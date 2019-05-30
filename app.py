from sys import stderr
import string
import random
from flask import Flask, request, redirect, jsonify, abort, render_template
from pygments import highlight
from pygments.lexers import Python3TracebackLexer
from pygments.formatters import HtmlFormatter
import db

app = Flask(__name__)


def _wants_json():
    """
    Determine if the user wants json or html output for APIs which can serve both.

    We prefer sending html over json, and only allow json if the Accept header contains application/json
    and either lacks text/html or has application/json has higher quality than text/html.

    :return: True if the user should be served json, False if the user should be served html
    """
    if not request.accept_mimetypes.accept_json:
        return False  # if json isn't allowed, don't serve it
    if not request.accept_mimetypes.accept_html:
        return True  # json is allowed but html isn't => serve json
    # otherwise prefer to serve html over json, respecting the quality param on Accept header
    best = request.accept_mimetypes.best_match(("text/html", "application/json"))
    if best != "application/json":
        return False  # html is of greater quality than json
    if request.accept_mimetypes.quality("text/html") == request.accept_mimetypes.quality("application/json"):
        return False  # html is of equal quality to json, and we prefer html
    return True  # json is of higher quality than html


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("c", None):
        return jsonify({"status": "error", "error": "Invalid request"}), 400
    charset = string.ascii_letters + string.digits
    with db.DbConnection() as conn:
        slug = "".join(random.choice(charset) for _ in range(4))
        while len(slug) < 17:
            found = len(conn.execute("SELECT paste_slug FROM pastes WHERE paste_slug = %s", (slug,)))
            if found == 0:
                break
            slug += random.choice(charset)
        if len(slug) == 17:
            # stderr is logged so we can examine these events later
            print(f"Unable to get unique URL slug, tried {slug}", file=stderr)
            return jsonify({"status": "error", "error": "Unable to get unique URL slug"}), 500
        conn.execute("""INSERT INTO pastes (paste_slug, paste_expires, paste_type, paste_content)
                     VALUES (%s, DATE_ADD(UTC_TIMESTAMP(), INTERVAL 7 DAY), 'paste', %s)""", (slug, data["c"]))
        return jsonify({"status": "success", "url": request.url_root + slug})


@app.route("/<slug>")
def get_paste(slug):
    if len(slug) > 16:
        if _wants_json():
            return jsonify({"status": "error", "error": "Invalid request"}), 400
        else:
            abort(400)
    with db.DbConnection() as conn:
        data = conn.fetch("SELECT * FROM pastes WHERE paste_slug = %s", (slug,))
    if not data:
        if _wants_json():
            return jsonify({"status": "error", "error": "Paste not found"}), 404
        else:
            abort(404)
    if data["paste_type"] == "redirect":
        redirect(data["paste_content"])
    if _wants_json():
        return jsonify({"status": "success", "data": data["paste_content"], "expires": data["paste_expires"]})
    return highlight(data["paste_content"],
                     Python3TracebackLexer(),
                     HtmlFormatter(full=True, linenos="table", lineanchors="l", anchorlinenos=True, wrapcode=True))


if __name__ == "__main__":
    app.run()
