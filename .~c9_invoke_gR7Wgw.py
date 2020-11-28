import os
import datetime
import re
import random
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session,  url_for, Response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, back_one_day

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
    user_id = session["user_id"]
    # activities = [["Exercise", "Eat Healthy", "Drink Water" , "Yoga", "Sleep Early"],
    # ["Give", "Meditate", "Music" , "Podcast", "Pray", "Relax", "Walk"],["Gaming", "Movies", "Reading" , "Woodworking"],["Date", "Family", "Friends" , "Party", "Video Chat"]
    # ,["Cleaning", "Coding", "Exam" , "Laundry", "Meeting", "Shopping", "Study"]]
    # for item in range(0,len(activities)):
    #     for items in activities[item]:
    #         db.execute("INSERT into activities(activity_name, category_id) values(?,?);", items,item+1)
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
        id = db.execute("SELECT entry_id from user_scores where user_id = ? and score = ? and day = ? and month = ? and year = ? and hour = ? and minute = ?;",user_id,score,day,month,year,hour,minute)

        return redirect(url_for('activities',id=id))
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
    id = request.args.get("id")
    print("ID:",id)
    if request.method == "POST":
        postedActivities = request.form.getlist("checked-activity")
        print("Checked Activities:",postedActivities)
        return redirect("/questions")
    else:
        user_id = session["user_id"]
        preferences = db.execute("SELECT preference_id from preferences where user_id = ?;", user_id)
        print(preferences)
        activityImagePaths=[]
        activityCategoryTitles=[]
        activityTitles = []
        activities=[]
        activityIds=[]
        for index in range(0,len(preferences)):
            activities.append(db.execute("SELECT category_name,activity_name,activity_id from activities JOIN categories ON activities.category_id = categories.category_id where categories.category_id=?;",preferences[index]["preference_id"]))
        for outerIndex in range(len(activities)):
            for item in range(0,len(activities[outerIndex])):
                # print(outerIndex)
                category = activities[outerIndex][item]['category_name']
                if category not in activityCategoryTitles:
                    activityCategoryTitles.append(category)
                activity = activities[outerIndex][item]['activity_name']
                activityTitles.append(activity)
                id = activities[outerIndex][item]['activity_id']
                activityIds.append(id)
                # print(category,activity)
                tmp = "/static/icons/"+category+"/"+activity+".png"
                activityImagePaths.append(tmp)
        # print(activityImagePaths)
        length = len(activityImagePaths)
        return render_template("activities.html",len=length,activities=activityImagePaths,activityTitles=activityTitles,categoryTitles=activityCategoryTitles,categories=len(activityCategoryTitles),activityIds=activityIds)

#Questions Method
@app.route("/questions", methods=["GET", "POST"])
@login_required
def questions():
    if request.method == "POST":
        answer1 = request.form.get("a1")
        answer2 = request.form.get("a2")
        db.execute("INSERT into user_scores(answer1, answer2) values(?,?);",answer1 )
        return redirect("/history")
    else:
        length = len(db.execute("SELECT * from questions;"))
        rand1 = random.randint(1,length)
        rand2 = random.randint(1,length)
        while( rand1 == rand2 ):
            rand2 = random.randint(1,length)
        q1 = db.execute("SELECT question from questions where question_id=?;",rand1)[0]["question"]
        q2 = db.execute("SELECT question from questions where question_id=?;",rand2)[0]["question"]
        print(q1,"\n",q2)
        return render_template("questions.html",q1=q1,q2=q2)

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
    """
    Displays the perosnal statistics for the user
    """
    user_id = session["user_id"]
    time  = datetime.datetime.now().astimezone()
    day = int(time.strftime("%-d"))
    month = int(time.strftime("%-m"))
    year = int(time.strftime("%Y"))

    try:
        scope = int(request.args.get("range"))
    except TypeError:
        scope = 7

    print(scope, type(scope))
    # Adjusting for difference in days in a month (Getting scores up until the same date a month before)
    if scope == 30:
        if month == 3:
            scope = 28
        elif (month == 1 or month == 2 or month == 4 or month == 6 or month == 8 or month == 9 or month == 11):
            scope = 31

    x = []
    y = []

    # Find the average scores of the last 7 days individually and append them to x, and y
    for i in range(scope):
        avg_score = db.execute("SELECT AVG(score) FROM user_scores WHERE user_id = ? AND Month = ? AND Day = ? AND Year = ?", session["user_id"], month, day, year)
        formatted_date = f"{month}-{day}-{year}"
        x.append(formatted_date)
        try:
            y.append(float(avg_score[0]['AVG(score)']))
        except TypeError:
            y.append(0)

        # Moving one day back in time -- move to helpers
        month, day, year = back_one_day(month, day, year)

    # Reversing the lists to get them in the right order
    x.reverse()
    y.reverse()
    #print(x)
    #print(y)

    # Setting the title and adjusting labels
    if scope == 7:
        title = 'Happiness over the last Week'
    elif scope > 27 and scope < 32:
        title = 'Happiness over the last Month'
    else:
        title = 'Happiness over the last Year'
        count = 0
        # Only keeping every 10th label for displaying purposes
        for i in range(len(x)):
            count += 1
            if count == 10:
                count = 0
                continue
            else:
                x[i] = ''

    return render_template("stats.html", title=title, max=5, labels=x, values=y)

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

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))


        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        if rows[0]['firstTime'] == 1:
            db.execute("UPDATE users SET firstTime = 0 WHERE id = ?;", rows[0]["id"])
            return redirect("/preferences")

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

         # Query dataxbase for email
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
        db.execute("INSERT INTO users (email, hash, firstTime) VALUES(?, ?, ?);", email, passwordHash, 1)

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    #THIS LINE DOESNT WORK
    if request.method == "POST":
        preferences = request.form.getlist('cb')
        for preference in preferences:
            p_id = preference.replace('/','')
            integerId = int(p_id)
            userID = session['user_id']
            db.execute("Insert into preferences (user_id, preference_id) values(?,?);",userID,integerId)
        return render_template("index.html")

    else:
        return render_template("preferences.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
