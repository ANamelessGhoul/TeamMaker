from flask_login import LoginManager, login_user, login_required, logout_user
from database import Database
from models import User

class User_Login:
    """
    docstring
    """
    def __init__(self, user_id):
        self.data = Database.getInstance().GetUser(user_id)
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.id)
        

def load_user(user_id):
    return User_Login(user_id)