import repositories.users
import bcrypt


users = repositories.users.get_users_with_password()


class Authotize():

    def __init__(self):
        self.users = self.get_users()

    def get_users(self):
        users = repositories.users.get_users_with_password()
        return {user["email"]: user["password"] for user in users}

    def auth(self, email, password: str):
        # print(self.users)
        passw = None

        if email in self.users:
            passw = self.users[email]
        else:
            return False

        if (passw == None):
            return False
        if (bcrypt.checkpw(password.encode("utf-8"), passw.encode("utf-8"))):
            return True