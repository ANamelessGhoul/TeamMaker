from flask import Flask, render_template, current_app, abort, request, redirect, url_for,  send_from_directory
from flask_login import login_required, logout_user, login_user, current_user
from login import load_user
import bcrypt
from datetime import datetime

from database import Database
from specs import getRoles, getSpecializations, specsContains

def home_page():
    return render_template("home.html")

def image_server(filename):
    return send_from_directory("./images", filename)

@login_required
def chat_page(chat_id):
    user_data = current_user.data
    if not Database.getInstance().IsUserInChatroom(user_data.id, chat_id):
        abort(403)
    past_messages = Database.getInstance().GetMessages(chat_id)
    return render_template("messaging.html", room_id = chat_id, past_messages=past_messages, current_user_id=user_data.id)

@login_required
def mychats_page():
    user_data = current_user.data
    team_chats = Database.getInstance().GetTeamChatRooms(user_data.id)
    private_chats = Database.getInstance().GetPrivateChatRooms(user_data.id)
    return render_template("mychats.html", team_chats = team_chats, private_chats=private_chats)

def start_chat():
    print(request.form)
    other_user = request.form.get('user', None)
    # TODO: Make sure private chat does not already exist
    if other_user is None or other_user == current_user.get_id():
        abort(404)

    db =  Database.getInstance()
    chat_id = db.CreateChatroom()
    db.JoinChatroom(current_user.get_id(), chat_id)
    db.JoinChatroom(other_user, chat_id)
    
    return redirect(url_for("chat_page", chat_id=chat_id))

def gamejams_page(status):
    if request.method == "GET":
        database = Database.getInstance()
        if status == "Active":
            gamejams = database.GetActiveGameJams()
        elif status == "Ongoing":
            gamejams = database.GetOngoingGameJams()
        elif status == "Past":
            gamejams = database.GetPastGameJams()
        elif status == "Upcoming":
            gamejams = database.GetUpcomingGameJams()
        elif status == "All":
            gamejams = database.GetAllGameJams()
        else:
            abort(404)

        return render_template("gamejams.html", now = datetime.now(), gamejams = sorted(gamejams, key=lambda x: x.startDate, reverse=False))
    else:
        return redirect(url_for("gamejams_page", status = request.form.get("status","ALL")))

def gamejams_redirect():
    return redirect(url_for("gamejams_page", status = 'Active'))

@login_required
def jam_page(jam_id):
    if request.method == "GET":
        jam = Database.getInstance().GetGameJam(jam_id)
        if not jam:
            abort(404)
        else:
            attending = Database.getInstance().GetUsersAttending(jam_id)
            current_user_id = current_user.data.id
            user_attending = next((x for x in attending if x.id == current_user_id), None)
            return render_template(
                "jam_info.html",
                jam = jam, 
                now = datetime.now(), 
                attending = attending, 
                current_user_attending = user_attending
            )
    elif request.method == "POST":
        if request.form.get('delete', None) is not None:
            Database.getInstance().DeleteGameJam(jam_id)
            return redirect(url_for("myjams_page"))
        elif request.form.get('join', None) is not None:
            Database.getInstance().UserAttendJam(current_user.data.id, jam_id)
            #TODO: Redirect to teams page
            return redirect(url_for("jam_page", jam_id = jam_id))

        
        return redirect(url_for("jam_page", jam_id = jam_id))

def render_jam_page(values, current_datetime, edit_mode = False):
    return render_template("newjam.html", values = values, min = current_datetime, edit_mode = edit_mode)

@login_required
def newjam_page():
    if request.method == "GET":
        current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())
        values = { "data": {"startDate": current_datetime, "endDate": current_datetime}}
        return render_jam_page(values, current_datetime)
    else:
        valid = validate_newjam_form(request.form)
        if not valid:
            current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())
            return render_jam_page(request.form, current_datetime)
        data = request.form.data
        id = Database.getInstance().AddNewJam(
            name = data['name'],
            theme = data['theme'],
            startDateString = data['startDate'],
            endDateString = data['endDate'],
            about = data['about']
        )
        Database.getInstance().UserAttendJam(current_user.data.id, id, True)
        return redirect(url_for("jam_page", jam_id=id))

@login_required
def editjam_page(jam_id):
    if request.method == "GET":
        jam = Database.getInstance().GetGameJam(jam_id)
        if jam is None:
            abort(404)
        current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())

        values = { 
            "data": {
                "startDate": '{date:%Y-%m-%dT%H:%M}'.format(date=jam.startDate),
                "endDate": '{date:%Y-%m-%dT%H:%M}'.format(date=jam.endDate),
                "name": jam.name,
                "theme": jam.theme,
                "about": jam.about
            }
        }
        return render_jam_page(values, current_datetime, edit_mode = True)
    else:
        valid = validate_newjam_form(request.form)
        if not valid:
            current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())
            return render_jam_page(request.form, current_datetime, edit_mode = True)
        data = request.form.data
        Database.getInstance().UpdateJam(
            jam_id = jam_id,
            name = data['name'],
            theme = data['theme'],
            startDateString = data['startDate'],
            endDateString = data['endDate'],
            about = data['about']
        )
        return redirect(url_for("jam_page", jam_id=jam_id))

def validate_newjam_form(form):
    form.data = {}
    form.errors = {}

    #validate dates
    startDateString = form.get("startDate", "2021-01-01T00:00")
    startDate = datetime.strptime(startDateString, '%Y-%m-%dT%H:%M')
    form.data['startDate'] = startDateString

    endDateString = form.get("endDate", "2021-01-01T00:00")
    endDate = datetime.strptime(endDateString, '%Y-%m-%dT%H:%M')
    form.data['endDate'] = endDateString

    if endDate <= startDate:
        form.errors['endDate'] = "End date must be after start date!"

    # validate jam name
    jam_name = form.get("name", "").strip()
    if len(jam_name) == 0:
        form.errors["name"] = "Jam name can not be blank."
    elif len(jam_name) > 255:
        form.errors["name"] = "Jam name is too long."
    else:
        form.data["name"] = jam_name

    # validate jam theme
    theme = form.get("theme", "").strip()
    if len(theme) == 0:
        form.errors["theme"] = "Theme can not be blank."
    elif len(theme) > 255:
        form.errors["theme"] = "Theme is too long."
    else:
        form.data["theme"] = theme

    form.data["about"] = form.get("about", "")

    return len(form.errors) == 0

@login_required
def myjams_page():
    gamejams = Database.getInstance().GetGameJamsAttending(current_user.get_id())
    return render_template(
        "mygamejams.html",
        now = datetime.now(),
        gamejams = sorted(gamejams['attending'], key=lambda x: x.startDate, reverse=False),
        moderating = sorted(gamejams['moderating'], key=lambda x: x.startDate, reverse=False)
    )


def profile_page(user_id):
    viewed_user = Database.getInstance().GetUser(user_id)
    if not viewed_user:
        abort(404)
    else:
        return render_template("profile.html", user= viewed_user, other_user = True)

@login_required
def my_profile_page():
    user_data = current_user.data
    if request.method == "GET":
        return render_template("profile.html", user= user_data , other_user = False)
    else:
        Database.getInstance().DeleteUser(user_data.id)
        return redirect(url_for('home_page'))

@login_required
def editprofile_page():
    user_data = current_user.data
    if request.method == "GET":
        names = user_data.name.split(' ')
        first_name = ' '.join(names[:-1])
        last_name = names[-1]
        values = { 
            "data":{
                "firstname": first_name,
                "lastname": last_name,
                "about": user_data.about, 
                "primary": user_data.primary_spec_raw, 
                "secondary": user_data.secondary_specs_raw, 
                "experience": user_data.experience, 
            }
        }
        return render_template(
            "signup.html", 
            values = values,
            pow = pow,
            options = getSpecializations(),
            contains = specsContains,
            edit_mode = True
        )
    else:
        options = getSpecializations()
        valid = validate_signup_form(request.form, options, True)
        if not valid:
            return render_template(
                "signup.html",
                values=request.form,
                pow = pow,
                options = options,
                contains = specsContains
            )
        
        data = request.form.data
        Database.getInstance().UpdateUser(
            user_id = user_data.id,
            first_name = data["firstname"],
            last_name = data["lastname"],
            about = data["about"], 
            primary_spec = data["primary"], 
            secondary_spec = data["secondary"], 
            experience = data["experience"]
        )
        return redirect(url_for("my_profile_page"))

def signup_page():
    if request.method == "GET":
        values = { "data": {"password": ""}}
        return render_template(
            "signup.html", 
            values = values,
            pow = pow,
            options = getSpecializations(),
            contains = specsContains,
            edit_mode = False
        )
    else:
        options = getSpecializations()
        valid = validate_signup_form(request.form, options)
        if not valid:
            return render_template(
                "signup.html",
                values=request.form,
                pow = pow,
                options = options,
                contains = specsContains
            )
        
        Database.getInstance().AddNewUser(
            email = request.form.data["email"],
            first_name = request.form.data["firstname"],
            last_name = request.form.data["lastname"],
            about = request.form.data["about"], 
            primary_spec = request.form.data["primary"], 
            secondary_spec = request.form.data["secondary"], 
            experience = request.form.data["experience"], 
            password = request.form.data["password"]
        )
        return redirect(url_for("home_page"))

def validate_signup_form(form, options, edit_mode = False):
    form.data = {}
    form.errors = {}

    # validate first name
    first_name = form.get("firstname", "").strip()
    if len(first_name) == 0:
        form.errors["firstname"] = "First name can not be blank."
    elif len(first_name) > 127:
        form.errors["firstname"] = "First name is too long."
    else:
        form.data["firstname"] = first_name

    # validate last name
    last_name = form.get("lastname", "").strip()
    if len(last_name) == 0:
        form.errors["lastname"] = "Last name can not be blank."
    elif len(last_name) > 127:
        form.errors["lastname"] = "Last name is too long."
    else:
        form.data["lastname"] = last_name

    if not edit_mode:
        # validate email
        email = form.get("email", "").strip()
        if len(email) == 0:
            form.errors["email"] = "Email can not be blank."
        elif Database.getInstance().GetUser(email, field = 'email'):
            form.errors["email"] = "Email already in use."
        else:
            form.data["email"] = email

        # validate password
        password = form.get("password", "")
        if len(password) == 0:
            form.errors["password"] = "Password can not be blank."
        elif False:
            # TODO:validate password
            pass
        else:
            form.data["password"] = password


    primary_spec = int(form.get("primary", -1))
    if primary_spec < 0:
        form.errors["primary"] = "You must choose a primary specialization."
    else:
        form.data["primary"] = primary_spec

    secondary_spec = 0
    for option in options:
        secondary_spec += int(form.get(option, 0))
    form.data["secondary"] = secondary_spec


    about = form.get("about", "").strip()
    if len(about) == 0:
        form.errors["about"] = "About can not be blank."
    else:
        form.data["about"] = about

    experience = form.get("experience", "").strip()
    if len(experience) == 0:
        form.errors["experience"] = "Experience can not be blank."
    else:
        form.data["experience"] = experience

    return len(form.errors) == 0

def login_page():
    if request.method == "GET":
        values = { "data": {"password": ""}}
        return render_template(
            "login.html", 
            values = values
        )
    else:
        valid = validate_login_form(request.form)
        if not valid:
            return render_template(
                "login.html",
                values=request.form,
            )
        login_user(load_user(request.form.data["user"].id))
        return redirect(url_for("home_page"))

def validate_login_form(form):
    form.data = {}
    form.errors = {}

    email = form.get("email", "").strip()
    if len(email) == 0:
        form.errors["email"] = "Email can not be blank."
        return False

    user = Database.getInstance().GetUser(email, field = 'email')
    form.data["user"] = user
    if user is None :
        form.data["email"] = email
        form.errors["email"] = "Email is not registered"
        return False
    
    form.data["email"] = email

    password = form.get("password", "")
    if len(password) == 0:
        form.errors["password"] = "Password can not be blank"
        return False
    if not Database.getInstance().ValidatePassword(email, password):
        form.errors["password"] = "Password is incorrect"
        return False
    
    form.data["password"] = password

    return len(form.errors) == 0

@login_required
def logout_page():
    logout_user()
    return redirect(url_for("home_page"))
