from raylib import *
from dataclasses import dataclass

@dataclass
class Vector3:
    x: float
    y: float
    z: float

class Obstacle:
    def __init__(self, position, size, color):
        self.position = position
        self.size = size
        self.color = color

    def draw(self):
        draw_cube_v(
            Vector3(self.position.x, self.position.y, self.position.z),
            Vector3(self.size.x, self.size.y, self.size.z),
            self.color
        )

class PowerUp:
    def __init__(self, position, type_):
        self.position = position
        self.type = type_
        self.active = True
        self.radius = 0.5

    def draw(self):
        if self.active:
            color = GREEN if self.type == "speed_boost" else YELLOW
            draw_sphere_v(
                Vector3(self.position.x, self.position.y, self.position.z),
                self.radius,
                color
            )

class Level:
    def __init__(self, obstacles, power_ups, target_score):
        self.obstacles = obstacles
        self.power_ups = power_ups
        self.target_score = target_score

    def draw(self):
        for obstacle in self.obstacles:
            obstacle.draw()
        for power_up in self.power_ups:
            power_up.draw()

def create_levels():
    levels = []
    
    # Level 1 - Tutorial level
    level1_obstacles = [
        Obstacle(
            Vector3(0.0, 1.0, -5.0),
            Vector3(2.0, 2.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(5.0, 1.0, 0.0),
            Vector3(2.0, 2.0, 2.0),
            BROWN
        )
    ]
    
    level1_power_ups = [
        PowerUp(Vector3(3.0, 1.0, 3.0), "speed_boost")
    ]
    
    levels.append(Level(level1_obstacles, level1_power_ups, 100))
    
    # Level 2 - More challenging
    level2_obstacles = [
        Obstacle(
            Vector3(-5.0, 1.0, -5.0),
            Vector3(2.0, 3.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(5.0, 1.0, 5.0),
            Vector3(2.0, 3.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(0.0, 1.0, 0.0),
            Vector3(3.0, 1.0, 3.0),
            BROWN
        )
    ]
    
    level2_power_ups = [
        PowerUp(Vector3(-3.0, 1.0, 3.0), "speed_boost"),
        PowerUp(Vector3(3.0, 1.0, -3.0), "invincibility")
    ]
    
    levels.append(Level(level2_obstacles, level2_power_ups, 200))
    
    return levels
