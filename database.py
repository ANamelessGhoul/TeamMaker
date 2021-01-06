# Decouple allows for local environment variables
from decouple import config
import mysql.connector

import models

class Database:
    def __init__(self):
        # Set up sql connection
        # TODO: Replace with real connection
        self.mydb = mysql.connector.connect(
            host=config('SQL_HOST'),
            user=config('SQL_USER'),
            password=config('SQL_PASSWORD'),
            database=config('SQL_DATABASE')
        )


    def __del__(self):
        self.mydb.close()


    def GetUpcomingGameJams(self):
        """
        Returns an array of all game jams where current timestamp is less than start date of game jam
        """

        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM GameJams WHERE startDate > CURRENT_TIMESTAMP()")
        
        upcoming_jams = []
        row = mycursor.fetchone()
        while row is not None:
            upcoming_jams.append(models.GameJam(row))
            row = mycursor.fetchone()
        
        mycursor.close()
        return upcoming_jams

    def GetActiveGameJams(self, parameter_list):
        """
        Returns an array of all game jams where current timestamp is within start and end date of game jam
        """
        
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM GameJams WHERE startDate < CURRENT_TIMESTAMP() AND endDate > CURRENT_TIMESTAMP()")
        
        active_jams = []
        row = mycursor.fetchone()
        while row is not None:
            active_jams.append(models.GameJam(row))
            row = mycursor.fetchone()
        
        mycursor.close()
        return active_jams
