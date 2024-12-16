import psycopg2
import psycopg2.extras
from repositories.settings import DB_CONFIG
from pandas import DataFrame
import repositories.users

def get_users() -> DataFrame:

    users = repositories.users.get_users()

    result = DataFrame(users)

    result = result[["user_id", "email"]]

    #for dic in users:
    #    for key in dic.keys():
    #        #result.insert(0, column=key, value=dic[key])
    #        result[key] = [dic[key]]
    #        print(key, dic[key])

    return result


# services.py

