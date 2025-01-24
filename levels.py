from pyray import *
from dataclasses import dataclass
import math

class Obstacle:
    def __init__(self, position, size, color, moving=False, move_range=0, move_speed=0):
        self.position = position
        self.size = size
        self.color = color
        self.moving = moving
        self.move_range = move_range
        self.move_speed = move_speed
        self.initial_position = Vector3(position.x, position.y, position.z)
        self.time = 0

    def update(self, delta_time):
        if self.moving:
            self.time += delta_time
            self.position.x = self.initial_position.x + math.sin(self.time * self.move_speed) * self.move_range

    def draw(self):
        draw_cube(self.position, self.size.x, self.size.y, self.size.z, self.color)

class PowerUp:
    def __init__(self, position, type_):
        self.position = position
        self.type = type_
        self.active = True
        self.radius = 0.5
        self.rotation = 0

    def update(self, delta_time):
        self.rotation += delta_time * 2  # Rotate the powerup

    def draw(self):
        if self.active:
            color = GREEN if self.type == "speed_boost" else YELLOW
            # Make powerup float up and down
            offset_y = math.sin(get_time() * 2) * 0.2
            draw_position = Vector3(
                self.position.x,
                self.position.y + offset_y,
                self.position.z
            )
            draw_sphere(draw_position, self.radius, color)

class Level:
    def __init__(self, obstacles, power_ups, target_score):
        self.obstacles = obstacles
        self.power_ups = power_ups
        self.target_score = target_score

    def update(self, delta_time):
        for obstacle in self.obstacles:
            obstacle.update(delta_time)
        for power_up in self.power_ups:
            power_up.update(delta_time)

    def draw(self):
        # Draw the track
        draw_plane(Vector3(0, 0, 0), Vector2(20, 100), DARKGRAY)  # Extended track
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw()
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw()

def create_levels():
    levels = []
    
    # Level 1 - Tutorial level with simple obstacles
    level1_obstacles = [
        # Stationary obstacles forming a slalom
        Obstacle(
            Vector3(-5.0, 1.0, 20.0),
            Vector3(3.0, 2.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(5.0, 1.0, 40.0),
            Vector3(3.0, 2.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(-5.0, 1.0, 60.0),
            Vector3(3.0, 2.0, 2.0),
            BROWN
        ),
        # Moving obstacle
        Obstacle(
            Vector3(0.0, 1.0, 80.0),
            Vector3(4.0, 2.0, 2.0),
            RED,
            moving=True,
            move_range=4.0,
            move_speed=2.0
        )
    ]
    
    level1_power_ups = [
        PowerUp(Vector3(3.0, 1.0, 30.0), "speed_boost"),
        PowerUp(Vector3(-3.0, 1.0, 50.0), "speed_boost"),
        PowerUp(Vector3(0.0, 1.0, 70.0), "speed_boost")
    ]
    
    levels.append(Level(level1_obstacles, level1_power_ups, 100))
    
    # Level 2 - More challenging with moving obstacles
    level2_obstacles = [
        # Moving obstacles creating a challenging pattern
        Obstacle(
            Vector3(-4.0, 1.0, 20.0),
            Vector3(3.0, 3.0, 2.0),
            RED,
            moving=True,
            move_range=3.0,
            move_speed=3.0
        ),
        Obstacle(
            Vector3(4.0, 1.0, 40.0),
            Vector3(3.0, 3.0, 2.0),
            RED,
            moving=True,
            move_range=3.0,
            move_speed=2.0
        ),
        # Stationary obstacles creating narrow passages
        Obstacle(
            Vector3(-6.0, 1.0, 60.0),
            Vector3(2.0, 4.0, 2.0),
            BROWN
        ),
        Obstacle(
            Vector3(6.0, 1.0, 60.0),
            Vector3(2.0, 4.0, 2.0),
            BROWN
        ),
        # Final moving obstacle
        Obstacle(
            Vector3(0.0, 1.0, 80.0),
            Vector3(6.0, 2.0, 2.0),
            RED,
            moving=True,
            move_range=5.0,
            move_speed=4.0
        )
    ]
    
    level2_power_ups = [
        PowerUp(Vector3(-3.0, 1.0, 30.0), "speed_boost"),
        PowerUp(Vector3(3.0, 1.0, 50.0), "speed_boost"),
        PowerUp(Vector3(0.0, 1.0, 70.0), "speed_boost")
    ]
    
    levels.append(Level(level2_obstacles, level2_power_ups, 200))
    
    return levels
