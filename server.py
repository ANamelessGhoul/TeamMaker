# https://web.itu.edu.tr/uyar/fad/application-structure.html
from flask import Flask, render_template
from flask_login import LoginManager

# Decouple allows for local environment variables
from decouple import config

from datetime import datetime
import mysql.connector

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
  # Set up sql connection
  # TODO: Replace with real connection
  mydb = mysql.connector.connect(
    host=config('SQL_HOST'),
    user=config('SQL_USER'),
    password=config('SQL_PASSWORD'),
    database=config('SQL_DATABASE')
  )

  mycursor = mydb.cursor()
  sql = "SELECT * FROM GameJams WHERE id = 1"
  # val = ("John", "Highway 21")
  mycursor.execute(sql)
  #mydb.commit()
  jam = models.GameJam(mycursor.fetchone())
  #for (id, name, desc, primary, secondary, Experience) in mycursor:
  print('{}: {} - {} -> {} = {}'.format(jam.id, jam.name, jam.startDate, jam.endDate, jam.endDate - jam.startDate))

  mycursor.close()
  mydb.close()

  # print(mycursor.rowcount, "users found.")
  # app = create_app()
  # app.run(host = "0.0.0.0", port = 8080)

