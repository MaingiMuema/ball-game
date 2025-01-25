from pyray import *
from random import choice, random, randint, uniform
import math

class Obstacle:
    def __init__(self, position, size, color, moving=False, move_range=0.0, move_speed=0.0, spinning=False, spin_radius=0.0, spin_speed=0.0):
        self.position = position
        self.size = size
        self.color = color
        self.moving = moving
        self.move_range = move_range
        self.move_speed = move_speed
        self.initial_x = position.x
        self.time = 0
        self.spinning = spinning
        self.spin_radius = spin_radius
        self.spin_speed = spin_speed
        self.spin_angle = 0

    def update(self, delta_time):
        if self.moving:
            self.time += delta_time
            self.position.x = self.initial_x + math.sin(self.time * self.move_speed) * self.move_range
        if self.spinning:
            self.spin_angle += self.spin_speed * delta_time
            self.position.x = self.spin_radius * math.cos(self.spin_angle)

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

class Particle:
    def __init__(self, position, velocity, color, life_time, size=0.2):
        self.position = position
        self.velocity = velocity
        self.color = color
        self.life_time = life_time
        self.max_life = life_time
        self.size = size

    def update(self, delta_time):
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time
        self.position.z += self.velocity.z * delta_time
        self.life_time -= delta_time
        
        # Add gravity effect
        self.velocity.y -= 9.8 * delta_time

    def draw(self):
        alpha = self.life_time / self.max_life
        color = Color(
            self.color[0],
            self.color[1],
            self.color[2],
            int(255 * alpha)
        )
        draw_sphere(
            (self.position.x, self.position.y, self.position.z),
            self.size * alpha,
            color
        )

class Level:
    def __init__(self):
        self.obstacles = []
        self.power_ups = []
        self.road_segments = []
        self.particles = []
        self.last_segment_z = 0
        self.segment_length = 20.0
        self.road_width = 10.0
        self.next_obstacle_z = -50
        self.obstacle_start_distance = -50
        self.difficulty = 1.0
        self.score_multiplier = 1.0
        self.combo_multiplier = 1.0
        self.combo_timer = 0
        self.combo_count = 0
        
        # Generate initial road segments
        for i in range(40):
            self.generate_road_segment()

    def update(self, delta_time, ball_position):
        # Update difficulty and multipliers
        self.difficulty = 1.0 + abs(ball_position.z) / 500.0
        self.score_multiplier = 1.0 + abs(ball_position.z) / 1000.0
        
        # Update combo system
        if self.combo_timer > 0:
            self.combo_timer -= delta_time
            if self.combo_timer <= 0:
                self.reset_combo()
        
        # Update particles
        self.particles = [p for p in self.particles if p.life_time > 0]
        for particle in self.particles:
            particle.update(delta_time)
        
        # Update game objects
        for obstacle in self.obstacles:
            obstacle.update(delta_time)
        for power_up in self.power_ups:
            power_up.update(delta_time)
            
        # Generate road and obstacles
        while self.last_segment_z > ball_position.z - 800:
            self.generate_road_segment()
            
        if ball_position.z <= self.obstacle_start_distance:
            while self.next_obstacle_z > ball_position.z - 400:
                self.generate_obstacle()
            
        # Cleanup
        self.cleanup(ball_position)

    def add_particle_effect(self, position, type="collect"):
        if type == "collect":
            for _ in range(20):
                angle = uniform(0, math.pi * 2)
                speed = uniform(5.0, 10.0)
                self.particles.append(
                    Particle(
                        Vector3(position.x, position.y, position.z),
                        Vector3(
                            math.cos(angle) * speed,
                            uniform(5.0, 10.0),
                            math.sin(angle) * speed
                        ),
                        GOLD,
                        0.5
                    )
                )
        elif type == "combo":
            for _ in range(30):
                angle = uniform(0, math.pi * 2)
                speed = uniform(8.0, 15.0)
                self.particles.append(
                    Particle(
                        Vector3(position.x, position.y, position.z),
                        Vector3(
                            math.cos(angle) * speed,
                            uniform(8.0, 15.0),
                            math.sin(angle) * speed
                        ),
                        PURPLE,
                        0.8
                    )
                )

    def add_combo(self):
        self.combo_count += 1
        self.combo_timer = 3.0  # Reset combo timer
        self.combo_multiplier = min(4.0, 1.0 + self.combo_count * 0.5)  # Max 4x multiplier
        if self.combo_count >= 3:  # Particle effect for combos of 3 or more
            self.add_particle_effect(ball.position, "combo")

    def reset_combo(self):
        self.combo_count = 0
        self.combo_multiplier = 1.0
        self.combo_timer = 0

    def generate_obstacle(self):
        from random import choice, random, randint, uniform
        
        # Number of obstacles based on difficulty
        max_obstacles = min(3, int(1 + self.difficulty / 2))
        num_obstacles = randint(1, max_obstacles)
        
        for _ in range(num_obstacles):
            patterns = [
                (self.create_slalom_obstacle, 0.25),
                (self.create_moving_gate, 0.25),
                (self.create_narrow_passage, 0.15),
                (self.create_jumping_obstacle, 0.2),
                (self.create_spinning_obstacle, 0.15)  # New obstacle type
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
        if random() < 0.3:
            power_up_types = [
                ("speed_boost", 0.3),
                ("shield", 0.25),
                ("points", 0.25),
                ("magnet", 0.2)
            ]
            
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
        
        # Update next obstacle position
        min_space = max(20, 40 - self.difficulty * 2)
        max_space = max(30, 60 - self.difficulty * 2)
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

    def create_spinning_obstacle(self):
        # Create a spinning obstacle that rotates around the center
        radius = uniform(2.0, 3.5)
        self.obstacles.append(
            Obstacle(
                Vector3(0.0, 1.0, self.next_obstacle_z),
                Vector3(4.0, 0.5, 0.5),
                RED,
                spinning=True,
                spin_radius=radius,
                spin_speed=uniform(2.0, 3.0 + self.difficulty)
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

    def generate_road_segment(self):
        self.last_segment_z -= self.segment_length
        self.road_segments.append(self.last_segment_z)

    def draw(self, ball_position):
        # Draw road segments
        for z in self.road_segments:
            draw_cube(
                (0.0, -0.5, z),
                10.0, 1.0, self.segment_length,
                DARKGRAY
            )
            # Road markings
            draw_cube(
                (0.0, 0.01, z),
                0.5, 0.1, self.segment_length * 0.5,
                YELLOW
            )
            # Side barriers with glow
            barrier_color = Color(41, 41, 41, 255)  # Dark gray
            glow_size = 1.0 + abs(math.sin(get_time() * 2 + z * 0.1)) * 0.1
            for x in [-5, 5]:
                draw_cube(
                    (x, 1.0, z),
                    0.5 * glow_size, 2.0 * glow_size, self.segment_length,
                    fade(barrier_color, 0.7)
                )
                draw_cube(
                    (x, 1.0, z),
                    0.3, 1.8, self.segment_length,
                    barrier_color
                )

        # Draw obstacles and power-ups
        for obstacle in self.obstacles:
            obstacle.draw()
        for power_up in self.power_ups:
            power_up.draw()
            
        # Draw particles
        for particle in self.particles:
            particle.draw()

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
