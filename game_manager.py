from enum import Enum
from pyray import *
from levels import create_levels, Obstacle, PowerUp
import math
from random import randint

# Window settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

class GameState(Enum):
    PLAYING = 1
    GAME_OVER = 2
    LEVEL_COMPLETE = 3

from dataclasses import dataclass

@dataclass
class Vector3:
    x: float
    y: float
    z: float

class GameManager:
    def __init__(self, levels):
        self.levels = levels
        self.current_level = 0
        self.state = GameState.PLAYING
        self.current_level_data = self.levels[self.current_level]
        self.distance_traveled = 0
        self.high_score = 0
        self.chunk_size = 100  # Length of each repeating chunk
        self.active_chunks = []  # List of active level chunks
        self.last_chunk_z = 0  # Z position of the last generated chunk
        self.ball_position = Vector3(0.0, 1.0, 0.0)

    def update(self, ball, delta_time):
        if self.state == GameState.PLAYING:
            # Update level elements
            self.current_level_data.update(delta_time, ball.position)
            
            # Update distance traveled (negative because we move in negative Z)
            self.distance_traveled = -ball.position.z
            
            # Generate new chunks as needed
            while -ball.position.z + 100 > self.last_chunk_z:  # Keep 100 units ahead
                self.generate_new_chunk(ball)

            # Check collisions with obstacles
            for obstacle in self.current_level_data.obstacles:
                if self.check_collision_with_obstacle(ball, obstacle):
                    self.state = GameState.GAME_OVER
                    if ball.score > self.high_score:
                        self.high_score = ball.score
                    return

            # Check collisions with power-ups
            for power_up in self.current_level_data.power_ups:
                if power_up.active and self.check_collision_with_power_up(ball, power_up):
                    power_up.active = False
                    if power_up.type == "speed_boost":
                        ball.has_speed_boost = True
                        ball.speed_boost_timer = 5.0
                        ball.score += 10

        elif self.state == GameState.GAME_OVER:
            if is_key_pressed(KEY_R):
                self.reset_game(ball)

    def generate_new_chunk(self, ball):
        # Create a new chunk of obstacles and power-ups
        chunk_z = self.last_chunk_z + self.chunk_size
        
        # Add obstacles
        new_obstacles = []
        
        # Add random obstacle patterns
        pattern = randint(0, 3)
        
        if pattern == 0:
            # Slalom pattern
            slalom_x = 3.0
            for z in range(int(chunk_z), int(chunk_z + self.chunk_size), 15):
                new_obstacles.append(
                    Obstacle(
                        Vector3(slalom_x, 1.0, float(z)),
                        Vector3(2.0, 2.0, 2.0),
                        DARKBROWN
                    )
                )
                slalom_x *= -1
        elif pattern == 1:
            # Moving gate pattern
            gate_spacing = self.chunk_size / 3
            for i in range(3):
                z_pos = chunk_z + i * gate_spacing
                new_obstacles.append(
                    Obstacle(
                        Vector3(0.0, 1.0, z_pos),
                        Vector3(6.0, 2.0, 2.0),
                        MAROON,
                        moving=True,
                        move_range=3.0,
                        move_speed=2.0 + i * 0.5
                    )
                )
        elif pattern == 2:
            # Zigzag pattern
            for i in range(4):
                z_pos = chunk_z + i * (self.chunk_size/4)
                x_pos = 4.0 if i % 2 == 0 else -4.0
                new_obstacles.append(
                    Obstacle(
                        Vector3(x_pos, 1.0, z_pos),
                        Vector3(2.0, 2.0, 2.0),
                        PURPLE
                    )
                )
        else:
            # Narrow passage pattern
            z_pos = chunk_z + self.chunk_size/2
            new_obstacles.append(
                Obstacle(
                    Vector3(-4.0, 1.0, z_pos),
                    Vector3(2.0, 2.0, 8.0),
                    DARKBLUE
                )
            )
            new_obstacles.append(
                Obstacle(
                    Vector3(4.0, 1.0, z_pos),
                    Vector3(2.0, 2.0, 8.0),
                    DARKBLUE
                )
            )
        
        # Add all new obstacles to the current level
        self.current_level_data.obstacles.extend(new_obstacles)
        
        # Add power-ups between obstacles
        power_up_z = chunk_z + randint(20, int(self.chunk_size - 20))
        power_up_x = randint(-3, 3)
        self.current_level_data.power_ups.append(
            PowerUp(
                Vector3(float(power_up_x), 1.0, power_up_z),
                "speed_boost"
            )
        )
        
        # Update the last chunk position
        self.last_chunk_z = chunk_z
        
        # Clean up old obstacles and power-ups
        self.cleanup_old_elements(ball)

    def cleanup_old_elements(self, ball):
        # Remove obstacles that are far behind the ball
        self.current_level_data.obstacles = [
            obs for obs in self.current_level_data.obstacles
            if obs.position.z > ball.position.z - 50
        ]
        
        # Remove inactive or far power-ups
        self.current_level_data.power_ups = [
            pow for pow in self.current_level_data.power_ups
            if pow.active and pow.position.z > ball.position.z - 50
        ]

    def draw_level(self):
        self.current_level_data.draw(self.ball_position)

    def draw_ui(self):
        # Draw score and distance
        draw_text(f"Distance: {int(self.distance_traveled)}m", 10, 10, 20, WHITE)
        draw_text(f"High Score: {self.high_score}m", 10, 40, 20, WHITE)
        
        # Draw speed boost timer if active
        if self.state == GameState.PLAYING:
            draw_text("Use LEFT/RIGHT to move, SPACE to jump", 
                     SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 30, 20, WHITE)

        # Draw game over screen
        if self.state == GameState.GAME_OVER:
            text = "Game Over! Press R to restart"
            font_size = 40
            text_width = measure_text(text, font_size)
            draw_text(text, SCREEN_WIDTH//2 - text_width//2, 
                     SCREEN_HEIGHT//2 - font_size//2, font_size, RED)

    def check_collision_with_obstacle(self, ball, obstacle):
        # Simple AABB-Sphere collision
        closest_x = max(obstacle.position.x - obstacle.size.x/2, 
                       min(ball.position.x, obstacle.position.x + obstacle.size.x/2))
        closest_y = max(obstacle.position.y - obstacle.size.y/2, 
                       min(ball.position.y, obstacle.position.y + obstacle.size.y/2))
        closest_z = max(obstacle.position.z - obstacle.size.z/2, 
                       min(ball.position.z, obstacle.position.z + obstacle.size.z/2))
        
        distance = ((closest_x - ball.position.x) ** 2 + 
                   (closest_y - ball.position.y) ** 2 + 
                   (closest_z - ball.position.z) ** 2) ** 0.5
        
        return distance < ball.radius

    def check_collision_with_power_up(self, ball, power_up):
        distance = ((ball.position.x - power_up.position.x) ** 2 +
                   (ball.position.y - power_up.position.y) ** 2 +
                   (ball.position.z - power_up.position.z) ** 2) ** 0.5
        return distance < (ball.radius + power_up.radius)

    def reset_game(self, ball):
        self.current_level = 0
        self.current_level_data = self.levels[self.current_level]
        self.state = GameState.PLAYING
        ball.position = Vector3(0.0, 1.0, 0.0)
        ball.velocity = Vector3(0.0, 0.0, 0.0)
        ball.score = 0
        ball.has_speed_boost = False
        ball.speed_boost_timer = 0
        self.distance_traveled = 0
        self.last_chunk_z = 0
        # Reset power-ups
        for power_up in self.current_level_data.power_ups:
            power_up.active = True
