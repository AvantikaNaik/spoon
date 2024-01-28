from collections import defaultdict
import random
from src.game_constants import SnipePriority, TowerType
from src.robot_controller import RobotController
from src.player import Player
from src.map import Map

class Path():
    def __init__(self, x: int, y: int, corner: int):
        self.coords = (x,y)
        self.corner = corner
    
    def get_free(self, rc: RobotController):
        team = rc.get_ally_team()
        x,y = self.coords
        if self.corner == 1:
            if rc.is_placeable(team, x+1, y+1):
                return (x+1, y+1)
            elif rc.is_placeable(team, x+2, y+2):
                return (x+2, y+2)
        elif self.corner == 2:
            if rc.is_placeable(team, x-1, y+1):
                return (x-1, y+1)
            elif rc.is_placeable(team, x-2, y+2):
                return (x-2, y+2)
        elif self.corner == 3:
            if rc.is_placeable(team, x-1, y-1):
                return (x-1, y-1)
            elif rc.is_placeable(team, x-2, y-2):
                return (x-2, y-2)
        elif self.corner == 4:
            if rc.is_placeable(team, x+1, y-1):
                return (x+1, y-1)
            elif rc.is_placeable(team, x+2, y-2):
                return (x+2, y-2)
        timeout = 10
        while not rc.is_placeable(team, x,y) and timeout > 0:
            x = random.randint(x-2, x+2)
            y = random.randint(y-2, y+2)
            timeout -= 1
            return x,y
        return -1,-1

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.num_solar = 0
        self.num_sent = 0
        self.num_guns = 0
        self.path = map.path
        self.pathObjs = []
        self.corners = self.identify_corners(self.path)
        for (x,y) in self.path:
            self.pathObjs.append(Path(x,y,self.corners[(x,y)]))
            

    def identify_corners(self, points):
        corners = defaultdict(int)
        #print(sorted_by_x)
        for i in range(2, len(points)):
            #diff x diff y:
            dir = 1
            if (points[i][0] != points[i - 2][0] and points[i][1] !=points[i - 2][1]):
                corners[points[i-1]] = dir
        return corners
    
    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def get_next2path(self, rc: RobotController):
        x,y = random.choice(self.pathObjs).get_free(rc)
        return x,y

    def build_towers(self, rc: RobotController):
        x = random.randint(0, self.map.height-1)
        y = random.randint(0, self.map.height-1)
        if self.num_solar >= 5 + self.num_sent and rc.can_send_debris(2,200):
            rc.send_debris(5,300)
            self.num_sent += 1
        if self.num_solar < 5 + self.num_sent and rc.can_build_tower(TowerType.SOLAR_FARM, x, y):
            rc.build_tower(TowerType.SOLAR_FARM, x, y)
            self.num_solar += 1
        else:
            unselected = True
            timeout = 5
            if self.num_guns * 7 < self.num_solar:
                x,y = 0,0
                while unselected and timeout > 0:
                    x,y = self.get_next2path(rc)
                    if rc.can_build_tower(TowerType.BOMBER, x-1, y-1):
                        unselected = False
                    timeout -= 1
                if rc.can_build_tower(TowerType.BOMBER, x-1, y-1):
                    rc.build_tower(TowerType.BOMBER, x-1, y-1)
                    self.num_guns += 1

    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
