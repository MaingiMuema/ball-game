from pyray import *
from dataclasses import dataclass
from typing import NamedTuple
from game_manager import GameManager, GameState
from levels import create_levels
import math

class Color(NamedTuple):
    r: int
    g: int
    b: int
    a: int

# Initialize window and game settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GRAVITY = 9.81
JUMP_FORCE = 15.0
MOVE_SPEED = 10.0

class Ball:
    def __init__(self):
        self.position = Vector3(0.0, 1.0, -10.0)  # Start further back
        self.velocity = Vector3(0.0, 0.0, 0.0)
        self.radius = 0.5
        self.is_grounded = False
        self.score = 0
        self.has_speed_boost = False
        self.speed_boost_timer = 0
        self.forward_speed = 15.0  # Base forward speed
        self.max_side_speed = 20.0  # Maximum horizontal speed
        self.side_acceleration = 40.0  # How quickly the ball responds to input
        self.side_drag = 5.0  # Horizontal drag to smooth movement

    def update(self, delta_time):
        # Constant forward movement
        self.velocity.z = self.forward_speed * (1.5 if self.has_speed_boost else 1.0)
        
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
        self.velocity.y -= 25.0 * delta_time  # Increased gravity for snappier jumps

        # Update position
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time
        self.position.z += self.velocity.z * delta_time

        # Ground collision with bouncing
        if self.position.y - self.radius <= 0:
            self.position.y = self.radius
            self.velocity.y = abs(self.velocity.y) * 0.5  # Bounce with energy loss
            self.is_grounded = True
        else:
            self.is_grounded = False

        # Wall collisions with bounce effect
        if abs(self.position.x) >= 10 - self.radius:
            self.position.x = (10 - self.radius) if self.position.x > 0 else -(10 - self.radius)
            self.velocity.x *= -0.8  # Bounce off walls

        # Jump control
        if is_key_pressed(KEY_SPACE) and self.is_grounded:
            self.velocity.y = 15.0  # Increased jump force
            self.is_grounded = False

        # Update speed boost timer
        if self.has_speed_boost:
            self.speed_boost_timer -= delta_time
            if self.speed_boost_timer <= 0:
                self.has_speed_boost = False

    def draw(self):
        # Trail effect
        trail_length = 10
        trail_spacing = 0.2
        for i in range(trail_length):
            alpha = 1.0 - (i / trail_length)
            trail_color = Color(
                int(BLUE.r * alpha) if not self.has_speed_boost else int(GREEN.r * alpha),
                int(BLUE.g * alpha) if not self.has_speed_boost else int(GREEN.g * alpha),
                int(BLUE.b * alpha) if not self.has_speed_boost else int(GREEN.b * alpha),
                int(255 * alpha)
            )
            trail_pos = Vector3(
                self.position.x,
                self.position.y,
                self.position.z - i * trail_spacing
            )
            draw_sphere(trail_pos, self.radius * (1 - i/trail_length), trail_color)
        
        # Main ball
        draw_sphere(self.position, self.radius, BLUE if not self.has_speed_boost else GREEN)

def main():
    # Initialize window
    init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "3D Bouncing Ball Game")
    
    # Initialize camera
    camera = Camera3D()
    camera.position = Vector3(10.0, 10.0, 10.0)
    camera.target = Vector3(0.0, 0.0, 0.0)
    camera.up = Vector3(0.0, 1.0, 0.0)
    camera.fovy = 45.0
    camera.projection = CAMERA_PERSPECTIVE

    # Create game objects
    ball = Ball()
    levels = create_levels()
    game_manager = GameManager(levels)

    set_target_fps(60)

    # Main game loop
    while not window_should_close():
        # Update
        delta_time = get_frame_time()

        # Update game state
        if game_manager.state == GameState.LEVEL_COMPLETE:
            if is_key_pressed(KEY_ENTER):
                ball = Ball()  # Reset ball for new level
                game_manager.state = GameState.PLAYING
        elif game_manager.state == GameState.GAME_OVER and is_key_pressed(KEY_R):
            game_manager = GameManager(levels)  # Reset entire game
            ball = Ball()

        # Update game logic if playing
        if game_manager.state == GameState.PLAYING:
            # Update camera to follow ball
            camera.position = Vector3(
                ball.position.x + 10.0,  # Offset to the right
                ball.position.y + 8.0,   # Above the ball
                ball.position.z + 15.0   # Behind the ball
            )
            camera.target = Vector3(
                ball.position.x,         # Look at ball
                ball.position.y,
                ball.position.z - 10.0   # Look ahead of the ball
            )

            game_manager.update(ball, delta_time)
            ball.update(delta_time)

        # Draw
        begin_drawing()
        clear_background(RAYWHITE)

        begin_mode_3d(camera)
        
        # Draw ground plane
        draw_grid(20, 1.0)
        
        # Draw level elements
        game_manager.draw_level()
        
        # Draw ball
        ball.draw()

        end_mode_3d()

        # Draw UI
        draw_text(f"Score: {ball.score}", 20, 20, 20, BLACK)
        if ball.has_speed_boost:
            draw_text("Speed Boost Active!", 20, 50, 20, RED)
        
        # Draw game state specific UI
        game_manager.draw_ui()

        end_drawing()

    close_window()

if __name__ == "__main__":
    main()
