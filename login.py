from flask_login import LoginManager, login_user, login_required, logout_user
from database import Database
from models import User

class User_Login:
    """
    docstring
    """
    def __init__(self, user_id):
        self.data = Database.getInstance().GetUser(user_id)
    @property
    def is_authenticated(self):
        return self.data is not None
    @property
    def is_active(self):
        return True
    @property
    def is_anonymous(self):
        return False
    def get_id(self):
        if self.data is None:
            return None
        
        return str(self.data.id)
        

def load_user(user_id):
    return User_Login(user_id)