
class User:
    def __init__(self, row):
        self.id = row[0]
        self.email = row[1]
        self.name = row[2]
        self.primary_specialization = row[3]
        self.secondary_specializations = row[4]
        self.experience = row[5]
    
    

class GameJam:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.theme = row[2]
        self.startDate = row[3]
        self.endDate = row[4]
        self.description = row[5]

class Team:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.description = row[2]
        self.leader_id = row[3]

class ChatRoom:
    def __init__(self, row):
        self.id = row[0]
        self.creator_id = row[1]

class Message:
    def __init__(self, row):
        self.sent_date = row[0]
        self.content = row[1]
        self.author_id = row[2]
        self.chatroom_id = row[3]