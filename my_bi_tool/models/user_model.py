# my_bi_tool/models/user_model.py

class User:
    """
    Represents a User record from the 'users' table.
    """
    def __init__(self, user_id, username, email, password):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password

