from flask import Flask, render_template, current_app, abort, request, redirect, url_for,  send_from_directory
from flask_login import login_required, logout_user, login_user
from login import load_user
import bcrypt

from datetime import datetime
from movie import Movie

from database import Database
import operator

def image_server(filename):
    return send_from_directory("./images", filename)

def home_page():
    today = datetime.today()
    day_name = today.strftime("%A")
    return render_template("home.html", day = day_name)

#@login_required
def gamejams_page():
    if request.method == "GET":
        database = Database.getInstance()
        gamejams = database.GetAllGameJams()
        return render_template("gamejams.html", gamejams = sorted(gamejams, key=lambda x: x.startDate, reverse=True))
    else:
        form_jam_ids = request.form.getlist("jam_ids")
        for id in form_jam_ids:
            print(id)
        return redirect(url_for("gamejams_page"))

def movie_page(movie_key):
    db = current_app.config["db"]
    movie = db.get_movie(movie_key)
    if movie is None:
        abort(404)
    return render_template("movie.html", movie = movie)

def movie_add_page():
    if request.method == "GET":
        values = { "data": {"title": "", "year": ""}}
        return render_template(
            "movie_edit.html", 
            min_year=1887, 
            max_year=datetime.now().year, 
            values = values
        )
    else:
        valid = validate_movie_form(request.form)
        if not valid:
            return render_template(
                "movie_edit.html",
                min_year=1887,
                max_year=datetime.now().year,
                values=request.form,
            )
        title = request.form.data["title"]
        year = request.form.data["year"]
        movie = Movie(title, year=year)
        db = current_app.config["db"]
        movie_key = db.add_movie(movie)
        return redirect(url_for("movie_page", movie_key=movie_key))

def validate_movie_form(form):
    form.data = {}
    form.errors = {}

    form_title = form.get("title", "").strip()
    if len(form_title) == 0:
        form.errors["title"] = "Title can not be blank."
    else:
        form.data["title"] = form_title

    form_year = form.get("year")
    if not form_year:
        form.data["year"] = None
    elif not form_year.isdigit():
        form.errors["year"] = "Year must consist of digits only."
    else:
        year = int(form_year)
        if (year < 1887) or (year > datetime.now().year):
            form.errors["year"] = "Year not in valid range."
        else:
            form.data["year"] = year

    return len(form.errors) == 0

def contains (a, b):
    return (a & (1 << b)) != 0

def signup_page():
    options = ['Game Design', 'Programming','2D Art', '3D Art', 'Narrative Design', 'Music', 'Sound']
    if request.method == "GET":
        values = { "data": {"name": "", "password": ""}}
        return render_template(
            "signup.html", 
            values = values,
            pow = pow,
            options = options,
            contains = contains
        )
    else:
        valid = validate_signup_form(request.form, options)
        if not valid:
            return render_template(
                "signup.html",
                values=request.form,
                pow = pow,
                options = options,
                contains = contains
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
        if not contains(secondary_spec, primary_spec):
            secondary_spec += int(form.get(option, 0))
    form.data["secondary"] = secondary_spec
    
    print('Start Values:')
    print(primary_spec)
    print(secondary_spec)
    print('End Values.')

    about = form.get("about", "")
    if len(about) == 0:
        form.errors["about"] = "About can not be blank."
    else:
        form.data["about"] = about

    experience = form.get("experience", "")
    if len(experience) == 0:
        form.errors["experience"] = "Experience can not be blank."
    else:
        form.data["experience"] = experience

    return len(form.errors) == 0

def login_page():
    if request.method == "GET":
        values = { "data": {"name": "", "password": ""}}
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
