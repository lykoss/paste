from sys import stderr
import string
from random import SystemRandom
import base64
from flask import Flask, request, redirect, jsonify, abort, render_template
from flask_talisman import Talisman
from pygments import highlight
from pygments.lexers import PythonTracebackLexer
from pygments.formatters import HtmlFormatter
import db
import config
import webhook

random = SystemRandom()
app = Flask(__name__)
Talisman(app, content_security_policy={"default-src": "'self' 'unsafe-inline'"})


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
        paste_url = request.url_root + slug
        webhook.send_newpaste(paste_url)
        return jsonify({"status": "success", "url": paste_url})


@app.route("/webhook_key")
def get_webhook_key():
    if not config.WEBHOOK_ENABLE:
        return jsonify({"status": "error", "error": "Webhook is disabled"}), 403
    pkey = base64.b64encode(webhook.get_public_key()).decode("ascii")
    return jsonify({"status": "success", "public": pkey})


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
        return redirect(data["paste_content"])
    if _wants_json():
        return jsonify({"status": "success", "data": data["paste_content"], "expires": data["paste_expires"]})
    output = highlight(data["paste_content"],
                       PythonTracebackLexer(),
                       HtmlFormatter(full=True, linenos="table", lineanchors="l",
                                     anchorlinenos=True, wrapcode=True))
    # get rid of red boxes. Tried to do this the "official" way but pygments hates me
    return output.replace(r'class="err"', "")


@app.route("/")
def get_root():
    return get_paste("")


if __name__ == "__main__":
    app.run()
