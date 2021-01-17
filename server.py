# https://web.itu.edu.tr/uyar/fad/application-structure.html
from flask import Flask, render_template
from flask_login import LoginManager, login_user, login_required, logout_user
from decouple import config


from datetime import datetime

import view
from database import Database

import login


def create_app():
    # Configure flask app
    app = Flask(__name__)

    app.secret_key = config('SECRET_KEY')

    app.add_url_rule("/", view_func = view.home_page)
    app.add_url_rule("/image/<filename>", view_func=view.image_server)

    app.add_url_rule("/gamejams/<status>", view_func = view.gamejams_page, methods=["GET", "POST"])
    app.add_url_rule("/gamejams", view_func = view.gamejams_redirect, methods=["GET", "POST"])
    app.add_url_rule("/viewjam/<int:jam_id>", view_func = view.jam_page, methods=["GET", "POST"])
    app.add_url_rule("/newjam", view_func = view.newjam_page, methods=["GET", "POST"])

    app.add_url_rule("/profile/<int:user_id>", view_func = view.profile_page)
    app.add_url_rule("/myprofile", view_func = view.my_profile_page)

    app.add_url_rule("/signup", view_func=view.signup_page, methods=["GET", "POST"])
    app.add_url_rule("/login", view_func=view.login_page, methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=view.logout_page)

    # Configure database
    database = Database.getInstance()

    # Configure flask login
    login_manager = LoginManager(app)
    login_manager.init_app(app)
    login_manager.user_loader(login.load_user)
    login_manager.login_view = "login_page"



    # Get Settings
    app.config.from_object("settings")
    return app


if __name__ == "__main__":

    app = create_app()
    app.run(host = "0.0.0.0", port = 8080)


