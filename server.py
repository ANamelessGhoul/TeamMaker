# https://web.itu.edu.tr/uyar/fad/application-structure.html
from flask import Flask, render_template
from flask_login import LoginManager, login_user, login_required, logout_user


from datetime import datetime

import view
from database import Database
from movie import Movie

import login


def create_app():
    # Configure flask app
    app = Flask(__name__)
    app.add_url_rule("/", view_func = view.home_page)
    app.add_url_rule("/gamejams", view_func = view.gamejams_page, methods=["GET", "POST"])
    app.add_url_rule("/movies/<int:movie_key>", view_func = view.movie_page)
    app.add_url_rule("/new-movie", view_func=view.movie_add_page, methods=["GET", "POST"])
    app.add_url_rule("/image/<filename>", view_func=view.image_server)
    app.add_url_rule("/signup", view_func=view.signup_page, methods=["GET", "POST"])

    # Configure temporary database
    database = Database.getInstance()

    # Configure flask login
    login_manager = LoginManager(app)
    login_manager.init_app(app)
    login_manager.user_loader(login.load_user)

    # Get Settings
    app.config.from_object("settings")
    return app


if __name__ == "__main__":

    app = create_app()
    app.run(host = "0.0.0.0", port = 8080)


