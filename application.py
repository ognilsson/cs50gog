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
import string
from flask_mail import Mail, Message


from helpers import apology, login_required, lookup, back_one_day

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure mail
app.config["MAIL_DEFAULT_SENDER"] = "cs50microjournal@gmail.com"
app.config["MAIL_USERNAME"] = "cs50microjournal@gmail.com"
app.config["MAIL_PASSWORD"] = "HMS2020!"
app.config["MAIL_PORT"] = 465
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


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
        id = db.execute("SELECT entry_id from user_scores where user_id = ? and score = ? and day = ? and month = ? and year = ? and hour = ? and minute = ?;",user_id,score,day,month,year,hour,minute)[0]["entry_id"]
        preferences = db.execute("SELECT preference_id from preferences where user_id = ?;", user_id)
        if len(preferences) == 0:
            i=1
            while(i < 6):
                db.execute("Insert into preferences(user_id, preference_id) values(?,?);",user_id,i)
                i += 1
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
    entryID = request.args.get("id")
    userID = session["user_id"]
    print("Activity Entry ID:",entryID)
    if request.method == "POST":
        postedActivities = request.form.getlist("checked-activity")
        print(postedActivities)
        entry=request.form["submit-activity"]
        for activity in postedActivities:
            res = activity.split(",")
            activityID = int(res[0])
            categoryID = int(res[1])
            db.execute("Insert into activity_entry (user_id, activity_id,entry_id,category_id) values(?,?,?,?);",userID,activityID,entry,categoryID)
        return redirect(url_for('questions',id=entry))
    else:
        # user_id = session["user_id"]
        preferences = db.execute("SELECT preference_id from preferences where user_id = ?;", userID)
        activityImagePaths=[]
        activityCategoryTitles=[]
        activityTitles = []
        activities=[]
        activityIds=[]
        for index in range(0,len(preferences)):
            activities.append(db.execute("SELECT category_name,activity_name,activity_id,activities.category_id from activities JOIN categories ON activities.category_id = categories.category_id where categories.category_id=?;",preferences[index]["preference_id"]))
        for outerIndex in range(len(activities)):
            for item in range(0,len(activities[outerIndex])):
                category = activities[outerIndex][item]['category_name']
                if category not in activityCategoryTitles:
                    activityCategoryTitles.append(category)
                activity = activities[outerIndex][item]['activity_name']
                activityTitles.append(activity)
                id = str(activities[outerIndex][item]['activity_id'])+","+str(activities[outerIndex][item]['category_id'])
                activityIds.append(id)
                tmp = "/static/icons/"+category+"/"+activity+".png"
                activityImagePaths.append(tmp)
        length = len(activityImagePaths)
        return render_template("activities.html",len=length,activities=activityImagePaths,activityTitles=activityTitles,categoryTitles=activityCategoryTitles,categories=len(activityCategoryTitles),activityIds=activityIds,entryID=entryID)

#Questions Method
@app.route("/questions", methods=["GET", "POST"])
@login_required
def questions():
    id = request.args.get("id")
    print("ENTRY ID - QUESTIONS:",id)
    if request.method == "POST":
        answer1 = request.form.get("a1")
        answer2 = request.form.get("a2")
        entry = request.form["submit-questions"]
        db.execute("UPDATE user_scores SET answer1=? , answer2 = ? WHERE entry_id = ?;",answer1, answer2,entry)
        return redirect("/stats")
    else:
        length = len(db.execute("SELECT * from questions;"))
        rand1 = random.randint(1,length)
        rand2 = random.randint(1,length)
        while( rand1 == rand2 ):
            rand2 = random.randint(1,length)
        q1 = db.execute("SELECT question from questions where question_id=?;",rand1)[0]["question"]
        q2 = db.execute("SELECT question from questions where question_id=?;",rand2)[0]["question"]
        print(q1,"\n",q2)
        return render_template("questions.html",q1=q1,q2=q2,entryID=id)

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
            y.append(float(round(avg_score[0]['AVG(score)'],2)))
        except TypeError:
            y.append(0)
        # Moving one day back in time -- move to helpers
        month, day, year = back_one_day(month, day, year)

    # Reversing the lists to get them in the right order
    x.reverse()
    y.reverse()

    # Setting the title
    if scope == 7:
        title = 'Happiness over the last Week'
    elif scope > 27 and scope < 32:
        title = 'Happiness over the last Month'
    else:
        title = 'Happiness over the last Year'


    ### ACTIVITIES STATS
    activity_count = {}
    x2, y2 = [], []
    user_activities = db.execute("SELECT activity_id FROM activity_entry WHERE user_id = ?", session["user_id"])

    for row in user_activities:
        if row["activity_id"] in activity_count:
            activity_count[row["activity_id"]] += 1
        else:
            activity_count[row["activity_id"]] = 1

    # From https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    activity_count = dict(sorted(activity_count.items(), key=lambda item: item[1]))

    # Trading activity id for activity names
    all_activities = db.execute("SELECT activity_id, activity_name FROM activities")
    for key in activity_count:
        for row in all_activities:
            if key == row["activity_id"]:
                x2.append(row["activity_name"])
                y2.append(int(activity_count[key]))

    # Query for activity id's and their respective scores for that entry
    activity_scores = db.execute("SELECT activity_id, score FROM activity_entry JOIN user_scores ON activity_entry.entry_id = user_scores.entry_id WHERE activity_entry.user_id = ?;", session["user_id"])

    # Calculate the average score when an activity is entered
    count = {}
    totals = {}
    for row in activity_scores:
        if row["activity_id"] in count:
            count[row["activity_id"]] += 1
            totals[row["activity_id"]] += int(row["score"])
        else:
            count[row["activity_id"]] = 1
            totals[row["activity_id"]] = int(row["score"])

    # Calculate the average
    for key in totals:
        totals[key] = round(totals[key] / count[key], 2)

    # Sort dictionary by their average scores
    # From https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    totals = dict(sorted(totals.items(), key=lambda item: item[1]))

    # Separate axis and find activity names
    x_tmp = totals.keys()
    x_tmp_2 = []
    for i in x_tmp:
        for row in all_activities:
            if i == row["activity_id"]:
                x_tmp_2.append(row["activity_name"])

    limit = 3
    x_top = x_tmp_2[-limit:]
    x_bottom = x_tmp_2[:limit]

    return render_template("stats.html", title=title, labels=x, values=y, activities=x2, freq=y2, best=x_top, worst=x_bottom)



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
    userID = session['user_id']
    if request.method == "POST":
        preferences = request.form.getlist('cb')
        for preference in preferences:
            p_id = preference.replace('/','')
            integerId = int(p_id)
            db.execute("Insert into preferences (user_id, preference_id) values(?,?);",userID,integerId)
        return redirect("/")

    else:
        if request.args.get("hasNoPreferences"):
            return render_template("preferences.html",hasNoPreferences=True,id=request.args.get(id))
        db.execute("DELETE FROM preferences WHERE user_id=?",userID)
        return render_template("preferences.html")


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
        length = 8
        letters = string.ascii_lowercase
        new_password = ''.join(random.choice(letters) for i in range(length))

        # Send email to user with new password
        email = request.form.get("email")

        if len(db.execute("SELECT * FROM users WHERE email = ?", email)) != 1:
            return apology("email does not match or records", 403)

        db.execute("UPDATE users SET hash = ? WHERE email = ?", generate_password_hash(new_password), email)
        m_body = "Your new password is: " + new_password
        message = Message(subject="New Password", recipients=[email])
        message.body = m_body
        print(m_body)
        mail.send(message)
        return redirect("/login")

@app.route("/habits", methods=["GET", "POST"])
@login_required
def habits():
    user_id = session["user_id"]
    check = db.execute("Select activity_id,progress,day,month,year from habits where user_id=?;",user_id)
    activities = db.execute("Select activity_name,activity_id from activities;")
    time  = datetime.datetime.now().astimezone()
    currentDay = time.strftime("%d")
    currentMonth = time.strftime("%m")
    currentYear = time.strftime("%Y")
    if request.method == "POST":
        buttonValue = request.form["btn-habit"]
        selectedActivity = request.form.get("selected-activity")
        currentlySelectedActivity = db.execute("SELECT activity_id from activities where activity_name = ?;",selectedActivity)
        if buttonValue == "Commit":
            if len(currentlySelectedActivity) == 0:
                missingActivity="Please select an activity from the list of activities!"
                return render_template("habits.html", activities=activities , hasActiveHabit=False,hasNotSelectedActivity=True,alertMessage=missingActivity)
            # if len(check) == 1:
            #     failureAlert = "Please finish developing on your current habit !"
            #     return render_template("habits.html",activities=activities,hasActiveHabit=True,alertMessage=failureAlert,isFailure=True)
            # print(currentlySelectedActivity)
            db.execute("INSERT into habits(user_id,activity_id,progress,day,month,year) values(?,?,?,?,?,?);",user_id,currentlySelectedActivity[0]["activity_id"],1,currentDay,currentMonth,currentYear)
            currentHabit = db.execute("Select activity_name from activities where activity_id =?",currentlySelectedActivity[0]["activity_id"])
            progress=1
            currentProgress = round(((progress / 18)*100),2)
            updateMessage = "Habit progress has been recorded. Come back tomorrow to log progress update!"
            return render_template("habits.html",activities=activities,hasActiveHabit=True,formattedProgress=currentProgress,progress=progress,currentHabit=currentHabit[0]["activity_name"],isReadyToUpdateHabit=False,alertMessaage=updateMessage,hasBeenUpdated=True)
        elif buttonValue == "Update":
            progress = int(check[0]["progress"])
            print(progress)
            if progress+1 == 18:
               successMessage = "Congratulations on developing a new habit!"
               db.execute("DELETE from habits where user_id = ?;", user_id)
               return render_template("habits.html",activities=activities,hasGainedHabit = True,hasActiveHabit=False, alertMessage = successMessage)
            else:
                progress = progress + 1
                db.execute("UPDATE habits SET progress=?, day=?, month=?, year=? WHERE activity_id=? and user_id=?;",progress,int(currentDay),int(currentMonth),int(currentYear),check[0]["activity_id"], user_id)
                # return render_template("habits.html", )
                updateMessage = "Habit progress has been recorded. Come back tomorrow to log progress update!"
                return redirect(url_for('habits',hasActiveHabit=True,isReadyToUpdateHabit=False,hasBeenUpdated=True,alertMessaage=updateMessage))
        else:
            db.execute("DELETE from habits where user_id=?;",user_id)
            deleteMessage = "Your current habit has been deleted!"
            return render_template("habits.html",activities=activities,hasActiveHabit=False,alertMessage=deleteMessage,hasDeletedHabit=True)
    else:
        # print("Length: ",len(check))
        if len(check) == 1:
            habitID = check[0]["activity_id"]
            currentHabit = db.execute("Select activity_name from activities where activity_id =?",habitID)
            progress = check[0]["progress"]
            currentProgress = round(((progress / 18)*100),2)
            if int(currentDay) == check[0]["day"] and int(currentMonth) == check[0]["month"] and int(currentYear) == check[0]["year"]:
                updateMessage = "Habit progress has already been recorded. Come back tomorrow to log progress update!"
                return render_template("habits.html", activities=activities , hasActiveHabit=True,formattedProgress=currentProgress,progress=progress,currentHabit=currentHabit[0]["activity_name"],isReadyToUpdateHabit=False,hasBeenUpdated=True,alertMessaage=updateMessage)
            return render_template("habits.html", activities=activities , hasActiveHabit=True,formattedProgress=currentProgress,progress=progress,currentHabit=currentHabit[0]["activity_name"],isReadyToUpdateHabit=True)
        else:
            return render_template("habits.html", activities=activities , hasActiveHabit=False)
    # Progress Circle Reference: https://jsfiddle.net/mvc6jkd2/


@app.route("/social", methods=["GET", "POST"])
@login_required
def social():
    if request.method == "POST":
        return render_template("social.html")
    else:
        return render_template("social.html")
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
