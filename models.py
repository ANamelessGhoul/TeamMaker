

class User:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.primary_specialization = row[2]
        self.secondary_specializations = row[3]
        self.experience = row[4]

class GameJam:
    def __init__(self, row):
        self.id = row[0]
        self.name = row[1]
        self.theme = row[2]
        self.startDate = row[3]
        self.endDate = row[4]
        self.description = row[5]