# my_bi_tool/models/user_model.py

class User:
    """
    Represents a single user record from the 'users' table.
    Depending on your approach, you can implement ORM-like patterns
    or just keep it as a placeholder for user-related logic.
    """
    def __init__(self, user_id, username, email, password):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password

