import functools
import os

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    g,
    current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT id, username, role FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    if not current_app.config["REGISTER_ACTIVE"]:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            role_str = request.form["role"]
            assert role_str in ["Student", "Professor"]
        except:
            role_str = False

        db = get_db()

        error = None
        if not role_str:
            error = "Role is required."
        elif not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif (
                db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone()
                is not None
        ):
            error = "User {} is already registered.".format(username)

        if error is None:
            if role_str == "Student":
                role = 1
            elif role_str == "Professor":
                role = 2
            else:
                raise

            db.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
            db.commit()
            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session["hmac_key"] = os.urandom(16)
            return redirect(url_for("panel.show_list"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def login_required(view, min_role: int = 1):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user["role"] < min_role:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
