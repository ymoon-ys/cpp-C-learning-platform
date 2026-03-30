from flask_login import user_loaded_from_header
from app.models import User
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))