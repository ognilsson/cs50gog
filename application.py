import os
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from pytz import timezone
from flask_mail import Mail, Message
import random
import string

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)


# Email config
app.config["MAIL_DEFAULT_SENDER"] = "cs50microjournal@gmail.com"
app.config["MAIL_USERNAME"] = "cs50microjournal@gmail.com"
app.config["MAIL_PASSWORD"] = "HMS2020!"
app.config["MAIL_PORT"] = 465
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///journal.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
    #raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show something to the user"""
    return apology("This is the index page")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email as username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/forgot_password", methods=["GET", "POST"]) ##### Need to add function so users can change password
def forgot_password():
    """Sends a new password to the user"""

    # User just clicked the link (reached route via GET)
    if request.method == "GET":
        return render_template("forgot_password.html")

    # User submitted their email (Reached route via POST)
    else:
        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("Must provide email", 403)

        # Generate new random password
        # From https://pynative.com/python-generate-random-string/
        length = 4
        letters = string.ascii_lowercase
        new_password = ''.join(random.choice(letters) for i in range(length))

        # Send email to user with new password
        email = request.form.get("email")

        if len(db.execute("SELECT * FROM users WHERE email = ?", email)) != 1:
            return apology("email does not match or records", 403)

        m_body = "Your new password is: " + new_password
        message = Message(subject="New Password", sender="cs50microjournal@gmail.com", recipients=[email])
        message.body = m_body
        print(m_body)
        mail.send(message)
        return redirect("/login")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via GET
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via post
    else:
        # Checking for email and if it already exists
        if not request.form.get("email") or len(db.execute("SELECT email from users WHERE email = ?", request.form.get("email"))) != 0:
            return apology("email not inputted or already used")

        # Checking for password and if it matches the confirmation
        if not request.form.get("password") or request.form.get("password") != request.form.get("confirmation"):
            return apology("Password not inputted or did not match confirmation")

        # Insert new user to db
        else:
            db.execute("INSERT INTO users (email, hash) VALUES (?, ?)", request.form.get("email"),
                       generate_password_hash(request.form.get("password")))
            return redirect("/login")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
