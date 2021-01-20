from specs import getRoles, decodeSpecs

class User:
    def __init__(self, row):
        self.id = row[0]
        self.email = row[1]
        self.name = row[2]
        self.about = row[3]
        self.primary_spec_raw = int(row[4])
        self.primary_spec = getRoles()[int(row[4])]
        self.secondary_specs_raw = int(row[5])
        self.secondary_specs = decodeSpecs(int(row[5]))
        self.experience = row[6]
    
    

class GameJam:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.theme = row[2]
        self.startDate = row[3]
        self.endDate = row[4]
        self.about = row[5]
    
    @property
    def duration(self):
        return self.endDate - self.startDate


class Team:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.about = row[2]
        self.looking_for = row[3]
        self.leader_id = int(row[4])
        self.jam_id = int(row[5])
        self.chat_id = int(row[6])


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