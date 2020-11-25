import os
import datetime
import re
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd

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


# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///journal.db")

#A global variable to save the transaction type in, need to display the alert in the index page
alertMessage = ""


@app.route("/")
@login_required
def index():
    # user_id = session["user_id"]
    # shares = db.execute("Select * From user_stocks WHERE user_id=?",user_id)
    # sharesToSend = []
    # totals = float(0)
    # for share in shares:
    #     dict = {'symbol': share['stock_symbol']}
    #     dict['name'] = share['stock_name']
    #     currentShares = share['shares']
    #     sharePriceLookUp = lookup(share['stock_symbol'])
    #     tmp = sharePriceLookUp.get("price")
    #     dict['shares'] = currentShares
    #     dict['price'] = usd(tmp)
    #     totals += tmp * currentShares
    #     dict['total'] = usd(tmp * currentShares)
    #     sharesToSend.append(dict)

    # print(sharesToSend)
    # usercashQuery = db.execute("Select cash from users WHERE id=?",user_id)
    # currentCash = usercashQuery[0].get('cash')
    # currentFormatted = usd(currentCash)
    # totalCash =  currentCash + totals
    # totalCashFormatted = usd(totalCash)
    # global alertMessage
    # message = alertMessage
    # # Reset alertMessage
    # alertMessage = ""
    # return render_template("index.html",len = len(sharesToSend),stockPrices = sharesToSend,leftOver=currentFormatted,total=totalCashFormatted,alert=message)
    return render_template("index.html")


@app.route("/new_entries", methods=["GET", "POST"])
@login_required
def new_entries():
    time  = datetime.datetime.now().astimezone()
    if request.method == "POST":
        user_id = session["user_id"]
        print("Result")
        score = request.form["btn-emotion"]

        day = time.strftime("%d")
        month = time.strftime("%m")
        year = time.strftime("%Y")
        hour = time.strftime("%H")
        minute = time.strftime("%M")
        db.execute("Insert into user_scores (user_id, score,day,month,year,hour,minute) values(?,?,?,?,?,?,?)",user_id,score,day,month,year,hour,minute)
        #  if request.form["btn-emotion"] == 1:
        #     print("Terrible")
        #  print(entry)
        #  data = {1,2,3,4,5}
        #  length = "FIVE"

        return redirect("/activities")
    else:
        user_id = session["user_id"]
        entry = request.form.get("btn-emotion")
        data = [1,2,3,4,5]
        length = len(data)
        timeOfEntry = time.strftime("%a, %b %d, %I:%M %p")
        return render_template("new_entries.html",len=length,data=data,timeOfEntry = timeOfEntry)

#Activties Method
@app.route("/activities", methods=["GET", "POST"])
@login_required
def activities():
    if request.method == "POST":
        return redirect("/questions")
    else:
        return render_template("activities.html")

#Questions Method
@app.route("/questions", methods=["GET", "POST"])
@login_required
def questions():
    if request.method == "POST":
        return redirect("/history")
    else:
        return render_template("questions.html")

#History Method
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("history.html")

@app.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    user_id = session["user_id"]
    # rows = db.execute("SELECT score,day,month,year FROM user_scores where user_id=? and day=23;",user_id)
    days = 0
    year = 2020
    points = [{}]
    time  = datetime.datetime.now().astimezone()
    currentyear = time.strftime("%Y")
    for year in range(year, int(currentyear)+1):
        for month in range(1,12):
            # Check the month
            if(month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12):
                days = 31
            elif month == 2 and year % 4 ==0 :
                days = 29
            elif month == 2:
                days = 28
            else:
                days = 30
            for day in range(1, days):
                average = db.execute("Select AVG(score) from user_scores where user_id=? and day=? and month=? and year=?" , user_id, day, month, year)
                if not average[0]['AVG(score)'] is None:
                    dict = {}
                    dict['avg'] = average
                    dict['day'] = day
                    points.append(dict)
                else:
                    continue
    print(points)




    return render_template("stats.html")

@app.route("/entries", methods=["GET","POST"])
@login_required
def entries():
    if request.method == "POST":
            return redirect(request.form["page-btn"])
    else:
        return render_template("entries.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

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


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        result = lookup(request.form.get("symbol"))
        if result is None:
            return apology("Invalid Symbol", 400)
        else:
            companyName = result["name"]
            symbolText = result["symbol"]
            price = usd(result["price"])
            return render_template("quote.html",name=companyName,symbol=symbolText,stockPrice=price,notSearched=False)
    else:
        return render_template("quote.html",notSearched=True)

@app.route("/change-password", methods=["GET", "POST"])
def changePassword():
    if request.method == "POST":
        oldPassword = request.form.get("oldPassword")
        newPassword = request.form.get("newPassword")
        confirmNewPassword = request.form.get("confirmNewPassword")
        rows = db.execute("SELECT * FROM users WHERE id = ?",session["user_id"] )
        # Ensure old password is correct
        if not oldPassword:
            return apology("Missing Old Password", 403)
        elif len(rows) != 1 or not check_password_hash(rows[0]["hash"], oldPassword):
            return apology("Incorrect Password", 403)
        elif not newPassword:
            return apology("Missing New Password", 403)
        elif not confirmNewPassword:
            return apology("Missing Confirm New Password", 403)
         #Special feature 1: Ensure password is no less than 8 characters
        elif len(newPassword) < 8:
            return apology("New Password must be at least 8 characters")
        elif newPassword != confirmNewPassword:
            return apology("New Passwords must match", 403)
        else:
            newPasswordHash = generate_password_hash(newPassword)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", newPasswordHash,session["user_id"])
        sucessAlert = "Password Changed Successfully!"
        return render_template("change-password.html",isChanged=True,alert=sucessAlert)
    else:
        return render_template("change-password.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure email was submitted
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not email:
            return apology("must provide email", 400)

         # Query database for email
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        #  Ensure email is unique
        if len(rows) == 1:
            return apology("email already exists", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        #Special feature 1: Ensure password is no less than 8 characters
        if( len(password) < 8):
            return apology("Password must be at least 8 characters")

        # Ensure password is confirmed
        elif not confirmation:
            return apology("must confirm password", 400)

        #Ensure confirmed password matces password
        if confirmation != password:
            return apology("paswords must match", 400)


        # Register User into the database

        passwordHash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (email, hash) VALUES(?, ?)", email, passwordHash)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # Get current timestomp, Reference: https://timestamp.online/article/how-to-convert-timestamp-to-datetime-in-python
    time  = datetime.datetime.now().astimezone()
    formattedTS = time.strftime("%Y-%m-%d %H:%M:%S")
    """Sell shares of stock"""
    symbol = request.form.get("symbol")
    if request.method == "POST":
        user_id = session["user_id"]
        result = lookup(symbol)
        shares = request.form.get("shares")
        if not symbol:
            return apology("Missing Symbol",400)
        elif not shares:
            return apology("Missing Shares",400)
        elif int(shares) <= 0:
            return apology("Shares Must Be Positive",400)
        else:
            numberOfSharesAvailable = db.execute("Select shares from user_stocks where user_id=? and stock_symbol=?;",session["user_id"],symbol)
            currentShares = numberOfSharesAvailable[0].get("shares")
            newShares = int(currentShares) - int(shares)
            currentUserCashDict = db.execute("SELECT cash from users where id=?",user_id)
            userCash = currentUserCashDict[0].get("cash")
            stockPrice = result["price"]
            totalPrice = float(shares) * float(stockPrice)
            sum = float(userCash) + totalPrice
            if int(shares) > currentShares:
                return apology("Too Many Shares",400)
            if int(newShares) == 0:
                db.execute("DELETE FROM user_stocks WHERE user_id=? AND stock_symbol = ?", user_id,symbol)
            else:
                db.execute("UPDATE user_stocks SET shares = ? WHERE user_id = ? AND stock_symbol = ?", newShares, user_id,symbol)
        db.execute("UPDATE users SET cash = ? WHERE id = ?",sum,user_id)
        db.execute("INSERT INTO transactions (transaction_id, symbol, shares, price, timestamp) VALUES(?,?,?,?,?)",user_id, symbol, - int(shares), totalPrice, formattedTS)
        global alertMessage
        alertMessage = "Sold!"
        return redirect("/")

    else:
        symbols = db.execute("Select stock_symbol from user_stocks where user_id=?",session["user_id"])
        symbolsList = []
        for symbol in symbols:
            symbolsList.append(symbol['stock_symbol'])
        return render_template("sell.html",len=len(symbolsList),symbols=symbolsList)




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
