from pyray import *
from random import choice, random, randint, uniform
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
        self.hover_offset = 0
        
        # Set color based on power-up type
        if type == "speed_boost":
            self.color = GOLD
        elif type == "shield":
            self.color = SKYBLUE
        elif type == "points":
            self.color = GREEN
        elif type == "magnet":
            self.color = PURPLE

    def update(self, delta_time):
        if self.active:
            self.rotation += 90.0 * delta_time
            self.hover_offset = math.sin(get_time() * 4) * 0.3  # Faster and more pronounced hover

    def draw(self):
        if self.active:
            # Draw power-up with glow effect
            glow_size = 1.0 + abs(math.sin(get_time() * 3)) * 0.2
            draw_cube(
                (self.position.x, self.position.y + self.hover_offset, self.position.z),
                0.8 * glow_size, 0.8 * glow_size, 0.8 * glow_size,
                fade(self.color, 0.5)
            )
            # Inner cube
            draw_cube(
                (self.position.x, self.position.y + self.hover_offset, self.position.z),
                0.5, 0.5, 0.5,
                self.color
            )

class Level:
    def __init__(self):
        self.obstacles = []
        self.power_ups = []
        self.road_segments = []
        self.last_segment_z = 0
        self.segment_length = 20.0
        self.road_width = 10.0
        self.next_obstacle_z = -50
        self.obstacle_start_distance = -50
        self.difficulty = 1.0  # Starting difficulty
        self.score_multiplier = 1.0
        
        # Generate initial road segments only
        for i in range(40):
            self.generate_road_segment()

    def update(self, delta_time, ball_position):
        # Update difficulty based on distance
        self.difficulty = 1.0 + abs(ball_position.z) / 500.0  # Increase difficulty every 500 units
        self.score_multiplier = 1.0 + abs(ball_position.z) / 1000.0  # Increase score multiplier with distance
        
        # Update existing obstacles and power-ups
        for obstacle in self.obstacles:
            obstacle.update(delta_time)
        for power_up in self.power_ups:
            power_up.update(delta_time)
            
        # Generate road segments ahead
        while self.last_segment_z > ball_position.z - 800:
            self.generate_road_segment()
            
        # Generate obstacles after start distance
        if ball_position.z <= self.obstacle_start_distance:
            while self.next_obstacle_z > ball_position.z - 400:
                self.generate_obstacle()
            
        # Cleanup old elements
        self.cleanup(ball_position)

    def generate_road_segment(self):
        self.last_segment_z -= self.segment_length
        self.road_segments.append(self.last_segment_z)

    def generate_obstacle(self):
        from random import choice, random, randint, uniform
        
        # Number of obstacles increases with difficulty
        max_obstacles = min(3, int(1 + self.difficulty / 2))
        num_obstacles = randint(1, max_obstacles)
        
        for _ in range(num_obstacles):
            patterns = [
                (self.create_slalom_obstacle, 0.3),
                (self.create_moving_gate, 0.25),
                (self.create_narrow_passage, 0.2),
                (self.create_jumping_obstacle, 0.25)
            ]
            
            total_weight = sum(weight for _, weight in patterns)
            r = uniform(0, total_weight)
            current_weight = 0
            
            for pattern, weight in patterns:
                current_weight += weight
                if r <= current_weight:
                    pattern()
                    break
        
        # Power-up generation
        if random() < 0.3:  # 30% chance for power-up
            power_up_types = [
                ("speed_boost", 0.4),
                ("shield", 0.3),
                ("points", 0.2),
                ("magnet", 0.1)
            ]
            
            # Choose power-up type based on weights
            total_weight = sum(weight for _, weight in power_up_types)
            r = uniform(0, total_weight)
            current_weight = 0
            
            for p_type, weight in power_up_types:
                current_weight += weight
                if r <= current_weight:
                    self.power_ups.append(
                        PowerUp(
                            Vector3(uniform(-3, 3), 1.0, self.next_obstacle_z),
                            p_type
                        )
                    )
                    break
        
        # Update next obstacle position with spacing based on difficulty
        min_space = max(20, 40 - self.difficulty * 2)  # Decrease minimum space with difficulty
        max_space = max(30, 60 - self.difficulty * 2)  # Decrease maximum space with difficulty
        self.next_obstacle_z -= randint(int(min_space), int(max_space))

    def create_slalom_obstacle(self):
        x_pos = uniform(2.0, 4.0) * (-1 if len(self.obstacles) % 2 == 0 else 1)
        self.obstacles.append(
            Obstacle(
                Vector3(x_pos, 1.0, self.next_obstacle_z),
                Vector3(2.0, 2.0, 2.0),
                DARKBROWN,
                moving=random() < 0.3  # 30% chance to be moving
            )
        )

    def create_moving_gate(self):
        speed = min(4.0, 2.0 + self.difficulty * 0.5)  # Speed increases with difficulty
        self.obstacles.append(
            Obstacle(
                Vector3(0.0, 1.0, self.next_obstacle_z),
                Vector3(6.0, 2.0, 2.0),
                MAROON,
                moving=True,
                move_range=uniform(2.0, 4.0),
                move_speed=speed
            )
        )

    def create_narrow_passage(self):
        gap_size = uniform(2.5, 3.5)
        offset = uniform(-2.0, 2.0)  # Random position of the gap
        self.obstacles.append(
            Obstacle(
                Vector3(-4.0 + offset, 1.0, self.next_obstacle_z),
                Vector3(2.0, 2.0, 3.0),
                DARKBLUE
            )
        )
        self.obstacles.append(
            Obstacle(
                Vector3(4.0 + offset, 1.0, self.next_obstacle_z),
                Vector3(2.0, 2.0, 3.0),
                DARKBLUE
            )
        )

    def create_jumping_obstacle(self):
        width = uniform(3.0, 5.0)
        x_offset = uniform(-2.0, 2.0)
        self.obstacles.append(
            Obstacle(
                Vector3(x_offset, 0.5, self.next_obstacle_z),
                Vector3(width, 1.0, 2.0),
                PURPLE
            )
        )

    def cleanup(self, ball_position):
        # Keep more road segments for smoother visuals
        self.road_segments = [seg for seg in self.road_segments 
                            if seg > ball_position.z - 400]  # Increased kept segments
        
        # Clean up old obstacles
        self.obstacles = [obs for obs in self.obstacles 
                         if obs.position.z > ball_position.z - 200]
        
        # Clean up old power-ups
        self.power_ups = [pow for pow in self.power_ups 
                         if pow.active and pow.position.z > ball_position.z - 200]

    def draw(self, ball_position):
        # Draw road segments
        for segment_z in self.road_segments:
            # Draw road surface with slight color variation for visual interest
            color_variation = (segment_z % 40) / 40  # Creates a subtle pattern
            road_color = Color(
                int(40 + color_variation * 20),
                int(40 + color_variation * 20),
                int(40 + color_variation * 20),
                255
            )
            
            # Draw road surface
            draw_cube(
                (0.0, -0.5, segment_z - self.segment_length/2),
                self.road_width, 0.5, self.segment_length,
                road_color
            )
            
            # Draw side barriers with glowing effect
            glow = abs(math.sin(get_time() * 2 + segment_z * 0.1)) * 0.5 + 0.5
            barrier_color = Color(
                int(0 + glow * 100),
                int(100 + glow * 155),
                int(200 + glow * 55),
                255
            )
            
            draw_cube(
                (self.road_width/2 + 0.5, 0.5, segment_z - self.segment_length/2),
                1.0, 1.0, self.segment_length,
                barrier_color
            )
            draw_cube(
                (-self.road_width/2 - 0.5, 0.5, segment_z - self.segment_length/2),
                1.0, 1.0, self.segment_length,
                barrier_color
            )
        
        # Draw space background with more stars and parallax effect
        for i in range(300):  # More stars
            depth_factor = (i % 3 + 1) * 0.5  # Creates 3 layers of stars
            star_x = math.sin(i * 1.1) * 50 * depth_factor
            star_y = math.cos(i * 0.9) * 30 * depth_factor
            star_z = ((get_time() * 20 * depth_factor + i * 10) % 600) - 600 + ball_position.z
            
            # Star color varies with depth
            star_brightness = int(255 * (1 - depth_factor * 0.3))
            star_color = Color(star_brightness, star_brightness, star_brightness, 255)
            
            draw_cube(
                (star_x, star_y, star_z),
                0.2 * depth_factor, 0.2 * depth_factor, 0.2 * depth_factor,
                star_color
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
