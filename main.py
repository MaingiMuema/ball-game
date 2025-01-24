from pyray import *
from dataclasses import dataclass
from typing import NamedTuple
from game_manager import GameManager, GameState
from levels import create_levels
import math

# Initialize window and game settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GRAVITY = 9.81
JUMP_FORCE = 15.0
MOVE_SPEED = 10.0

class Color(NamedTuple):
    r: int
    g: int
    b: int
    a: int

class Ball:
    def __init__(self):
        self.position = Vector3(0.0, 1.0, 0.0)
        self.velocity = Vector3(0.0, 0.0, 0.0)
        self.radius = 0.5
        self.is_grounded = False
        self.score = 0
        
        # Power-up states
        self.has_speed_boost = False
        self.has_shield = False
        self.has_magnet = False
        self.power_up_timers = {
            "speed_boost": 0,
            "shield": 0,
            "magnet": 0
        }
        
        # Movement properties
        self.forward_speed = 20.0
        self.max_side_speed = 15.0
        self.side_acceleration = 50.0
        self.side_drag = 8.0
        
        # Visual effects
        self.trail_color = BLUE
        self.shield_rotation = 0

    def update(self, delta_time):
        # Update power-up timers
        for power_up, timer in self.power_up_timers.items():
            if timer > 0:
                self.power_up_timers[power_up] -= delta_time
                if self.power_up_timers[power_up] <= 0:
                    if power_up == "speed_boost":
                        self.has_speed_boost = False
                    elif power_up == "shield":
                        self.has_shield = False
                    elif power_up == "magnet":
                        self.has_magnet = False

        # Update forward speed based on power-ups
        current_speed = self.forward_speed * (1.5 if self.has_speed_boost else 1.0)
        self.velocity.z = -current_speed
        
        # Horizontal movement with smooth acceleration
        target_x_speed = 0
        if is_key_down(KEY_LEFT):
            target_x_speed = -self.max_side_speed
        elif is_key_down(KEY_RIGHT):
            target_x_speed = self.max_side_speed
            
        # Smoothly adjust horizontal speed
        speed_diff = target_x_speed - self.velocity.x
        self.velocity.x += speed_diff * self.side_acceleration * delta_time
        
        # Apply drag to horizontal movement
        if abs(self.velocity.x) > 0:
            drag_direction = -1 if self.velocity.x > 0 else 1
            drag_force = min(abs(self.velocity.x), self.side_drag * delta_time)
            self.velocity.x += drag_direction * drag_force

        # Apply gravity
        if not self.is_grounded:
            self.velocity.y -= 35.0 * delta_time

        # Update position
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time
        self.position.z += self.velocity.z * delta_time

        # Ground collision
        if self.position.y - self.radius <= 0:
            self.position.y = self.radius
            self.velocity.y = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

        # Wall collisions
        if abs(self.position.x) >= 4.5 - self.radius:
            self.position.x = (4.5 - self.radius) if self.position.x > 0 else -(4.5 - self.radius)
            self.velocity.x *= -0.5

        # Jump control
        if is_key_pressed(KEY_SPACE) and self.is_grounded:
            self.velocity.y = 12.0
            self.is_grounded = False
            
        # Update shield rotation
        if self.has_shield:
            self.shield_rotation += 180.0 * delta_time
            
        # Update trail color
        if self.has_speed_boost:
            self.trail_color = GREEN
        elif self.has_shield:
            self.trail_color = SKYBLUE
        elif self.has_magnet:
            self.trail_color = PURPLE
        else:
            self.trail_color = BLUE

    def apply_power_up(self, power_up_type):
        if power_up_type == "speed_boost":
            self.has_speed_boost = True
            self.power_up_timers["speed_boost"] = 5.0
        elif power_up_type == "shield":
            self.has_shield = True
            self.power_up_timers["shield"] = 10.0
        elif power_up_type == "points":
            self.score += 1000
        elif power_up_type == "magnet":
            self.has_magnet = True
            self.power_up_timers["magnet"] = 8.0

    def draw(self):
        # Draw shield effect if active
        if self.has_shield:
            shield_scale = 1.2 + math.sin(get_time() * 4) * 0.1
            shield_color = fade(SKYBLUE, 0.5)
            draw_sphere(
                (self.position.x, self.position.y, self.position.z),
                self.radius * shield_scale,
                shield_color
            )

        # Trail effect
        trail_length = 15
        trail_spacing = 0.15
        for i in range(trail_length):
            alpha = 1.0 - (i / trail_length)
            trail_color = Color(
                int(self.trail_color[0] * alpha),
                int(self.trail_color[1] * alpha),
                int(self.trail_color[2] * alpha),
                int(255 * alpha)
            )
            trail_pos = Vector3(
                self.position.x,
                self.position.y,
                self.position.z + i * trail_spacing
            )
            draw_sphere(
                (trail_pos.x, trail_pos.y, trail_pos.z),
                self.radius * (1.0 - i/trail_length * 0.5),
                trail_color
            )
        
        # Main ball with glow effect
        glow_size = 1.0 + abs(math.sin(get_time() * 3)) * 0.1
        draw_sphere(
            (self.position.x, self.position.y, self.position.z),
            self.radius * glow_size,
            fade(self.trail_color, 0.5)
        )
        draw_sphere(
            (self.position.x, self.position.y, self.position.z),
            self.radius * 0.8,
            self.trail_color
        )

def main():
    # Initialize window
    init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Endless Runner Ball Game")
    set_target_fps(60)

    # Initialize camera
    camera = Camera3D()
    camera.position = Vector3(0.0, 6.0, 10.0)
    camera.target = Vector3(0.0, 0.0, 0.0)
    camera.up = Vector3(0.0, 1.0, 0.0)
    camera.fovy = 60.0
    camera.projection = CAMERA_PERSPECTIVE

    def reset_game():
        nonlocal ball, game_manager
        ball = Ball()
        levels = create_levels()
        game_manager = GameManager(levels)

    # Create initial game objects
    ball = None
    game_manager = None
    reset_game()

    # Game state variables
    start_message_shown = True
    game_started = False

    while not window_should_close():
        # Update
        delta_time = get_frame_time()
        
        if not game_started:
            if is_key_pressed(KEY_SPACE):
                game_started = True
                start_message_shown = False
        
        if game_started and game_manager.state == GameState.PLAYING:
            # Update game objects
            ball.update(delta_time)
            game_manager.ball_position = ball.position
            game_manager.update(ball, delta_time)
            
            # Check power-up collisions
            for power_up in game_manager.current_level_data.power_ups:
                if power_up.active:
                    distance = math.sqrt(
                        (power_up.position.x - ball.position.x) ** 2 +
                        (power_up.position.y - ball.position.y) ** 2 +
                        (power_up.position.z - ball.position.z) ** 2
                    )
                    collect_radius = 1.0 if not ball.has_magnet else 3.0
                    if distance < collect_radius:
                        power_up.active = False
                        ball.apply_power_up(power_up.type)
            
            # Update camera to follow ball
            camera.position = Vector3(
                ball.position.x * 0.3,
                6.0 + math.sin(get_time()) * 0.2,
                ball.position.z + 10.0
            )
            camera.target = Vector3(
                ball.position.x * 0.3,
                1.0,
                ball.position.z - 5.0
            )
            
            # Update score based on distance and multiplier
            ball.score = int(-ball.position.z * game_manager.current_level_data.score_multiplier)
            
        elif game_manager.state == GameState.GAME_OVER and is_key_pressed(KEY_R):
            reset_game()
            game_started = False
            start_message_shown = True

        # Draw
        begin_drawing()
        clear_background(BLACK)
        
        begin_mode_3d(camera)
        
        # Draw game elements
        game_manager.draw_level()
        ball.draw()
        
        end_mode_3d()
        
        # Draw UI
        if start_message_shown:
            draw_text("Press SPACE to Start", 
                     SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 20, WHITE)
            draw_text("Use Arrow Keys to Move, SPACE to Jump", 
                     SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 + 30, 20, GRAY)
        else:
            # Draw score and distance
            draw_text(f"Distance: {int(-ball.position.z)} m", 20, 20, 20, WHITE)
            draw_text(f"Score: {ball.score}", 20, 50, 20, GOLD)
            
            # Draw active power-ups
            y_offset = 80
            if ball.has_speed_boost:
                draw_text("Speed Boost!", 20, y_offset, 20, GREEN)
                y_offset += 30
            if ball.has_shield:
                draw_text("Shield Active", 20, y_offset, 20, SKYBLUE)
                y_offset += 30
            if ball.has_magnet:
                draw_text("Magnet Active", 20, y_offset, 20, PURPLE)
            
            if game_manager.state == GameState.GAME_OVER:
                draw_text("Game Over! Press R to restart", 
                         SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 20, RED)
                draw_text(f"Final Score: {ball.score}", 
                         SCREEN_WIDTH//2 - 70, SCREEN_HEIGHT//2 + 30, 20, GOLD)
        
        end_drawing()

    close_window()

if __name__ == "__main__":
    main()
