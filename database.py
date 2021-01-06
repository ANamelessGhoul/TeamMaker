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


    def GetActiveGameJams(self):
        """
        Gets all current game jams
        """

        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM GameJams WHERE startDate < CURRENT_TIMESTAMP()")
        
        active_jams = []
        row = mycursor.fetchone()
        while row is not None:
            active_jams.append(models.GameJam(row))
            row = mycursor.fetchone()
        
        mycursor.close()
        return active_jams
