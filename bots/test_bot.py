from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
import random

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
    
    def play_turn(self, rc: RobotController):
        corners = self.identify_corners(self.map.path)
        print(corners)
        self.build_towers(rc)
        self.towers_attack(rc)

    def get_path_coordinates(self):
        coords = []
        for x in range(self.map.width):
            for y in range(self.map.height):
                if self.map.is_path(x, y):
                    coords.append((x, y))
        return coords

    def identify_corners(self, points):
        corners = []
        #print(sorted_by_x)
        for i in range(2, len(points)):
            #diff x diff y:
            if (points[i][0] != points[i - 2][0] and points[i][1] !=points[i - 2][1]):
                corners.append(points[i-1])
        return corners
    
    def build_towers(self, rc: RobotController):
        x = random.randint(0, self.map.height-1)
        y = random.randint(0, self.map.height-1)
        tower = random.randint(1, 4) # randomly select a tower
        if (rc.can_build_tower(TowerType.GUNSHIP, x, y) and 
            rc.can_build_tower(TowerType.BOMBER, x, y) and
            rc.can_build_tower(TowerType.SOLAR_FARM, x, y) and
            rc.can_build_tower(TowerType.REINFORCER, x, y)
        ):
            if tower == 1:
                rc.build_tower(TowerType.BOMBER, x, y)
            elif tower == 2:
                rc.build_tower(TowerType.GUNSHIP, x, y)
            elif tower == 3:
                rc.build_tower(TowerType.SOLAR_FARM, x, y)
            elif tower == 4:
                rc.build_tower(TowerType.REINFORCER, x, y)
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
