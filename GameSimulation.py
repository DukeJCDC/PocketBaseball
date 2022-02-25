from importlib.util import module_for_loader
import random
import sqlite3
from sqlite3 import Error
from datetime import date
import pandas as pd
import math

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

def create_scoreboard(conn):
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

class Player: #Loads player stats into player object, adjusting for morale
    #Running speed: 23ft/sec is slow, 27ft/sec is average, 30ft/sec is fast
    def __init__(self, batting, running, throwing, catching, pos, morale, lineup, player_name):
        self.batting = batting * (morale/100)
        self.running = round((running * (morale/100))/100 * 7 + 23)
        self.throwing = throwing * (morale/100)
        self.catching = catching * (morale/100)
        self.pos = pos
        self.lineup = lineup
        self.player_name = player_name

class Team:  #Holds each player stats and is grouped by hometeam and awayteam
  def __init__(self, ID,conn):
    teamlist = pd.read_sql_query("SELECT * from '%(teamid)s' WHERE player_pos != 'BENCH'" % {'teamid': ID}, conn)
    self.lineup = pd.read_sql_query("SELECT * from '%(teamid)s' WHERE player_pos != 'BENCH'" % {'teamid': ID}, conn)
    self.P = get_stats(teamlist, 'P')
    self.C = get_stats(teamlist, 'C')
    self.FIR = get_stats(teamlist, '1B')
    self.SEC = get_stats(teamlist, '2B')
    self.SS = get_stats(teamlist, 'SS')
    self.THI = get_stats(teamlist, '3B')
    self.LF = get_stats(teamlist, 'LF')
    self.CF = get_stats(teamlist, 'CF')
    self.RF = get_stats(teamlist, 'RF')
    self.DH = get_stats(teamlist, 'DH')

class Scoreboard: #Tracks all of the game stats and contains methods to update stats
    def __init__(self,hometeam,awayteam):
        self.hometeam = hometeam
        self.awayteam = awayteam
        self.homeBatter = 1
        self.awayBatter = 1
        self.inning = 0
        self.strike = 0
        self.ball = 0
        self.outs = 0
        self.homeHits = 0
        self.awayHits = 0
        self.homeRuns = 0
        self.awayRuns = 0
        self.homeErrors = 0
        self.awayErrors = 0
        self.homeWalks = 0
        self.awayWalks = 0
        self.onFirst = []
        self.onSecond = []
        self.onThird = []
    def Strike(self):
        self.strike = self.strike + 1
    def Ball(self):
        self.ball = self.ball + 1
    def print_Count(self):
        return print(self.ball," - ",self.strike)
    def AwayHit(self):
        self.awayHits = self.awayHits + 1
    def HomeHit(self):
        self.homeHits = self.homeHits + 1
    def ResetCount(self):
        self.strike = 0
        self.ball = 0
    def Outs(self):
        self.outs = self.outs + 1
    def ResetInning(self):
        self.ResetCount()
        self.outs = 0
    def nexthomeBatter(self):
        if self.homeBatter == 9:
            self.homeBatter = 1
        else:
            self.homeBatter = self.homeBatter + 1
    def nextawayBatter(self):
        if self.awayBatter == 9:
            self.awayBatter = 1
        else:
            self.awayBatter = self.awayBatter + 1
    def nextInning(self):
        if self.inning <10:
            self.inning = self.inning +1

def get_stats(team,item): #Loads Dict to put into Player object, loaded from Team object
    return_dict = {
        "pos": team.loc[team['player_pos'] == item]['player_pos'].values[0],
        "batting":team.loc[team['player_pos'] == item]['player_batting'].values[0],
        "running": team.loc[team['player_pos'] == item]['player_running'].values[0],
        "throwing": team.loc[team['player_pos'] == item]['player_throwing'].values[0],
        "catching": team.loc[team['player_pos'] == item]['player_catching'].values[0],
        "lineup": team.loc[team['player_pos'] == item]['player_lineup'].values[0],
        "morale": team.loc[team['player_pos'] == item]['player_morale'].values[0],
        "player_name": team.loc[team['player_pos'] == item]['player_name'].values[0]
    }
    playername = Player(return_dict['batting'],return_dict['running'],return_dict['throwing'],return_dict['catching'],return_dict['pos'],return_dict['morale'],return_dict['lineup'],return_dict['player_name'])

    return playername

def batter(lineupnumber,team): #Takes in the current lineup number for the team at bat and returns the players batting and running skill and name.
    batterrating = team.loc[team['player_lineup'] == lineupnumber]['player_batting'].values[0]
    player_name = team.loc[team['player_lineup'] == lineupnumber]['player_name'].values[0]
    batter_running = team.loc[team['player_lineup'] == lineupnumber]['player_running'].values[0]
    return batterrating,player_name,batter_running

def throw_pitch(pitcherrating,batterrating): #All actions from pitch to where ball will land/roll
    pitchquality = random.randint(0,100)
    pitchspeed = random.randint(0,int(pitcherrating))
    if pitcherrating >= pitchquality:
        pitch='strike'
    elif pitchquality == 0:
        pitch='deadball'
    else:
        pitch = 'ball'
    action,distance,hitangle,hitlift = hit_pitch(pitch,pitchspeed,batterrating)
    return action,distance,hitangle,hitlift

def hit_pitch(pitch,pitchspeed,batterrating): #Determines if the batter hits the ball
    idpitch = random.randint(0,100)
    hitpower = random.randint(0,int(batterrating))
    anglecoinflip = random.randint(0,1)
    if anglecoinflip == 1:
        hitangle = random.randint(0,50) + hitpower
    else:
        hitangle = random.randint(0,150)
    if batterrating >= idpitch:
        if pitch == 'strike' and hitpower >= pitchspeed:
            action = 'hit'
        elif pitch == 'strike':
            action = 'strike'
        else:
            action = 'ball'
    elif hitpower <= pitchspeed and pitch == 'strike':
        action = 'hit'
    elif hitpower <= pitchspeed and pitch == 'ball':
        action = 'strike'
    elif hitpower >= pitchspeed and pitch == 'strike':
        action = 'strike'
    else:
        action = 'ball'
    distance = hitpower * 1.25
    hitlift = random.randint(0,int(batterrating))
    return action,distance,hitangle,hitlift

def field_hitOLD(distance,hitangle,hitlift,team,batter_running): #MOVED TO MAIN() -- Determines where the ball goes when hit and initial proposed structure for who attempts to catch the ball
    # Homerun Hits take off between 25-30 degrees typically. 
    # Groundball is <10 degrees, 
    # Line drive is 10-25 degrees, 
    # Fly ball is 25-50, 
    # Pop up is 50 or higher

    lvl0 = 30 #catcher gets the ball
    lvl1 = 45 #pitcher gets the ball
    lvl2 = 120 #infielder gets the ball
    inangle1 = 52 #thirdbase gets the ball
    inangle2 = 75 #SS gets the ball
    inangle3 = 88 #2B gets the ball
    outangle1 = 60 #LF gets the ball
    outangle2 = 90 #CF gets the ball
    batter_to_base = 8 - (batter_running/100)*2
    #print(batter_to_base)

    time_in_air = round(abs((((distance * math.sin(hitlift))+(distance * math.sin(hitlift)))/(9.8*3.281))),2)
    air_distance = round(time_in_air*abs((distance * math.cos(hitlift))))
    if air_distance <= lvl0:
        responder = ['C',0,75]
    elif air_distance <=lvl1:
        responder = ['P',60,0]
    elif air_distance <= lvl2:
        if hitangle <= inangle1:
            responder = ['3B',95,35]
        elif hitangle <= inangle2:
            responder = ['SS',122,70]
        elif hitangle <= inangle3:
            responder = ['2B',122,80]
        else:
            responder = ['1B',95,115]
    else:
        if hitangle <= outangle1:
            responder = ['LF',210,52]
        elif hitangle <= outangle2:
            responder = ['CF',264,75]
        else:
            responder = ['RF',210,98]

    responder_running = team.loc[team['player_pos'] == responder[0]]['player_running'].values[0]
    responder_throw = team.loc[team['player_pos'] == responder[0]]['player_throwing'].values[0]
    responder_catch = team.loc[team['player_pos'] == responder[0]]['player_catching'].values[0]
    print('The ball traveled ',air_distance,'ft in ',time_in_air,' seconds towards ',responder[0])
    groundroll = air_distance*.3

def reset_positions():
    CPos = [0,0]
    PPos = [42,42]
    FirPos = [99,25]
    SecPos = [99,65]
    SSPos = [65,99]
    ThiPos = [25,99]
    LFPos = [90,225]
    CFPos = [210,210]
    RFPos = [225,90]
    FirstBase = [90,0]
    SecondBase = [90,90]
    ThirdBase = [0,90]
    HomeBase = [0,0]
    FieldPositions = {'C': CPos,'P': PPos,'FIR': FirPos,'SEC': SecPos,'SS': SSPos,'THI':ThiPos,'LF':LFPos,'CF':CFPos,'RF':RFPos}
    return FieldPositions

def field_hit(batter_running,distance,hitlift,hitangle,fielding):
    #In Play hit is angle 0 to 90 degrees
    # Homerun Hits take off between 25-30 degrees typically. 
    # Groundball is <10 degrees, 
    # Line drive is 10-25 degrees, 
    # Fly ball is 25-50, 
    # Pop up is 50 or higher
    hitangle = hitangle - 30
    if hitangle < 0 or hitangle > 90:
        action = 'foul'
        return action
    elif hitlift >= 50:
        action = 'fly out'
        return action
    else:
        action = 'hit'
        #return action
        FieldPositions = reset_positions()
        batter_to_base = 90/batter_running
        time_in_air = round(abs((((distance * math.sin(hitlift))+(distance * math.sin(hitlift)))/(9.8*3.281))),2)
        air_distance = round(time_in_air*abs((distance * math.cos(hitlift))))
        if air_distance > 300:
            print('Home run!')
            action = 'hit'
            return action
        # print('The ball launched at ',hitlift,'degrees for ',air_distance,'ft in ',time_in_air)
        groundroll = air_distance*.3
        nearest_position = None
        nearest_distance = 1000
        x_pos = abs(round(air_distance * math.cos(hitangle)))
        y_pos = abs(round(air_distance * math.sin(hitangle)))
        #print('Angle is ',hitangle,' to (',x_pos,',',y_pos,')')
        
        for item in FieldPositions:
            item_x = FieldPositions.get(item)[0]
            item_y = FieldPositions.get(item)[1]
            distance_to_player = round(math.sqrt(((x_pos-item_x) ** 2) + ((y_pos-item_y) ** 2)),0)
            if distance_to_player < nearest_distance:
                nearest_distance = distance_to_player
                nearest_position = item
        nearest_position_running = getattr(getattr(fielding,nearest_position),'running')
        nearest_position_catching = getattr(getattr(fielding,nearest_position),'catching')
        fielder_to_ball = nearest_distance/nearest_position_running
        if time_in_air >= fielder_to_ball:
            if random.randint(0,100) <= nearest_position_catching:
                action = 'fly out'
                print(nearest_position,'caught the ball')
                return action 
            else:
                action = 'hit'
                print(nearest_position, 'missed!')
                return action
        else:
            print(nearest_position,'gets the ball hit to (',x_pos,',',y_pos,'). The ball is ',nearest_distance,'units away')
            return action
  

    
    

def main():

    database = r"smallballdb.db"
    conn = create_connection(database)
    homeid = 3
    awayid = 3
    hometeam = Team(homeid,conn)
    awayteam = Team(awayid,conn)
    atbat= awayteam
    fielding = hometeam
    action = None
    game = Scoreboard(homeid,awayid)
    walks = 0
    while game.inning <9:
        atbat= awayteam
        fielding = hometeam
        while game.outs <6:
            if atbat == awayteam:
                batterrating,playername,batter_running = batter(game.awayBatter,awayteam.lineup)
            elif atbat == hometeam:
                batterrating,playername,batter_running = batter(game.homeBatter,hometeam.lineup)


            while not (game.strike == 3 or game.ball == 4 or action=='hit' or action=='fly out'):
                action,distance,hitangle,hitlift = throw_pitch(fielding.P.throwing,batterrating)

                if action == 'hit':
                    # Homerun Hits take off between 25-30 degrees typically. 
                    # Groundball is <10 degrees, 
                    # Line drive is 10-25 degrees, 
                    # Fly ball is 25-50, 
                    # Pop up is 50 or higher                    
                    action = field_hit(batter_running,distance,hitlift,hitangle,fielding)

                if game.strike <3 and action == "foul":
                    game.Strike()
                if action == "strike":
                    game.Strike()
                elif action == "ball":
                    game.Ball()
                elif action == 'hit':
                    if atbat == awayteam:
                        game.AwayHit()
                    elif atbat == hometeam: 
                        game.HomeHit()
                    #field_hit(distance,hitangle,hitlift,fielding.lineup,batter_running)
            if game.strike == 3 or action == 'fly out' or action == 'out at first':
                game.Outs()
            elif game.ball == 4:
                if atbat == awayteam:
                    game.awayWalks = game.awayWalks + 1
                else:
                    game.homeWalks = game.homeWalks + 1
            # else:
            #     print(playername," gets a hit!")
            action = None
            game.ResetCount()
            if atbat == awayteam:
                game.nextawayBatter()
            else:
                game.nexthomeBatter()
            if game.outs == 3 and atbat == awayteam:
                atbat = hometeam
                fielding = awayteam
            elif game.outs == 6:
                atbat = awayteam
                fielding = hometeam
        game.ResetInning()
        game.nextInning()
    print('Away Hits - ',game.awayHits)
    print('Away Walks - ',game.awayWalks)
    print('Home Hits - ',game.homeHits)
    print('Home Walks - ',game.homeWalks)
    print ('Home Pitcher - ',hometeam.P.throwing,' | Away Pitcher - ',awayteam.P.throwing)
    
main()