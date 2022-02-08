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

def create_team(conn): # add team information into database
    """
    Create a new team on the teams table
    :param conn:
    :param team info:
    :return: team id
    """
    today=date.today()
    ownername = input("What's your name?")
    teamname = input("Whats your teams name?")
    email = input("What's your email?")
    #teaminfo = (ownername, today, teamname, email)
    
    sql = """INSERT INTO teams (owner,start_date,team_name,owner_email) 
            VALUES('%(owner)s','%(start_date)s','%(team_name)s','%(owner_email)s');""" % {'owner':ownername,'team_name':teamname,'start_date':today,'owner_email':email}
    cursor= conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
    except Error as e:
        print(e)
    
    teamid = cursor.lastrowid
    create_player_table(conn,teamid)
    
    for x in range(0,12):
        batting, running, throwing, catching, strength, morale, position, lineup = statGen(x)
        playerStats = (x+100, position, lineup, batting, running, throwing, catching, morale, strength, 1, teamid)
        player_id = add_player(conn, playerStats, teamid)
        #print(player_id)
    get_players(conn,teamid)

    return cursor.lastrowid

def create_player_table(conn, teamid): #create the roster table with players stats, positions and lineups

    sql = """CREATE TABLE IF NOT EXISTS '%(teamid)s' (
        id integer PRIMARY KEY,
        player_name text NOT NULL,
        player_pos text NOT NULL,
        player_lineup integer NOT NULL,
        player_batting integer NOT NULL,
        player_running integer NOT NULL,
        player_throwing integer NOT NULL,
        player_catching integer NOT NULL,
        player_morale integer NOT NULL,
        player_strength text NOT NULL,
        player_active integer NOT NULL,
        team_id integer NOT NULL,
        FOREIGN KEY (team_id) REFERENCES teams (id)
        );""" % {'teamid':teamid}
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def add_player(conn, playerinfo, teamid): #add player stats into database
    """
    Add a new player
    :param conn:
    :param playerinfo:
    :return:
    """
    sql = '''INSERT INTO '%(teamid)s'(player_name,player_pos,player_lineup,player_batting,player_running,player_throwing,player_catching,player_morale,player_strength,player_active,team_id)
    VALUES(?,?,?,?,?,?,?,?,?,?,?) ''' % {'teamid':teamid}
    cursor = conn.cursor()
    cursor.execute(sql, playerinfo)
    conn.commit()
    return cursor.lastrowid

def get_teams(conn): #Print Teams table
    cursor = conn.cursor()
    with conn:
        cursor.execute("SELECT * FROM teams")
        print(cursor.fetchall())

def get_players(conn,teamid): #Print Players table
    cursor = conn.cursor()
    with conn:
        cursor.execute("SELECT * FROM '%(teamid)s'" % {'teamid':teamid})
        print(cursor.fetchall())

def statGen(x): # generate stats for an individual player and return them
    a=0
    b=0
    c=0
    d=0
    positions = ['P','C','1B','2B','SS','3B','LF','CF','RF','DH','BENCH','BENCH']
    morale = 50
    strength = random.randrange(1,5)
    if strength == 5:
        strength = 'None'
    elif strength == 1:
        strength = 'batting'
        a=10
    elif strength == 2:
        strength = 'running'
        b=10
    elif strength == 3:
        strength = 'throwing'
        c=10
    elif strength == 4:
        strength = 'catching'
        d=10
    lineup = x+1
    position = positions[x]
    
    batting = random.randrange(2,5) + a
    running = random.randrange(2,5) + b
    throwing = random.randrange(2,5) + c
    catching = random.randrange(2,5) + d
    
    #id = playerStats(batting,running,throwing,catching,strength)
    return batting, running, throwing, catching, strength, morale, position, lineup

    
def main():
    today=date.today()
    database = r"smallballdb.db"       
    conn = create_connection(database)
    team_id = create_team(conn)

    get_teams(conn)


main()





# class playerStats:
#     roster=[]
#     def __init__(self, batting, running, throwing, catching, strength):
#         self.roster.append(self)
#         self.batting = batting
#         self.running = running
#         self.throwing = throwing
#         self.catching = catching
#         self.strength = strength