import pyray as rl
from dataclasses import dataclass
from enum import Enum
from levels import create_levels

# Window settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

@dataclass
class Vector3:
    x: float
    y: float
    z: float

class GameState(Enum):
    PLAYING = 1
    GAME_OVER = 2
    LEVEL_COMPLETE = 3

class GameManager:
    def __init__(self, levels):
        self.levels = levels
        self.current_level = 0
        self.state = GameState.PLAYING
        self.current_level_data = self.levels[self.current_level]
        self.distance_traveled = 0
        self.high_score = 0

    def update(self, ball, delta_time):
        if self.state == GameState.PLAYING:
            # Update level elements
            self.current_level_data.update(delta_time)
            
            # Update distance traveled
            self.distance_traveled = ball.position.z
            
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
                        ball.speed_boost_timer = 5.0  # 5 seconds of speed boost
                        ball.score += 10

            # Check if level is complete (reached the end of the track)
            if ball.position.z >= 100:  # End of track
                self.state = GameState.LEVEL_COMPLETE
                if self.current_level < len(self.levels) - 1:
                    self.current_level += 1
                    self.current_level_data = self.levels[self.current_level]
                    ball.position = Vector3(0.0, 1.0, -10.0)  # Reset ball position
                    ball.velocity = Vector3(0.0, 0.0, 0.0)
                    self.state = GameState.PLAYING

        elif self.state == GameState.GAME_OVER:
            if rl.is_key_pressed(rl.KEY_R):
                self.reset_game(ball)

    def draw_level(self):
        self.current_level_data.draw()

    def draw_ui(self):
        # Draw score and distance
        rl.draw_text(f"Score: {int(self.distance_traveled)}", 10, 10, 20, rl.WHITE)
        rl.draw_text(f"High Score: {self.high_score}", 10, 40, 20, rl.WHITE)
        
        # Draw speed boost timer if active
        if self.state == GameState.PLAYING:
            rl.draw_text("Use LEFT/RIGHT to move, SPACE to jump", 
                     SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 30, 20, rl.WHITE)

        # Draw game over screen
        if self.state == GameState.GAME_OVER:
            text = "Game Over! Press R to restart"
            font_size = 40
            text_width = rl.measure_text(text, font_size)
            rl.draw_text(text, SCREEN_WIDTH//2 - text_width//2, 
                     SCREEN_HEIGHT//2 - font_size//2, font_size, rl.RED)

        # Draw level complete screen
        if self.state == GameState.LEVEL_COMPLETE:
            text = "Level Complete!"
            font_size = 40
            text_width = rl.measure_text(text, font_size)
            rl.draw_text(text, SCREEN_WIDTH//2 - text_width//2, 
                     SCREEN_HEIGHT//2 - font_size//2, font_size, rl.GREEN)

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
        ball.position = Vector3(0.0, 1.0, -10.0)
        ball.velocity = Vector3(0.0, 0.0, 0.0)
        ball.score = 0
        ball.has_speed_boost = False
        ball.speed_boost_timer = 0
        # Reset power-ups
        for power_up in self.current_level_data.power_ups:
            power_up.active = True
