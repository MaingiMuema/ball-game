from pyray import *
from dataclasses import dataclass
from typing import NamedTuple
from game_manager import GameManager, GameState
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
        self.position = Vector3(0.0, 5.0, 0.0)
        self.velocity = Vector3(0.0, 0.0, 0.0)
        self.radius = 0.5
        self.is_grounded = False
        self.score = 0
        self.has_speed_boost = False
        self.speed_boost_timer = 0

    def update(self, delta_time):
        # Apply gravity
        self.velocity.y -= GRAVITY * delta_time

        # Update position based on velocity
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time
        self.position.z += self.velocity.z * delta_time

        # Ground collision
        if self.position.y - self.radius <= 0:
            self.position.y = self.radius
            self.velocity.y = -self.velocity.y * 0.8  # Bounce with damping
            self.is_grounded = True
        else:
            self.is_grounded = False

        # Wall collisions
        if abs(self.position.x) >= 10 - self.radius:
            self.position.x = (10 - self.radius) if self.position.x > 0 else -(10 - self.radius)
            self.velocity.x *= -0.8

        if abs(self.position.z) >= 10 - self.radius:
            self.position.z = (10 - self.radius) if self.position.z > 0 else -(10 - self.radius)
            self.velocity.z *= -0.8

        # Update speed boost timer
        if self.has_speed_boost:
            self.speed_boost_timer -= delta_time
            if self.speed_boost_timer <= 0:
                self.has_speed_boost = False

        # Handle keyboard input
        if is_key_down(KEY_LEFT):
            self.velocity = Vector3(-MOVE_SPEED, self.velocity.y, self.velocity.z)
        elif is_key_down(KEY_RIGHT):
            self.velocity = Vector3(MOVE_SPEED, self.velocity.y, self.velocity.z)
        else:
            self.velocity = Vector3(0, self.velocity.y, self.velocity.z)

        if is_key_down(KEY_UP):
            self.velocity = Vector3(self.velocity.x, self.velocity.y, -MOVE_SPEED)
        elif is_key_down(KEY_DOWN):
            self.velocity = Vector3(self.velocity.x, self.velocity.y, MOVE_SPEED)
        else:
            self.velocity = Vector3(self.velocity.x, self.velocity.y, 0)

        # Jump when space is pressed and ball is grounded
        if is_key_pressed(KEY_SPACE) and self.is_grounded:
            self.velocity = Vector3(self.velocity.x, JUMP_FORCE, self.velocity.z)
            self.is_grounded = False

    def draw(self):
        draw_sphere(self.position, self.radius, BLUE if not self.has_speed_boost else GREEN)

def main():
    # Initialize window
    init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "3D Bouncing Ball Game")
    set_target_fps(60)

    # Initialize camera
    camera = Camera3D()
    camera.position = Vector3(10.0, 10.0, 10.0)
    camera.target = Vector3(0.0, 0.0, 0.0)
    camera.up = Vector3(0.0, 1.0, 0.0)
    camera.fovy = 45.0
    camera.projection = CAMERA_PERSPECTIVE

    # Create game objects
    ball = Ball()
    game_manager = GameManager()

    # Main game loop
    while not window_should_close():
        # Update
        delta_time = get_frame_time()

        # Handle game state transitions
        if game_manager.state == GameState.MENU and is_key_pressed(KEY_ENTER):
            game_manager.state = GameState.PLAYING
        elif game_manager.state == GameState.LEVEL_COMPLETE and is_key_pressed(KEY_ENTER):
            game_manager.current_level += 1
            if game_manager.current_level >= len(game_manager.levels):
                game_manager.state = GameState.GAME_OVER
            else:
                game_manager.reset_level()
                ball = Ball()  # Reset ball for new level
                game_manager.state = GameState.PLAYING
        elif game_manager.state == GameState.GAME_OVER and is_key_pressed(KEY_R):
            game_manager = GameManager()  # Reset entire game
            ball = Ball()

        # Update game logic if playing
        if game_manager.state == GameState.PLAYING:
            ball.update(delta_time)
            game_manager.update(ball, delta_time)

        # Update camera to follow ball
        camera.target = Vector3(ball.position.x, ball.position.y, ball.position.z)
        camera.position = Vector3(
            ball.position.x + 10.0,
            ball.position.y + 10.0,
            ball.position.z + 10.0
        )

        # Draw
        begin_drawing()
        clear_background(Color(135, 206, 235, 255))

        begin_mode_3d(camera)
        
        # Draw ground plane
        draw_grid(20, 1.0)
        
        # Draw level elements
        if game_manager.state != GameState.MENU:
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
