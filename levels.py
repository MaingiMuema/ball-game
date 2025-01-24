from pyray import *
import math

class Obstacle:
    def __init__(self, position, size, color, moving=False, move_range=0.0, move_speed=0.0):
        self.position = position
        self.size = size
        self.color = color
        self.moving = moving
        self.move_range = move_range
        self.move_speed = move_speed
        self.initial_x = position.x
        self.time = 0

    def update(self, delta_time):
        if self.moving:
            self.time += delta_time
            self.position.x = self.initial_x + math.sin(self.time * self.move_speed) * self.move_range

    def draw(self):
        draw_cube(
            (self.position.x, self.position.y, self.position.z),
            self.size.x, self.size.y, self.size.z,
            self.color
        )

class PowerUp:
    def __init__(self, position, type):
        self.position = position
        self.type = type
        self.radius = 0.5
        self.active = True
        self.rotation = 0

    def update(self, delta_time):
        if self.active:
            self.rotation += 90.0 * delta_time  # Rotate 90 degrees per second
            self.position.y = self.position.y + math.sin(get_time() * 2) * 0.01  # Float up and down

    def draw(self):
        if self.active:
            # Draw a rotating cube for power-up
            draw_cube(
                (self.position.x, self.position.y, self.position.z),
                0.8, 0.8, 0.8,
                GOLD
            )

class Level:
    def __init__(self):
        self.obstacles = []
        self.power_ups = []
        self.road_segments = []  # Store road segment positions
        self.last_segment_z = 0  # Track the last generated segment position
        self.segment_length = 20.0
        self.road_width = 10.0
        self.next_obstacle_z = 0  # Track next obstacle position

    def update(self, delta_time, ball_position):
        # Update obstacles and power-ups
        for obstacle in self.obstacles:
            obstacle.update(delta_time)
        for power_up in self.power_ups:
            power_up.update(delta_time)
            
        # Generate new road segments ahead
        while self.last_segment_z > ball_position.z - 400:  # Keep 400 units ahead
            self.generate_road_segment()
            
        # Generate obstacles
        while self.next_obstacle_z > ball_position.z - 300:  # Keep obstacles 300 units ahead
            self.generate_obstacle()
            
        # Remove old segments and obstacles
        self.cleanup(ball_position)

    def generate_road_segment(self):
        self.last_segment_z -= self.segment_length
        self.road_segments.append(self.last_segment_z)

    def generate_obstacle(self):
        from random import choice, random, randint
        
        # Different obstacle patterns
        patterns = [
            self.create_slalom_obstacle,
            self.create_moving_gate,
            self.create_narrow_passage,
            self.create_jumping_obstacle
        ]
        
        # Choose and create a random pattern
        chosen_pattern = choice(patterns)
        chosen_pattern()
        
        # Update next obstacle position
        self.next_obstacle_z -= randint(30, 50)  # Variable spacing between obstacles

    def create_slalom_obstacle(self):
        x_pos = 3.0 if len(self.obstacles) % 2 == 0 else -3.0
        self.obstacles.append(
            Obstacle(
                Vector3(x_pos, 1.0, self.next_obstacle_z),
                Vector3(2.0, 2.0, 2.0),
                DARKBROWN
            )
        )

    def create_moving_gate(self):
        self.obstacles.append(
            Obstacle(
                Vector3(0.0, 1.0, self.next_obstacle_z),
                Vector3(6.0, 2.0, 2.0),
                MAROON,
                moving=True,
                move_range=3.0,
                move_speed=2.0
            )
        )

    def create_narrow_passage(self):
        self.obstacles.append(
            Obstacle(
                Vector3(-4.0, 1.0, self.next_obstacle_z),
                Vector3(1.5, 2.0, 4.0),
                DARKBLUE
            )
        )
        self.obstacles.append(
            Obstacle(
                Vector3(4.0, 1.0, self.next_obstacle_z),
                Vector3(1.5, 2.0, 4.0),
                DARKBLUE
            )
        )

    def create_jumping_obstacle(self):
        self.obstacles.append(
            Obstacle(
                Vector3(0.0, 0.5, self.next_obstacle_z),
                Vector3(4.0, 1.0, 2.0),
                PURPLE
            )
        )

    def cleanup(self, ball_position):
        # Keep only segments within range
        self.road_segments = [seg for seg in self.road_segments 
                            if seg > ball_position.z - 200]  # Keep 200 units behind
        
        # Remove old obstacles
        self.obstacles = [obs for obs in self.obstacles 
                         if obs.position.z > ball_position.z - 100]  # Keep 100 units behind
        
        # Remove old power-ups
        self.power_ups = [pow for pow in self.power_ups 
                         if pow.active and pow.position.z > ball_position.z - 100]

    def draw(self, ball_position):
        # Draw road segments
        for segment_z in self.road_segments:
            # Draw road surface
            draw_cube(
                (0.0, -0.5, segment_z - self.segment_length/2),
                self.road_width, 0.5, self.segment_length,
                DARKGRAY
            )
            # Draw side barriers
            draw_cube(
                (self.road_width/2 + 0.5, 0.5, segment_z - self.segment_length/2),
                1.0, 1.0, self.segment_length,
                BLUE
            )
            draw_cube(
                (-self.road_width/2 - 0.5, 0.5, segment_z - self.segment_length/2),
                1.0, 1.0, self.segment_length,
                BLUE
            )
        
        # Draw space background (stars)
        for i in range(200):  # Increased number of stars
            star_x = math.sin(i * 1.1) * 50
            star_y = math.cos(i * 0.9) * 30
            star_z = ((get_time() * 20 + i * 10) % 400) - 400 + ball_position.z
            draw_cube(
                (star_x, star_y, star_z),
                0.2, 0.2, 0.2,
                WHITE
            )
        
        # Draw obstacles and power-ups
        for obstacle in self.obstacles:
            obstacle.draw()
        for power_up in self.power_ups:
            power_up.draw()

def create_levels():
    levels = []
    
    # Create level 1
    level1 = Level()
    
    # Add initial obstacles
    level1.obstacles.append(
        Obstacle(
            Vector3(5.0, 1.0, 20.0),
            Vector3(3.0, 2.0, 2.0),
            DARKBROWN
        )
    )
    
    level1.obstacles.append(
        Obstacle(
            Vector3(-5.0, 1.0, 40.0),
            Vector3(3.0, 2.0, 2.0),
            DARKBROWN
        )
    )
    
    level1.obstacles.append(
        Obstacle(
            Vector3(0.0, 1.0, 60.0),
            Vector3(4.0, 2.0, 2.0),
            MAROON,
            moving=True,
            move_range=4.0,
            move_speed=2.0
        )
    )
    
    # Add power-ups
    level1.power_ups.append(
        PowerUp(
            Vector3(0.0, 1.0, 30.0),
            "speed_boost"
        )
    )
    
    levels.append(level1)
    
    # Create level 2
    level2 = Level()
    
    # Add initial obstacles
    level2.obstacles.append(
        Obstacle(
            Vector3(-4.0, 1.0, 20.0),
            Vector3(3.0, 3.0, 2.0),
            RED,
            moving=True,
            move_range=3.0,
            move_speed=3.0
        )
    )
    
    level2.obstacles.append(
        Obstacle(
            Vector3(4.0, 1.0, 40.0),
            Vector3(3.0, 3.0, 2.0),
            RED,
            moving=True,
            move_range=3.0,
            move_speed=2.0
        )
    )
    
    level2.obstacles.append(
        Obstacle(
            Vector3(-6.0, 1.0, 60.0),
            Vector3(2.0, 4.0, 2.0),
            BROWN
        )
    )
    
    level2.obstacles.append(
        Obstacle(
            Vector3(6.0, 1.0, 60.0),
            Vector3(2.0, 4.0, 2.0),
            BROWN
        )
    )
    
    level2.obstacles.append(
        Obstacle(
            Vector3(0.0, 1.0, 80.0),
            Vector3(6.0, 2.0, 2.0),
            RED,
            moving=True,
            move_range=5.0,
            move_speed=4.0
        )
    )
    
    # Add power-ups
    level2.power_ups.append(
        PowerUp(
            Vector3(-3.0, 1.0, 30.0),
            "speed_boost"
        )
    )
    
    level2.power_ups.append(
        PowerUp(
            Vector3(3.0, 1.0, 50.0),
            "speed_boost"
        )
    )
    
    level2.power_ups.append(
        PowerUp(
            Vector3(0.0, 1.0, 70.0),
            "speed_boost"
        )
    )
    
    levels.append(level2)
    
    return levels
