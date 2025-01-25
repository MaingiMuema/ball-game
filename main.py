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
        
        # Achievement tracking
        self.speed_boost_count = 0
        self.consecutive_power_ups = 0
        self.max_combo = 0
        self.total_power_ups = 0
        
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
                        self.speed_boost_count = 0  # Reset count when speed boost expires
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
        self.total_power_ups += 1
        self.consecutive_power_ups += 1
        
        if power_up_type == "speed_boost":
            self.has_speed_boost = True
            self.power_up_timers["speed_boost"] = 5.0
            self.speed_boost_count += 1
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

class Achievement:
    def __init__(self, name, description, condition_fn):
        self.name = name
        self.description = description
        self.condition_fn = condition_fn
        self.unlocked = False
        self.show_time = 0

class GameManager:
    def __init__(self, levels):
        self.levels = levels
        self.current_level = 0
        self.current_level_data = levels[self.current_level]
        self.state = GameState.PLAYING
        self.ball_position = Vector3(0, 0, 0)
        self.high_score = 0
        
        # Achievement system
        self.achievements = [
            Achievement(
                "Speed Demon",
                "Collect 3 speed boosts in a row",
                lambda ball: ball.speed_boost_count >= 3
            ),
            Achievement(
                "Combo Master",
                "Get a 3x combo multiplier",
                lambda ball: self.current_level_data.combo_multiplier >= 3
            ),
            Achievement(
                "Distance Runner",
                "Travel 1000 meters",
                lambda ball: abs(ball.position.z) >= 1000
            ),
            Achievement(
                "Power Collector",
                "Collect 20 power-ups in total",
                lambda ball: ball.total_power_ups >= 20
            ),
            Achievement(
                "Chain Master",
                "Collect 5 power-ups in a row",
                lambda ball: ball.consecutive_power_ups >= 5
            )
        ]

    def update(self, ball, delta_time):
        if self.state == GameState.PLAYING:
            # Check collisions
            for obstacle in self.current_level_data.obstacles:
                if self.check_collision(ball, obstacle):
                    if not ball.has_shield:
                        self.state = GameState.GAME_OVER
                        if ball.score > self.high_score:
                            self.high_score = ball.score
                    else:
                        ball.has_shield = False  # Remove shield on hit
                        self.current_level_data.add_particle_effect(ball.position, "collect")
            
            # Check achievements
            for achievement in self.achievements:
                if not achievement.unlocked and achievement.condition_fn(ball):
                    achievement.unlocked = True
                    achievement.show_time = 3.0  # Show for 3 seconds
                    
            # Update achievement timers
            for achievement in self.achievements:
                if achievement.show_time > 0:
                    achievement.show_time -= delta_time

    def check_collision(self, ball, obstacle):
        # Improved collision detection for different obstacle types
        if obstacle.spinning:
            # For spinning obstacles, check distance to the center line
            dx = ball.position.x - obstacle.position.x
            dy = ball.position.y - obstacle.position.y
            dz = ball.position.z - obstacle.position.z
            
            if abs(dz) < obstacle.size.z + ball.radius:
                distance_to_center = math.sqrt(dx * dx + dy * dy)
                return distance_to_center < obstacle.spin_radius + ball.radius
        else:
            # Box collision for regular obstacles
            half_size = Vector3(
                obstacle.size.x / 2,
                obstacle.size.y / 2,
                obstacle.size.z / 2
            )
            
            return (
                abs(ball.position.x - obstacle.position.x) < half_size.x + ball.radius and
                abs(ball.position.y - obstacle.position.y) < half_size.y + ball.radius and
                abs(ball.position.z - obstacle.position.z) < half_size.z + ball.radius
            )

    def draw_level(self):
        self.current_level_data.draw(self.ball_position)

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
                        game_manager.current_level_data.add_particle_effect(power_up.position)
                        game_manager.current_level_data.add_combo()
            
            # Update camera with smooth follow and effects
            target_cam_x = ball.position.x * 0.3
            camera.position = Vector3(
                target_cam_x,
                6.0 + math.sin(get_time() * 2) * 0.2,  # Gentle camera bob
                ball.position.z + 10.0
            )
            camera.target = Vector3(
                target_cam_x,
                1.0,
                ball.position.z - 5.0
            )
            
            # Update score with combo system
            ball.score = int(
                -ball.position.z * 
                game_manager.current_level_data.score_multiplier * 
                game_manager.current_level_data.combo_multiplier
            )
            
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
            # Draw HUD
            draw_text(f"Distance: {int(-ball.position.z)} m", 20, 20, 20, WHITE)
            draw_text(f"Score: {ball.score}", 20, 50, 20, GOLD)
            
            # Draw combo multiplier
            if game_manager.current_level_data.combo_multiplier > 1:
                draw_text(
                    f"Combo: x{game_manager.current_level_data.combo_multiplier:.1f}",
                    20, 80, 20, PURPLE
                )
            
            # Draw active power-ups
            y_offset = 110
            if ball.has_speed_boost:
                draw_text("Speed Boost!", 20, y_offset, 20, GREEN)
                y_offset += 30
            if ball.has_shield:
                draw_text("Shield Active", 20, y_offset, 20, SKYBLUE)
                y_offset += 30
            if ball.has_magnet:
                draw_text("Magnet Active", 20, y_offset, 20, PURPLE)
            
            # Draw achievement notifications
            y_offset = 150
            for achievement in game_manager.achievements:
                if achievement.show_time > 0:
                    draw_text(
                        f"Achievement Unlocked: {achievement.name}",
                        SCREEN_WIDTH//2 - 150,
                        y_offset,
                        20,
                        GOLD
                    )
                    draw_text(
                        achievement.description,
                        SCREEN_WIDTH//2 - 120,
                        y_offset + 25,
                        16,
                        LIGHTGRAY
                    )
                    y_offset += 60
            
            if game_manager.state == GameState.GAME_OVER:
                draw_text("Game Over! Press R to restart", 
                         SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 20, RED)
                draw_text(f"Final Score: {ball.score}", 
                         SCREEN_WIDTH//2 - 70, SCREEN_HEIGHT//2 + 30, 20, GOLD)
                
                # Show unlocked achievements
                y_offset = SCREEN_HEIGHT//2 + 70
                draw_text("Achievements Unlocked:", 
                         SCREEN_WIDTH//2 - 100, y_offset, 20, GOLD)
                y_offset += 30
                for achievement in game_manager.achievements:
                    if achievement.unlocked:
                        draw_text(
                            f"- {achievement.name}",
                            SCREEN_WIDTH//2 - 80,
                            y_offset,
                            16,
                            WHITE if achievement.unlocked else GRAY
                        )
                        y_offset += 25
        
        end_drawing()

    close_window()

if __name__ == "__main__":
    main()
