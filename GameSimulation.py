from importlib.util import module_for_loader
import random
import sqlite3
from sqlite3 import Error
from datetime import date
import pandas as pd
import math

# with open('testfile.csv','a') as f:
#     f.write('START GAME')
# #     f.write('\n')
# #     f.write("test,")

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
        self.running = round((running * (morale/100))/100 * 7 + 21)
        self.throwingspeed = round((throwing * (morale/100))/100 * 40 + 100)
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
        self.homeHR = 0
        self.awayHR = 0
        self.homeErrors = 0
        self.awayErrors = 0
        self.homeWalks = 0
        self.awayWalks = 0
        self.onFirst = []
        self.onSecond = []
        self.onThird = []
    def HomeHR(self):
        self.homeHR = self.homeHR + 1
        self.HomeRun()
    def AwayHR(self):
        self.awayHR = self.awayHR + 1
        self.AwayRun()
    def HomeRun(self):
        self.homeRuns = self.homeRuns + 1
    def AwayRun(self):
        self.awayRuns = self.awayRuns + 1
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
    batter_position = team.loc[team['player_lineup'] == lineupnumber]['player_pos'].values[0]
    return batterrating,player_name,batter_running,batter_position

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
    Bases = {'First': FirstBase, 'Second': SecondBase,'Third':ThirdBase,'Home':HomeBase}
    return FieldPositions, Bases

def calculate_distance(aX,aY,bX,bY):
    distance = round(math.sqrt(abs(((aX-bX) * (aX-bX))) + abs(((aY-bY) * (aY-bY)))),0)
    return distance

def time_of_flight(distance,liftangle):
    pass

def find_coordinates(distance,angle):
    x_pos = abs(round(distance * math.cos(angle)))
    y_pos = abs(round(distance * math.sin(angle)))
    position = [x_pos,y_pos]
    return position

def reset_bases():
    FirstRunner = None
    SecondRunner = None
    ThirdRunner = None
    return FirstRunner,SecondRunner,ThirdRunner

def advance_bases(FirstRunner,SecondRunner,ThirdRunner):
    ThirdRunner = SecondRunner
    SecondRunner = FirstRunner
    return SecondRunner,ThirdRunner


def field_hit(batter_running,batter_name,batter_position,distance,hitlift,hitangle,fielding,FirstRunner,SecondRunner,ThirdRunner):
    #In Play hit is angle 0 to 90 degrees
    # Homerun Hits take off between 25-30 degrees typically. 
    # Groundball is <10 degrees, 
    # Line drive is 10-25 degrees, 
    # Fly ball is 25-50, 
    # Pop up is 50 or higher
    hitangle = hitangle - 30
    if hitangle < 0 or hitangle > 90:
        action = 'foul'
        return action,FirstRunner,SecondRunner,ThirdRunner
    elif hitlift >= 50:
        action = 'fly out'
        return action,FirstRunner,SecondRunner,ThirdRunner
    else:
        print('Hit!')
        action = 'hit'
        #return action
        FieldPositions,Bases = reset_positions()
        batter_to_base = 90/batter_running
        time_in_air = round(abs((((distance * math.sin(hitlift))+(distance * math.sin(hitlift)))/(9.8*3.281))),2)
        air_distance = round(time_in_air*abs((distance * math.cos(hitlift))))
        if air_distance > 300:
            print('Home run!')
            action = 'home run'
            return action,FirstRunner,SecondRunner,ThirdRunner
        # print('The ball launched at ',hitlift,'degrees for ',air_distance,'ft in ',time_in_air)
        groundroll = distance*.3
        nearest_position = None
        nearest_distance = 1000
        ball_land = find_coordinates(air_distance,hitangle)
        ball_roll = find_coordinates(air_distance+groundroll,hitangle) 
        #print('Angle is ',hitangle,' to (',x_pos,',',y_pos,')')
        
        for item in FieldPositions:
            item_x = FieldPositions.get(item)[0]
            item_y = FieldPositions.get(item)[1]
            distance_to_player = calculate_distance(ball_land[0],ball_land[1],item_x,item_y)
            if distance_to_player <= nearest_distance:
                nearest_distance = distance_to_player
                nearest_position = item

        nearest_position_running = getattr(getattr(fielding,nearest_position),'running')
        nearest_position_catching = getattr(getattr(fielding,nearest_position),'catching')
        nearest_position_throwing = getattr(getattr(fielding,nearest_position),'throwingspeed')
        fielder_to_ball = nearest_distance/nearest_position_running
        if time_in_air >= fielder_to_ball:
            if random.randint(0,100) <= nearest_position_catching:
                action = 'fly out'
                print(nearest_position,'caught the ball')
                return action,FirstRunner,SecondRunner,ThirdRunner
            else:
                print(nearest_position, 'missed!') 

    #=========================================================================================================
    # ========================================================================================================
    # ========================================================================================================
    # BELOW THIS IS WHAT HAPPENS IF THE FIELDER CANNOT GET TO THE BALL IN TIME/MISSES THE CATCH               
    print(nearest_position,'gets the ball hit to (',ball_land[0],',',ball_land[1],'). The ball is ',nearest_distance,'units away')
    fielder_to_ball = calculate_distance(ball_roll[0],ball_roll[1],FieldPositions.get(nearest_position)[0],FieldPositions.get(nearest_position)[1])/nearest_position_running
    distance_to_base = calculate_distance(ball_roll[0],ball_roll[1],Bases.get('First')[0],Bases.get('First')[1])/nearest_position_throwing + 0.5
    if batter_to_base >= (fielder_to_ball+distance_to_base):
        print('out at first!')
        action = 'out at first'
    else:
        action = 'safe at first'
        FirstRunner = [batter_name,batter_position,batter_running]
    return action,FirstRunner,SecondRunner,ThirdRunner
  

    
    

def main():

    database = r"smallballdb.db"
    conn = create_connection(database)
    homeid = 2
    awayid = 2
    hometeam = Team(homeid,conn)
    awayteam = Team(awayid,conn)
    atbat= awayteam
    fielding = hometeam
    action = None
    game = Scoreboard(homeid,awayid)
    walks = 0
    FirstRunner,SecondRunner,ThirdRunner = reset_bases()
    while (game.inning <9) or (game.awayRuns == game.homeRuns and game.inning >=9):
        print('==========Top of ',game.inning+1,'==========')
        atbat= awayteam
        fielding = hometeam
        while game.outs <6:
            if atbat == awayteam:
                batterrating,playername,batter_running,batter_position = batter(game.awayBatter,awayteam.lineup)
            elif atbat == hometeam:
                batterrating,playername,batter_running,batter_position = batter(game.homeBatter,hometeam.lineup)
            print(playername,'(',batter_position,') steps up to the plate!')    


            while not (game.strike == 3 or game.ball == 4 or action=='hit' or action=='fly out'):
                action,distance,hitangle,hitlift = throw_pitch(fielding.P.throwing,batterrating)

                if action == 'hit':
                    # Homerun Hits take off between 25-30 degrees typically. 
                    # Groundball is <10 degrees, 
                    # Line drive is 10-25 degrees, 
                    # Fly ball is 25-50, 
                    # Pop up is 50 or higher                    
                    action,FirstRunner,SecondRunner,ThirdRunner = field_hit(batter_running,playername,batter_position,distance,hitlift,hitangle,fielding,FirstRunner,SecondRunner,ThirdRunner)

                if game.strike <2 and action == "foul":
                    game.Strike()
                    print('Foul ball!')
                    print(game.ball,'-',game.strike)
                if action == "strike":
                    game.Strike()
                    print('Strike!')
                    print(game.ball,'-',game.strike)
                elif action == "ball":
                    game.Ball()
                    print('Ball!')
                    print(game.ball,'-',game.strike)
                elif action == 'safe at first' or action == 'home run':
                    if atbat == awayteam:
                        game.AwayHit()
                        if action == 'home run':
                            game.AwayHR()
                            if FirstRunner != None:
                                game.AwayRun()
                            if SecondRunner != None:
                                game.AwayRun()
                            if ThirdRunner != None:
                                game.AwayRun()
                    elif atbat == hometeam: 
                        game.HomeHit()
                        if action == 'home run':
                            game.HomeHR()
                            print(playername,' scores!')
                            if FirstRunner != None:
                                game.HomeRun()
                                print(FirstRunner[0], ' scores!')
                            if SecondRunner != None:
                                game.HomeRun()
                                print(SecondRunner[0],' scores!')
                            if ThirdRunner != None:
                                game.HomeRun()
                                print(ThirdRunner[0],' scores!')
                    #field_hit(distance,hitangle,hitlift,fielding.lineup,batter_running)
            if game.strike == 3 or action == 'fly out' or action == 'out at first' or action == 'out at first':
                game.Outs()
                if action == 'out at first':
                    print(playername,'(',batter_position,')  is out at first')
                elif action == 'fly out':
                    print(playername,'(',batter_position,') flies out')
                else:
                    print(playername,'(',batter_position,') strikes out')   
            elif game.ball == 4:
                if atbat == awayteam:
                    game.awayWalks = game.awayWalks + 1 
                    if ThirdRunner != None:
                        game.AwayRun()  
                        print(ThirdRunner[0],' scores!')
                else:
                    game.homeWalks = game.homeWalks + 1
                    if ThirdRunner != None:
                        game.HomeRun()
                        print(ThirdRunner[0],' scores!')
                SecondRunner,ThirdRunner = advance_bases(FirstRunner,SecondRunner,ThirdRunner)
                FirstRunner = [playername,batter_running]

                print(playername,'(',batter_position,') walks') 
            action = None
            game.ResetCount()
            if atbat == awayteam:
                game.nextawayBatter()
            else:
                game.nexthomeBatter()
            if game.outs == 3 and atbat == awayteam:
                atbat = hometeam
                fielding = awayteam
                FirstRunner,SecondRunner,ThirdRunner = reset_bases()
                print('==========Bottom  of the ',game.inning+1,'==========')
            elif game.outs == 6:
                FirstRunner,SecondRunner,ThirdRunner = reset_bases()
                atbat = awayteam
                fielding = hometeam
        game.ResetInning()
        print('==========',game.inning+1,'inning End==========')
        game.nextInning()
    print('Away Hits - ',game.awayHits)
    print('Away Walks - ',game.awayWalks)
    print('Home Hits - ',game.homeHits)
    print('Home Walks - ',game.homeWalks)
    print ('Home Pitcher - ',hometeam.P.throwing,' | Away Pitcher - ',awayteam.P.throwing)
    print('Home Runs - ',game.homeRuns)
    print('Away Runs - ',game.awayRuns)
    
main()