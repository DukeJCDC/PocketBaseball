import random
import sqlite3
from sqlite3 import Error
from datetime import date

def create_connection(db_file): #Create the database, otherwise connect to it if it exists
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql): #generically create tables
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_games_table(conn): #create table to store top level game info
    seasonnumber = 1
    season = 'games' + str(seasonnumber)
    sql = """CREATE TABLE IF NOT EXISTS '%(season)s' (
        id integer PRIMARY KEY,
        homeid integer NOT NULL,
        awayid integer NOT NULL,
        homescore integer NOT NULL,
        awayscore integer NOT NULL
        );""" % {'season':season}
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def main():
    database = r"smallballdb.db"
    sql_create_teams_table = """ CREATE TABLE IF NOT EXISTS teams (
        id integer PRIMARY KEY,
        owner text NOT NULL,
        start_date date NOT NULL,
        team_name text NOT NULL,
        owner_email text NOT NULL UNIQUE
        );"""
    
        
    conn = create_connection(database)
    if conn is not None:
        create_table(conn, sql_create_teams_table)
        create_games_table(conn)
    #  create_table(conn,sql_create_players_table)
    else:
        print("Error! cannot create the database connection.")

    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(cursor.fetchall())

main()