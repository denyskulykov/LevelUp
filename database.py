import datetime
import sqlite3

path_database = "report/base.db"

view_data = ('mail', 'date', 'name')

connect = sqlite3.connect(path_database, check_same_thread=False)
cursor = connect.cursor()


def _exe_raw_sql(sql):
    try:
        cursor.execute(sql)
        fetchall = cursor.fetchall()
    except sqlite3.DatabaseError as err:
        raise err
    else:
        connect.commit()
    return fetchall


# Mails
def create_bd():
    sql = """
    CREATE TABLE if not exists mails(
        Mail VARCHAR(255) PRIMARY KEY UNIQUE,
        Date VARCHAR(255) NOT NULL,
        Name VARCHAR(255)
        );
    """
    _exe_raw_sql(sql)


def insert_into_table(mail, name, table='mails'):
    date = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

    data = dict(zip(view_data, (mail, name, date)))

    cols = ', '.join("'{}'".format(col) for col in data.keys())
    vals = ', '.join(':{}'.format(col) for col in data.keys())
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, cols, vals)
    try:
        cursor.execute(sql, data)
    except sqlite3.DatabaseError as err:
        raise err
    connect.commit()


def is_not_mail_exist(mail):
    sql = "SELECT * FROM mails WHERE Mail is '{}';".format(mail)
    resp = _exe_raw_sql(sql)
    return not any(resp)
