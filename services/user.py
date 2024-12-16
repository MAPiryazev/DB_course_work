import psycopg2
import psycopg2.extras
from repositories.settings import DB_CONFIG
from pandas import DataFrame
import repositories.users

def get_user(email) -> DataFrame:

    user = repositories.users.get_user_by_email(email)

    result = DataFrame(user)

    #for dic in user:
    #    for key in dic.keys():
    #        #result.insert(0, column=key, value=dic[key])
    #        result[key] = [dic[key]]
    #        print(key, dic[key])

    return result

def get_user_balance(user_email) -> float:

    return repositories.users.get_user_balance_by_email(user_email)


# services.py

def set_user_balance(user_email, new_balance: float) -> None:
    repositories.users.set_user_balance_by_email(user_email, new_balance)
    print("баланс пользователея пополнен до new_balance", new_balance)

