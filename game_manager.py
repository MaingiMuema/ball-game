import pyray as rl
from dataclasses import dataclass
from levels import create_levels

# Window settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

@dataclass
class Vector3:
    x: float
    y: float
    z: float

class GameState:
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    LEVEL_COMPLETE = 4

class GameManager:
    def __init__(self):
        self.state = GameState.MENU
        self.levels = create_levels()
        self.current_level = 0
        self.reset_level()

    def reset_level(self):
        self.current_level_data = self.levels[self.current_level]
        
    def update(self, ball, delta_time):
        if self.state == GameState.PLAYING:
            # Check collisions with obstacles
            for obstacle in self.current_level_data.obstacles:
                if self.check_collision_with_obstacle(ball, obstacle):
                    ball.velocity = Vector3(
                        ball.velocity.x * -0.8,
                        max(ball.velocity.y, 5.0),  # Bounce up
                        ball.velocity.z
                    )
                    ball.score += 10

            # Check collisions with power-ups
            for power_up in self.current_level_data.power_ups:
                if power_up.active and self.check_collision_with_power_up(ball, power_up):
                    self.apply_power_up(ball, power_up)
                    power_up.active = False

            # Check if level is complete
            if ball.score >= self.current_level_data.target_score:
                self.state = GameState.LEVEL_COMPLETE

    def check_collision_with_obstacle(self, ball, obstacle):
        # Simple AABB collision check
        ball_min = Vector3(
            ball.position.x - ball.radius,
            ball.position.y - ball.radius,
            ball.position.z - ball.radius
        )
        ball_max = Vector3(
            ball.position.x + ball.radius,
            ball.position.y + ball.radius,
            ball.position.z + ball.radius
        )
        
        obstacle_min = Vector3(
            obstacle.position.x - obstacle.size.x/2,
            obstacle.position.y - obstacle.size.y/2,
            obstacle.position.z - obstacle.size.z/2
        )
        obstacle_max = Vector3(
            obstacle.position.x + obstacle.size.x/2,
            obstacle.position.y + obstacle.size.y/2,
            obstacle.position.z + obstacle.size.z/2
        )
        
        return (ball_min.x <= obstacle_max.x and ball_max.x >= obstacle_min.x and
                ball_min.y <= obstacle_max.y and ball_max.y >= obstacle_min.y and
                ball_min.z <= obstacle_max.z and ball_max.z >= obstacle_min.z)

    def check_collision_with_power_up(self, ball, power_up):
        distance = ((ball.position.x - power_up.position.x) ** 2 +
                   (ball.position.y - power_up.position.y) ** 2 +
                   (ball.position.z - power_up.position.z) ** 2) ** 0.5
        return distance < (ball.radius + power_up.radius)

    def apply_power_up(self, ball, power_up):
        if power_up.type == "speed_boost":
            ball.has_speed_boost = True
            ball.speed_boost_timer = 5.0  # 5 seconds duration
        elif power_up.type == "invincibility":
            # Implement invincibility logic here
            pass

    def draw_level(self):
        self.current_level_data.draw()

    def draw_ui(self):
        if self.state == GameState.MENU:
            text = "Press ENTER to Start"
            text_width = rl.measure_text(text, 20)
            rl.draw_text(
                text,
                SCREEN_WIDTH//2 - text_width//2,
                SCREEN_HEIGHT//2,
                20,
                rl.BLACK
            )
        elif self.state == GameState.LEVEL_COMPLETE:
            text = "Level Complete! Press ENTER for next level"
            text_width = rl.measure_text(text, 20)
            rl.draw_text(
                text,
                SCREEN_WIDTH//2 - text_width//2,
                SCREEN_HEIGHT//2,
                20,
                rl.BLACK
            )
        elif self.state == GameState.GAME_OVER:
            text = "Game Over! Press R to Restart"
            text_width = rl.measure_text(text, 20)
            rl.draw_text(
                text,
                SCREEN_WIDTH//2 - text_width//2,
                SCREEN_HEIGHT//2,
                20,
                rl.BLACK
            )
