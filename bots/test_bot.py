from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
import random
from collections import deque

DEBUG = False

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.next_coords = deque()
        self.corners = self.identify_corners(self.map.path)
        corners = list(self.corners.keys())
        if len(corners) > 10:
            corners = random.sample(corners, 10)
        for c in corners:
            pot_tower_point = self.get_inner_point(self.corners[c][0], self.corners[c][1], c)
            self.next_coords.append((pot_tower_point, TowerType.BOMBER, 0))
        
    def add_neighbors(self, coords: tuple[int, int], tower: TowerType, depth: int, rc: RobotController):
        if depth < 2:
            for x in range(coords[0]-1, coords[0]+2):
                for y in range(coords[1]-1, coords[1]+2):
                    if (x,y) != coords:
                        if tower == TowerType.BOMBER:
                            newtower = random.choice([TowerType.GUNSHIP, TowerType.GUNSHIP, TowerType.GUNSHIP, TowerType.REINFORCER, TowerType.REINFORCER, TowerType.SOLAR_FARM])
                        elif tower == TowerType.GUNSHIP:
                            newtower = random.choice([TowerType.BOMBER, TowerType.BOMBER, TowerType.SOLAR_FARM, TowerType.GUNSHIP, TowerType.REINFORCER, TowerType.REINFORCER])
                        else:
                            continue 
                        if newtower == TowerType.SOLAR_FARM:
                            xs = random.randint(0, self.map.height-1)
                            ys = random.randint(0, self.map.height-1)
                            self.next_coords.append(((xs,ys), newtower, 0))
                            continue
                        self.next_coords.append(((x,y), newtower, depth+1))
        else:
            newCoords = self.get_random_edge(rc)
            if DEBUG:
                print("random edge", newCoords)
            if newCoords:
                self.next_coords.append((newCoords, TowerType.BOMBER, 0))
        

    
    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def get_inner_point(self, p1, p2, p3):
        X = p1[0]^ p2[0] ^ p3[0]
        Y = p1[1]^ p2[1] ^ p3[1]
        return (X,Y)

    def identify_corners(self, points):
        corners = {}
        for i in range(2, len(points)):
            #diff x diff y:
            if (points[i][0] != points[i - 2][0] and points[i][1] !=points[i - 2][1]):
                corners[points[i-1]] = [points[i], points[i-2]]
        return corners
    
    def get_random_edge(self, rc: RobotController):
        x,y = random.choice(self.map.path)
        for i in range(x-1, x+2):
            for j in range(y-1, y+2):
                if (i,j) != (x,y) and rc.is_placeable(rc.get_ally_team(), i, j):
                    return i,j
        return None
    
    def rush_debris(self, rc: RobotController):
        if DEBUG:
            print("RUSHING DEBRIS")
        while rc.can_send_debris(1, 50):
            rc.send_debris(1, 50)
        
    def build_towers(self, rc: RobotController):
        # print(self.next_coords)
        timeout = 10
        if rc.get_turn() < 10 or random.randint(0, 500) == 0:
            self.rush_debris(rc)
        while len(self.next_coords) > 0 and timeout > 0:
            if random.randint(0,100) == 0:
                if DEBUG:
                    print("promoting random tower")
                idx = random.randint(0, len(self.next_coords)-1)
                coords, tower, depth = self.next_coords[idx]
                del self.next_coords[idx]
            else:
                coords, tower, depth = self.next_coords.popleft()
            if rc.get_balance(rc.get_ally_team()) < tower.cost:
                self.next_coords.appendleft((coords, tower, depth))
                return
            if rc.can_build_tower(tower, coords[0], coords[1]):
                if DEBUG:
                    print("building tower", tower, "at", coords, "depth", depth)
                rc.build_tower(tower, coords[0], coords[1])
                self.add_neighbors(coords, tower, depth, rc)
                return
            timeout -= 1
        
        x,y = self.get_random_edge(rc)
        tower = random.choice([TowerType.GUNSHIP, TowerType.BOMBER, TowerType.REINFORCER])
        if (rc.can_build_tower(TowerType.GUNSHIP, x, y) and 
            rc.can_build_tower(TowerType.BOMBER, x, y) and
            rc.can_build_tower(TowerType.REINFORCER, x, y)
        ):
            rc.build_tower(tower, x, y)
            self.add_neighbors((x,y), tower, 0, rc)
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
