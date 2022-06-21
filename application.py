import os
import random

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


Session(app)
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mentalmaths.db")
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
            session["user_id"] = rows[0]["id"]
            rows = db.execute("SELECT op FROM quiz WHERE user_id = :id", id = session["user_id"])
        x = 0
        for row in rows:
            x = x + 1
        if x == 0:
            db.execute("INSERT INTO quiz (user_id, op) VALUES (:user, :o)", user=session["user_id"], o="Def")
        rows1 = db.execute("SELECT op FROM operation WHERE user_id = :id", id = session["user_id"])
        y = 0
        for row in rows1:
            y = y + 1
        if y == 0:
            db.execute("INSERT INTO operation (user_id, op, point) VALUES (:user, :o, :p)", user=session["user_id"], o="Division", p = 0)
            db.execute("INSERT INTO operation (user_id, op, point) VALUES (:user, :o, :p)", user=session["user_id"], o="Multiplication", p = 0)
            db.execute("INSERT INTO operation (user_id, op, point) VALUES (:user, :o, :p)", user=session["user_id"], o="Addition", p = 0)
            db.execute("INSERT INTO operation (user_id, op, point) VALUES (:user, :o, :p)", user=session["user_id"], o="Subtraction", p = 0)
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


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
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        rows = db.execute("SELECT username FROM users")
        for row in rows:
            if request.form.get("username") == row["username"]:
                return apology("This username is already taken", 403)
        # Ensure inputs was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)
        if not request.form.get("confirmation"):
            return apology("must provide input", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("The passwords must match", 403)

        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        x = "Def"
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :passw)", username=username, passw=password)
        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register1.html")

@app.route("/quizoptions", methods=["GET", "POST"])
def quizo():
    """Quiz"""
    if request.method == "GET":
        return render_template("quizoptions.html")
    else:
        if not request.form.get("Operation"):
            return apology("Must select an Operation", 403)
        Operation = request.form.get("Operation")
        db.execute("UPDATE quiz SET op = :o WHERE user_id = :iod",o = Operation, iod=session["user_id"])
        return redirect("/quiz")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "GET":
        number1 = random.randint(100, 300)
        number2 = random.randint(1, 50)
        rows = db.execute("SELECT op FROM quiz WHERE user_id = :id", id = session["user_id"] )
        for row in rows:
            operation = row["op"]
        m = "Multiplication"
        a = "Addition"
        if str(operation) == "Division":
            answer = number1/number2
            s = "/"
        elif str(operation) == m:
            answer = number1*number2
            s = "*"
        elif str(operation) == a:
            answer = number1 + number2
            s = "+"
        else:
            answer = number1-number2
            s = "-"
        return render_template("quiz.html", number1 = number1, number2 = number2,sign=s, ans = answer, op = str(operation))

    else:
        if not request.form.get("ans"):
            return apology("Must enter an input", 403)
        answer = float(request.form.get("an1s"))
        answeruser = round(float(request.form.get("ans")))
        ope = request.form.get("op")

        if answeruser == round(answer):
            db.execute("UPDATE users SET points = points + :o WHERE id = :iod",o = 100, iod=session["user_id"])
            db.execute("UPDATE operation SET point = point + :o WHERE user_id = :iod AND op = :oq",oq = ope, o = 100, iod=session["user_id"])
            flash("Correct Answer")
            return redirect("/quiz")
        else:
            flash("*Sorry, wrong answer")
            return redirect("/quiz")

@app.route("/score", methods=["GET"])
def score():
    rows = db.execute("SELECT points FROM users WHERE id = :id", id = session["user_id"])
    roe = db.execute("SELECT point, op FROM operation WHERE user_id = :id", id = session["user_id"])
    score = rows[0]["points"]
    return render_template("score.html", score=score, rows = roe)
@app.route("/", methods=["GET"])
def go():
    return render_template("index.html")
@app.route("/rank", methods=["GET"])
def rank():
    x = 1
    dicta = []
    rows = db.execute("SELECT username, points FROM users ORDER BY points DESC")
    for row in rows:
        dicta.append(x)
        x += 1
    t = 0
    return render_template("rank.html", rows=rows, di = dicta, t = t)

