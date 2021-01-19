# Decouple allows for local environment variables
from decouple import config
import mysql.connector
import bcrypt

import models


class Database:
    __instance = None

    @staticmethod 
    def getInstance():
        """ Static access method. """
        if Database.__instance == None:
            Database()
        return Database.__instance

    def __init__(self):
        if Database.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Database.__instance = self
        # Set up sql connection
        self.mydb = mysql.connector.connect(
            host=config('SQL_HOST'),
            user=config('SQL_USER'),
            password=config('SQL_PASSWORD'),
            database=config('SQL_DATABASE')
        )

    ### Database queries

    times_dict = {
        "All": "SELECT * FROM GameJams",
        "Ongoing": "SELECT * FROM GameJams WHERE startDate <= CURRENT_TIMESTAMP() AND endDate > CURRENT_TIMESTAMP()",
        "Upcoming": "SELECT * FROM GameJams WHERE startDate >= CURRENT_TIMESTAMP()",
        "Active": "SELECT * FROM GameJams WHERE endDate > CURRENT_TIMESTAMP()",
        "Past": "SELECT * FROM GameJams WHERE endDate <= CURRENT_TIMESTAMP()"
    }

    def _GetGameJams(self, time):
        """
        Internal function to handle reading multiple rows of Game Jams depending on time
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute(self.times_dict[time])
        
        jams = []
        row = mycursor.fetchone()
        while row is not None:
            jams.append(models.GameJam(row))
            row = mycursor.fetchone()
        
        mycursor.close()
        return jams

    def GetAllGameJams(self):
        """
        Returns an array of all game jams
        """
        return self._GetGameJams("All")

    def GetUpcomingGameJams(self):
        """
        Returns an array of all game jams where current timestamp is less than start date of game jam
        """
        return self._GetGameJams("Upcoming")
    
    def GetActiveGameJams(self):
        """
        Returns an array of all game jams where current timestamp is within start and end date of game jam
        """
        return self._GetGameJams("Active")

    def GetOngoingGameJams(self):
        """
        Returns an array of all game jams where current timestamp is within start and end date of game jam
        """
        return self._GetGameJams("Ongoing")

    def GetPastGameJams(self):
        """
        Returns an array of all game jams where current timestamp is greater than end date of game jam
        """
        return self._GetGameJams("Past")

    def GetGameJam(self, id):
        """
        Returns game jam with id from database
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM GameJams WHERE id = %(id)s", {'id': id})

        jam = mycursor.fetchone()
        mycursor.close()

        if jam is not None:
            return models.GameJam(jam)
        else:
            return None
    
    def GetUser(self, value, field = 'id'):
        """
        Returns user with value corresponding to field from database
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM Users WHERE {} = %(value)s".format(field), {'value': value})

        user = mycursor.fetchone()
        mycursor.close()

        if user is not None:
            return models.User(user)
        else:
            return None
    
    def ValidatePassword(self, email, password):
        """
        Checks database to see if given email has corresponding password
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT password FROM Users WHERE email = %s", (email,))
        
        password_hash = mycursor.fetchone()
        mycursor.close()

        return bcrypt.checkpw(bytes(password, encoding="utf-8"), bytes(password_hash[0], encoding="utf-8"))
    
    def GetUsersAttending(self, jam_id):
        """
        Returns a list of all users attending the given game jam
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        expression = "SELECT * FROM Users Join GameJamUsers on Users.Id = GameJamUsers.User_id WHERE Jam_id = %s;"
        mycursor.execute(expression, (jam_id,))
        
        users = []
        row = mycursor.fetchone()
        while row is not None:
            user = models.User(row)
            user.moderator = row[10]
            users.append(user)
            row = mycursor.fetchone()
        
        mycursor.close()
        return users

    def GetMessages(self, chat_id, count = 500):
        """
        Returns a list of size count with messages from chat room chat_id
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        expression = "SELECT Content, Author_id, Name FROM Messages JOIN Users ON Messages.Author_id = Users.id WHERE Messages.Chatroom_id = %s  ORDER BY Messages.DateSent DESC LIMIT %s;"
        mycursor.execute(expression, (chat_id,count))
        
        rows = mycursor.fetchall()

        keys = ['data','user_id', 'user_name']
        messages = [dict(zip(keys, values)) for values in rows]
        messages.reverse()
        mycursor.close()
        return messages
    
    def IsUserInChatroom(self, user_id, chat_id):
        """
        returns True if player is in the chat room
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT count(Chat_id) FROM ChatRoomUsers WHERE User_id = %s AND Chat_id = %s;", (user_id,chat_id))
        
        count = mycursor.fetchone()[0]
        mycursor.close()
        
        return count == 1

    ### Database Insertions

    def AddNewUser(self, email, first_name, last_name, about, primary_spec, secondary_spec, experience, password):
        """
        Inserts a new user into the database
        """
        hashed_password = bcrypt.hashpw(bytes(password, encoding="utf-8"), bcrypt.gensalt())
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = ("INSERT INTO Users (Name, Email, ProfileSummary, PrimarySpecialization, SecondarySpecializations, Experience, Password) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s);")
        data = (first_name + ' ' + last_name, email, about, primary_spec, secondary_spec, experience, hashed_password)

        mycursor.execute(expression, data)
        mycursor.close()
        self.mydb.commit()

    def AddNewJam(self, name, theme, startDateString, endDateString, about):
        """
        Inserts a new jam into the database
        """

        startDate = startDateString.replace("T"," ") + ":00"
        endDate = endDateString.replace("T"," ") + ":00"

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = ("INSERT INTO GameJams (Name, Theme, StartDate, EndDate, Description) "
        "VALUES (%s, %s, %s, %s, %s);")
        data = (name, theme, startDate, endDate, about)

        mycursor.execute(expression, data)
        id = mycursor.lastrowid
        mycursor.close()
        self.mydb.commit()
        return id
    
    def UserAttendJam(self, user_id, jam_id, moderator = False):
        """
        Inserts a new entry to represent attending the jam into the database
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = ("INSERT INTO GameJamUsers (user_id, jam_id, organiser) VALUES (%s, %s, %s);")
        data = (user_id, jam_id, moderator)

        mycursor.execute(expression, data)
        mycursor.close()
        self.mydb.commit()
    
    def InsertMessage(self, user_id, room_id, message):
        """
        Inserts a new message with user id and chatroom id into the database
        """
        
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = ("INSERT INTO Messages (Content, Author_id, Chatroom_id) Values (%s, %s, %s);")
        data = (message, user_id, room_id)

        mycursor.execute(expression, data)
        mycursor.close()
        self.mydb.commit()