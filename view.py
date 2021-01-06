from flask import Flask, render_template, current_app, abort, request, redirect, url_for,  send_from_directory
from datetime import datetime
from movie import Movie

def image_server(filename):
    return send_from_directory("./images", filename)

def home_page():
    today = datetime.today()
    day_name = today.strftime("%A")
    return render_template("home.html", day = day_name)

def movies_page():
    db = current_app.config["db"]
    if request.method == "GET":
        movies = db.get_movies()
        return render_template("movies.html", movies = sorted(movies))
    else:
        form_movie_keys = request.form.getlist("movie_keys")
        for form_movie_key in form_movie_keys:
            db.delete_movie(int(form_movie_key))
        return redirect(url_for("movies_page"))

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

def signup_page():
    if request.method == "GET":
        values = { "data": {"name": "", "password": ""}}
        return render_template(
            "signup.html", 
            values = values
        )
    else:
        valid = validate_signup_form(request.form)
        if not valid:
            return render_template(
                "signup.html",
                values=request.form,
            )
        # title = request.form.data["title"]
        # year = request.form.data["year"]
        # movie = Movie(title, year=year)
        # db = current_app.config["db"]
        # movie_key = db.add_movie(movie)
        return redirect(url_for("home_page"))

def validate_signup_form(form):
    form.data = {}
    form.errors = {}

    form_name = form.get("name", "").strip()
    if len(form_name) == 0:
        form.errors["name"] = "Title can not be blank."
    else:
        form.data["name"] = form_name

    return len(form.errors) == 0