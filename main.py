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
        self.position = Vector3(0.0, 1.0, 0.0)  # Start at origin
        self.velocity = Vector3(0.0, 0.0, 0.0)
        self.radius = 0.5
        self.is_grounded = False
        self.score = 0
        self.has_speed_boost = False
        self.speed_boost_timer = 0
        self.forward_speed = 20.0  # Increased base forward speed
        self.max_side_speed = 15.0  # Maximum horizontal speed
        self.side_acceleration = 50.0  # Increased for more responsive controls
        self.side_drag = 8.0  # Increased horizontal drag for better control

    def update(self, delta_time):
        # Constant forward movement (negative Z is forward)
        self.velocity.z = -self.forward_speed * (1.5 if self.has_speed_boost else 1.0)
        
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
            self.velocity.y -= 35.0 * delta_time  # Increased gravity for snappier jumps

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

        # Wall collisions (with bounce effect)
        if abs(self.position.x) >= 4.5 - self.radius:  # Narrower bounds for the suspended road
            self.position.x = (4.5 - self.radius) if self.position.x > 0 else -(4.5 - self.radius)
            self.velocity.x *= -0.5  # Reduced bounce for better control

        # Jump control
        if is_key_pressed(KEY_SPACE) and self.is_grounded:
            self.velocity.y = 12.0  # Adjusted jump force
            self.is_grounded = False

        # Update speed boost timer
        if self.has_speed_boost:
            self.speed_boost_timer -= delta_time
            if self.speed_boost_timer <= 0:
                self.has_speed_boost = False

    def draw(self):
        # Trail effect
        trail_length = 15  # Increased trail length
        trail_spacing = 0.15
        for i in range(trail_length):
            alpha = 1.0 - (i / trail_length)
            base_color = BLUE if not self.has_speed_boost else GREEN
            trail_color = Color(
                int(base_color[0] * alpha),
                int(base_color[1] * alpha),
                int(base_color[2] * alpha),
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
        
        # Main ball
        draw_sphere(
            (self.position.x, self.position.y, self.position.z),
            self.radius,
            BLUE if not self.has_speed_boost else GREEN
        )

def main():
    # Initialize window
    init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Endless Runner Ball Game")
    set_target_fps(60)

    # Initialize camera
    camera = Camera3D()
    camera.position = Vector3(0.0, 6.0, 10.0)  # Adjusted camera position
    camera.target = Vector3(0.0, 0.0, 0.0)
    camera.up = Vector3(0.0, 1.0, 0.0)
    camera.fovy = 60.0
    camera.projection = CAMERA_PERSPECTIVE

    # Create game objects
    ball = Ball()
    levels = create_levels()
    game_manager = GameManager(levels)

    while not window_should_close():
        # Update
        delta_time = get_frame_time()
        
        # Update game objects
        ball.update(delta_time)
        game_manager.update(ball, delta_time)
        
        # Update camera to follow ball
        camera.position = Vector3(
            ball.position.x * 0.3,  # Slight camera follow on x-axis
            6.0,  # Fixed height
            ball.position.z + 10.0  # Follow behind the ball
        )
        camera.target = Vector3(
            ball.position.x * 0.3,  # Look ahead where the ball is going
            0.0,
            ball.position.z - 5.0
        )

        # Draw
        begin_drawing()
        clear_background(BLACK)  # Changed to black for space theme
        
        begin_mode_3d(camera)
        
        # Draw game elements
        ball.draw()
        game_manager.current_level_data.draw()
        
        end_mode_3d()
        
        # Draw UI
        draw_text(f"Score: {int(-ball.position.z)}", 20, 20, 20, WHITE)
        if game_manager.state == GameState.GAME_OVER:
            draw_text("Game Over! Press R to restart", 
                     SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 20, RED)
            draw_text(f"High Score: {game_manager.high_score}", 
                     SCREEN_WIDTH//2 - 70, SCREEN_HEIGHT//2 + 30, 20, GOLD)
        
        end_drawing()

    close_window()

if __name__ == "__main__":
    main()
