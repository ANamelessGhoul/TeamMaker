from flask import Flask, render_template, current_app, abort, request, redirect, url_for,  send_from_directory
from flask_login import login_required, logout_user, login_user, current_user
from login import load_user
import bcrypt
from datetime import datetime

from database import Database
from specs import getRoles, getSpecializations, specsContains

def image_server(filename):
    return send_from_directory("./images", filename)

def home_page():
    return render_template("home.html")

#@login_required
def gamejams_page():
    if request.method == "GET":
        database = Database.getInstance()
        gamejams = database.GetAllGameJams()
        return render_template("gamejams.html", gamejams = sorted(gamejams, key=lambda x: x.startDate, reverse=False))
    else:
        form_jam_ids = request.form.getlist("jam_ids")
        for id in form_jam_ids:
            print(id)
        return redirect(url_for("gamejams_page"))
    
def newjam_page():
    if request.method == "GET":
        current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())
        values = { "data": {"startDate": current_datetime, "endDate": current_datetime}}
        return render_template("newjam.html", values = values, min = current_datetime)
    else:
        valid = validate_newjam_form(request.form)
        if not valid:
            current_datetime = '{date:%Y-%m-%dT%H:%M}'.format(date=datetime.now())
            return render_template("newjam.html", values=request.form, min = current_datetime)
        data = request.form.data
        id = Database.getInstance().AddNewJam(
            name = data['name'],
            theme = data['theme'],
            startDateString = data['startDate'],
            endDateString = data['endDate'],
            about = data['about']
        )
        return redirect(url_for("home_page"))

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

def profile_page(user_id):
    user = Database.getInstance().GetUser(user_id)
    if not user:
        abort(404)
    else:
        return render_template("profile.html", user= user)

@login_required
def my_profile_page():
    user_data = current_user.data
    return render_template("profile.html", user= user_data)


def signup_page():
    if request.method == "GET":
        values = { "data": {"password": ""}}
        return render_template(
            "signup.html", 
            values = values,
            pow = pow,
            options = getSpecializations(),
            contains = specsContains
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

def validate_signup_form(form, options):
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
