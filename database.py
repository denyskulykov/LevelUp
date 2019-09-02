import sqlite3

path_database = "base.db"

connect = sqlite3.connect(path_database, check_same_thread=False)
cursor = connect.cursor()

view_data = (
    'Number',
    'Name',
    'Link',
    'Price',
    'Profile',
    'Information',
    'Address')

view_data_telegram = (
    'Number',
    'Name',
    'Seen',
    'Profile',
    'Processed')


# Common
def _exe_raw_sql(sql):
    try:
        cursor.execute(sql)
        fetchall = cursor.fetchall()
    except sqlite3.DatabaseError as err:
        raise err
    else:
        connect.commit()
    return fetchall


# People
def create_bd():
    sql = """
    CREATE TABLE if not exists people(
        Id INTEGER PRIMARY KEY UNIQUE,
        Number VARCHAR(255) NOT NULL,
        Name VARCHAR(255) NOT NULL,
        Link VARCHAR(255),
        Price VARCHAR(255),
        Profile VARCHAR(255),
        Information VARCHAR(255),
        Address VARCHAR(255),
        CONSTRAINT unique_local UNIQUE (Number)
        );
    """
    _exe_raw_sql(sql)


def insert_into_table(*args, table='people'):
    if table == 'people':
        colons = view_data
    elif table == 'telegram':
        colons = view_data_telegram
    data = dict(zip(colons, args))

    cols = ', '.join("'{}'".format(col) for col in data.keys())
    vals = ', '.join(':{}'.format(col) for col in data.keys())
    sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, cols, vals)
    try:
        cursor.execute(sql, data)
    except sqlite3.DatabaseError as err:
        raise err
    connect.commit()


def get_all():
    sql = "SELECT * FROM people;"
    return _exe_raw_sql(sql)


#  Filters People
def filter_by_links(links):
    """links should be set, Return Set of links for processing"""

    assert isinstance(links, set)

    sql = "SELECT Link FROM people WHERE Link in ({});".format(
        ', '.join(["'{}'".format(item) for item in links]))
    resp = _exe_raw_sql(sql)
    return set(links) - set([item[0] for item in resp])


def is_not_phone_exists(phone):
    """Return True or False"""

    sql = "SELECT Number FROM people WHERE Number is '{}';".format(phone)
    resp = _exe_raw_sql(sql)
    return not any(resp)


def number_exists(number):
    """Return True or False"""
    return _exe_raw_sql("SELECT Link FROM people WHERE Link is '{}';"
                        .format(number))


def link_exists(link):
    """Return True or False"""
    return _exe_raw_sql("SELECT Link FROM people WHERE Link is '{}';"
                        .format(link))


# Telegram
def create_bd_telegram():
    sql = """
    CREATE TABLE if not exists telegram(
        Number VARCHAR(20) NOT NULL,
        Name VARCHAR(100) NOT NULL,
        Seen VARCHAR(30),
        Profile VARCHAR(255),
        Processed INTEGER,
        CONSTRAINT unique_local UNIQUE (Number)
        );
    """
    _exe_raw_sql(sql)


def is_telegram_acount(phone):
    """Return True or False"""

    sql = "SELECT Number FROM telegram WHERE Number is '{}';".format(phone)
    resp = _exe_raw_sql(sql)
    return any(resp)


def get_all_from_telegram():
    sql = "SELECT * FROM telegram;"
    return _exe_raw_sql(sql)


def get_user_from_telegram(phone):
    sql = "SELECT Name, Seen, Profile, Processed " \
          "FROM telegram WHERE Number is '{}';".format(phone)
    return _exe_raw_sql(sql)


def get_unprocessed_users():
    sql = "SELECT Number FROM telegram " \
          "WHERE Name IS NOT 'Not found' AND Processed IS NULL;"
    return [item[0] for item in _exe_raw_sql(sql)]


def set_user_processed(phone):
    sql = "UPDATE telegram SET Processed=1 WHERE Number = '{}'".format(phone)
    return [item[0] for item in _exe_raw_sql(sql)]
