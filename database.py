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
    
    def GetGameJamsAttending(self, user_id):
        """
        Internal function to handle reading multiple rows of Game Jams depending on time
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT Id, Name, Theme, StartDate, EndDate, Description, Organiser FROM GameJams Join GameJamUsers on GameJams.Id = GameJamUsers.Jam_id WHERE User_id = %s;", (user_id,))
        
        jams = {'attending': [], 'moderating': []}
        row = mycursor.fetchone()
        while row is not None:
            status = 'moderating' if row[6] else 'attending'
            jams[status].append(models.GameJam(row))
            row = mycursor.fetchone()
        
        mycursor.close()
        return jams

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

    def GetPrivateChatRooms(self, user_id):
        """
        Returns a list of dictionaries of Chatrooms the user is in that are not team chat rooms
        """

        expression = """
SELECT Chat_id, u.name as User_count 
FROM ChatRoomUsers c 
JOIN Users u 
ON c.User_id = u.id 
WHERE Chat_id IN (
    SELECT chat.Chat_id 
    FROM ChatRoomUsers chat 
    WHERE NOT EXISTS(
        SELECT * 
        FROM Teams t 
        WHERE t.Chat_id = chat.Chat_id
        ) 
    AND User_id = %s
    ) 
AND User_id != %s;
"""

        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute(expression, (user_id, user_id))
        
        rows = mycursor.fetchall()

        keys = ['id', 'name']
        messages = [dict(zip(keys, values)) for values in rows]
        mycursor.close()

        return messages

    def GetTeamChatRooms(self, user_id):
        """
        Returns a list of dictionaries of team chat rooms the user is in
        """

        expression = "SELECT c.Chat_id, t.Name FROM ChatRoomUsers c JOIN Teams t ON t.Chat_id = c.Chat_id WHERE User_id = %s;"

        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute(expression, (user_id,))
        
        rows = mycursor.fetchall()

        keys = ['id', 'name']
        messages = [dict(zip(keys, values)) for values in rows]
        mycursor.close()

        return messages

    def GetTeam(self, team_id):
        """
        Returns game team with id from database
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()
        mycursor.execute("SELECT * FROM Teams WHERE id = %(id)s", {'id': team_id})

        team = mycursor.fetchone()
        mycursor.close()

        if team is not None:
            return models.Team(team)
        else:
            return None

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
    
    def CreateChatroom(self):
        """
        Creates a new empty chat room and returns its id
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        mycursor.execute("INSERT INTO Chatrooms () VALUES ();")
        id = mycursor.lastrowid
        mycursor.close()
        self.mydb.commit()
        return id
    
    def JoinChatroom(self, user_id, chat_id):        
        """
        Adds user with id user_id into chatroom
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        mycursor.execute("INSERT INTO ChatRoomUsers (Chat_id, User_id) values (%s, %s);",(chat_id, user_id))
        
        mycursor.close()
        self.mydb.commit()

    def CreateTeam(self, name, about, specs, creator_id, jam_id, chat_id):
        """
        Inserts a new team into the database
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = ("INSERT INTO Teams (Name, Description, LookingFor, Leader_id, Jam_id, Chat_id) "
        "VALUES (%s, %s, %s, %s, %s, %s);")
        data = (name, about, specs, creator_id, jam_id, chat_id)

        mycursor.execute(expression, data)
        team_id = mycursor.lastrowid
        mycursor.close()
        self.mydb.commit()
        return team_id
    
    def JoinTeam(self, user_id, team_id):
        """
        Adds user with id user_id to team with id team_id
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        mycursor.execute("INSERT INTO TeamUsers (Team_id, User_id) values (%s, %s);",(team_id, user_id))
        
        mycursor.close()
        self.mydb.commit()

    ### Database Deletions

    def DeleteUser(self, user_id):
        """
        Deletes user and all corresponding data from database
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        mycursor.execute("DELETE FROM Users WHERE id = %s;",(user_id,))
        
        mycursor.close()
        self.mydb.commit()

    def DeleteGameJam(self, jam_id):
        """
        Deletes user and all corresponding data from database
        """
        self.mydb.commit()
        mycursor = self.mydb.cursor()

        mycursor.execute("DELETE FROM GameJams WHERE id = %s;",(jam_id,))
        
        mycursor.close()
        self.mydb.commit()

    ### Database Updates

    def UpdateJam(self, jam_id, name, theme, startDateString, endDateString, about):
        """
        Updates values of the jam corresponding to jam_id in the database
        """

        startDate = startDateString.replace("T"," ") + ":00"
        endDate = endDateString.replace("T"," ") + ":00"

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = """
UPDATE GameJams 
	SET Name = %s,
		Theme = %s,
		StartDate = %s,
		EndDate = %s,
		Description = %s
	WHERE id = %s"""
        data = (name, theme, startDate, endDate, about, jam_id)

        mycursor.execute(expression, data)
        mycursor.close()
        self.mydb.commit()
    
    def UpdateUser(self, user_id, first_name, last_name, about, primary_spec, secondary_spec, experience):
        """
        Updates values of the user corresponding to user_id in the database
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = """
UPDATE Users 
	SET Name = %s,
        ProfileSummary = %s,
        PrimarySpecialization = %s,
        SecondarySpecializations = %s,
        Experience = %s
	WHERE id = %s"""

        data = (first_name + ' ' + last_name, about, primary_spec, secondary_spec, experience, user_id)

        mycursor.execute(expression, data)
        mycursor.close()
        self.mydb.commit()
    
    def UpdateTeam(self, team_id, name, about, specs):
        """
        Inserts a new team into the database
        """

        self.mydb.commit()
        mycursor = self.mydb.cursor()

        expression = "UPDATE Teams SET Name = %s, Description = %s, LookingFor = %s WHERE id = %s"

        data = (name, about, specs, team_id)

        mycursor.execute(expression, data)
        team_id = mycursor.lastrowid
        mycursor.close()
        self.mydb.commit()
        return team_id
