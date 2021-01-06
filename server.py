# https://web.itu.edu.tr/uyar/fad/application-structure.html
from flask import Flask, render_template
from flask_login import LoginManager


from datetime import datetime

import view
from database import Database
from movie import Movie

import models

def create_app():
  # Configure flask app
  app = Flask(__name__)
  app.add_url_rule("/", view_func = view.home_page)
  app.add_url_rule("/movies", view_func = view.movies_page, methods=["GET", "POST"])
  app.add_url_rule("/movies/<int:movie_key>", view_func = view.movie_page)
  app.add_url_rule("/new-movie", view_func=view.movie_add_page, methods=["GET", "POST"])
  app.add_url_rule("/image/<filename>", view_func=view.image_server)
  app.add_url_rule("/signup", view_func=view.signup_page, methods=["GET", "POST"])

  # Configure temporary database
  db = Database()
  db.add_movie(Movie("Slaughterhouse-Five", year = 1972))
  db.add_movie(Movie("The Shining"))
  app.config["db"] = db

  # Configure flask login
  # login = LoginManager(app)
  # login.init_app(app)

  # Get Settings
  app.config.from_object("settings")
  return app


if __name__ == "__main__":


  db = Database()
  active_jams = db.GetUpcomingGameJams()
  if(len(active_jams) == 0):
    print('No upcoming jams')
  else:
    for jam in active_jams:
      print('{}: {} - {} -> {} = {}'.format(jam.id, jam.name, jam.startDate, jam.endDate, jam.endDate - jam.startDate))



  del db


  # print(mycursor.rowcount, "users found.")
  # app = create_app()
  # app.run(host = "0.0.0.0", port = 8080)

