"""
Auth routes - login, logout.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user

from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models import User, Role


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page and form handler."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=request.form.get("remember", False))
                next_url = request.args.get("next") or url_for("admin.dashboard")
                return redirect(next_url)
            flash("Account is inactive.", "danger")
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    """Logout user."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
