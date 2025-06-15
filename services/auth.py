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
            
        try:
            # Проверяем хешированный пароль
            return bcrypt.checkpw(password.encode("utf-8"), passw.encode("utf-8"))
        except Exception as e:
            print(f"Error checking password: {e}")
            return False