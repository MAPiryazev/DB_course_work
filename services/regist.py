import repositories.users
import bcrypt
import repositories.registr
import pandas as pd


class Registration():
    def registr(self, user: pd.DataFrame):
        return repositories.registr.registration(user)
