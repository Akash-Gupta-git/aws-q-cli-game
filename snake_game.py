import pygame
import random
import sys
import os
import json
from pygame.math import Vector2

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
CELL_SIZE = 30
CELL_NUMBER = 20
SCREEN_WIDTH = CELL_SIZE * CELL_NUMBER
SCREEN_HEIGHT = CELL_SIZE * CELL_NUMBER
FPS = 10

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 175, 0)
DARK_GREEN = (0, 125, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

# File paths
HIGHSCORE_FILE = "snake_highscore.json"

class Snake:
    def __init__(self):
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(1, 0)
        self.new_block = False
        
    def draw(self, screen):
        for i, block in enumerate(self.body):
            # Create rectangle for snake block
            rect = pygame.Rect(block.x * CELL_SIZE, block.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            # Draw different color for head
            if i == 0:
                pygame.draw.rect(screen, DARK_GREEN, rect)
            else:
                pygame.draw.rect(screen, GREEN, rect)
            
            # Draw a smaller rectangle inside to create a pattern
            inner_rect = pygame.Rect(
                block.x * CELL_SIZE + 4, 
                block.y * CELL_SIZE + 4, 
                CELL_SIZE - 8, 
                CELL_SIZE - 8
            )
            pygame.draw.rect(screen, DARK_GREEN if i != 0 else GREEN, inner_rect)
    
    def move(self):
        if self.new_block:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
            self.new_block = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
    
    def add_block(self):
        self.new_block = True
    
    def reset(self):
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(1, 0)

class Food:
    def __init__(self):
        self.randomize()
    
    def draw(self, screen):
        # Create a rectangle for food
        food_rect = pygame.Rect(self.pos.x * CELL_SIZE, self.pos.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, RED, food_rect)
        
        # Draw a circle inside to make it look like an apple
        pygame.draw.circle(
            screen, 
            RED, 
            (int(self.pos.x * CELL_SIZE + CELL_SIZE/2), int(self.pos.y * CELL_SIZE + CELL_SIZE/2)), 
            int(CELL_SIZE/2 - 2)
        )
    
    def randomize(self):
        self.x = random.randint(0, CELL_NUMBER - 1)
        self.y = random.randint(0, CELL_NUMBER - 1)
        self.pos = Vector2(self.x, self.y)

class SoundManager:
    def __init__(self):
        # Load sounds
        try:
            self.eat_sound = pygame.mixer.Sound('eat.wav')
            self.game_over_sound = pygame.mixer.Sound('game_over.wav')
            
            # Load and play background music
            pygame.mixer.music.load('background_music.mp3')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            self.music_on = True
            self.sound_enabled = True
        except:
            print("Warning: Sound files not found. Creating placeholder sounds.")
            # Create placeholder sounds if files not found
            self.eat_sound = pygame.mixer.Sound(buffer=bytearray(100))
            self.game_over_sound = pygame.mixer.Sound(buffer=bytearray(100))
            self.sound_enabled = False
    
    def play_eat_sound(self):
        if self.sound_enabled:
            self.eat_sound.play()
    
    def play_game_over_sound(self):
        if self.sound_enabled:
            self.game_over_sound.play()
    
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            pygame.mixer.music.set_volume(0.5)
        else:
            pygame.mixer.music.set_volume(0)
        
    def pause_music(self):
        pygame.mixer.music.pause()
        self.music_on = False
    def resume_music(self):
        pygame.mixer.music.unpause()
        self.music_on = True

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_over = False
        self.paused = False
        self.sound_manager = SoundManager()
        
    def update(self):
        if not self.game_over and not self.paused:
            self.snake.move()
            self.check_collision()
            self.check_fail()
    
    def draw(self, screen):
        self.food.draw(screen)
        self.snake.draw(screen)
        self.draw_score(screen)
        
        if self.game_over:
            self.draw_game_over(screen)
        elif self.paused:
            self.draw_pause_screen(screen)
    
    def check_collision(self):
        if self.food.pos == self.snake.body[0]:
            # Reposition the food
            self.food.randomize()
            
            # Make sure food doesn't appear on snake
            while self.food.pos in self.snake.body:
                self.food.randomize()
                
            # Add a block to snake
            self.snake.add_block()
            
            # Increase score
            self.score += 1
            
            # Play eat sound
            self.sound_manager.play_eat_sound()
            
            # Update high score if needed
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def check_fail(self):
        # Check if snake hits the walls
        if not 0 <= self.snake.body[0].x < CELL_NUMBER or not 0 <= self.snake.body[0].y < CELL_NUMBER:
            self.game_over = True
            self.sound_manager.play_game_over_sound()
            self.sound_manager.pause_music()
            
        
        # Check if snake hits itself
        for block in self.snake.body[1:]:
            if block == self.snake.body[0]:
                self.game_over = True
                self.sound_manager.play_game_over_sound()
                self.sound_manager.pause_music()
    
    def reset(self):
        self.snake.reset()
        self.food.randomize()
        self.score = 0
        self.game_over = False
        
    
    def toggle_pause(self):
        self.paused = not self.paused
    
    def draw_score(self, screen):
        score_text = f'Score: {self.score}'
        high_score_text = f'High Score: {self.high_score}'
        font = pygame.font.SysFont('Arial', 20)
        
        score_surface = font.render(score_text, True, WHITE)
        score_rect = score_surface.get_rect(topleft=(10, 10))
        screen.blit(score_surface, score_rect)
        
        high_score_surface = font.render(high_score_text, True, WHITE)
        high_score_rect = high_score_surface.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        screen.blit(high_score_surface, high_score_rect)
        
        # Display sound status
        sound_text = "Sound: ON" if self.sound_manager.sound_enabled else "Sound: OFF"
        sound_surface = font.render(sound_text, True, WHITE)
        sound_rect = sound_surface.get_rect(bottomleft=(10, SCREEN_HEIGHT - 10))
        screen.blit(sound_surface, sound_rect)
    
    def draw_game_over(self, screen):
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Game over text
        font = pygame.font.SysFont('Arial', 40)
        game_over_surface = font.render('GAME OVER', True, WHITE)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        
        # Score text
        score_surface = font.render(f'Score: {self.score}', True, WHITE)
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        
        # High score text
        high_score_surface = font.render(f'High Score: {self.high_score}', True, WHITE)
        high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
        
        # Restart text
        restart_font = pygame.font.SysFont('Arial', 25)
        restart_surface = restart_font.render('Press SPACE to restart', True, WHITE)
        restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 80))
        
        screen.blit(game_over_surface, game_over_rect)
        screen.blit(score_surface, score_rect)
        screen.blit(high_score_surface, high_score_rect)
        screen.blit(restart_surface, restart_rect)
    
    def draw_pause_screen(self, screen):
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Pause text
        font = pygame.font.SysFont('Arial', 40)
        pause_surface = font.render('PAUSED', True, WHITE)
        pause_rect = pause_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
        
        # Resume text
        resume_font = pygame.font.SysFont('Arial', 25)
        resume_surface = resume_font.render('Press P to resume', True, WHITE)
        resume_rect = resume_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
        
        screen.blit(pause_surface, pause_rect)
        screen.blit(resume_surface, resume_rect)
    
    def load_high_score(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except:
            print("Error loading high score")
        return 0
    
    def save_high_score(self):
        try:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            print("Error saving high score")

def main():
    # Set up the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Snake Game')
    
    # Set up the clock
    clock = pygame.time.Clock()
    
    # Create game instance
    game = Game()
    
    # Create a custom event for snake movement
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)  # Update every 150ms
    
    # Game loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == SCREEN_UPDATE and not game.paused:
                game.update()
            
            if event.type == pygame.KEYDOWN:
                # Game controls
                if not game.game_over and not game.paused:
                    if event.key == pygame.K_UP and game.snake.direction.y != 1:
                        game.snake.direction = Vector2(0, -1)
                    if event.key == pygame.K_DOWN and game.snake.direction.y != -1:
                        game.snake.direction = Vector2(0, 1)
                    if event.key == pygame.K_LEFT and game.snake.direction.x != 1:
                        game.snake.direction = Vector2(-1, 0)
                    if event.key == pygame.K_RIGHT and game.snake.direction.x != -1:
                        game.snake.direction = Vector2(1, 0)
                
                # Pause/Resume with P key
                if event.key == pygame.K_p and not game.game_over:
                    game.sound_manager.toggle_sound()
                    game.toggle_pause()
                
                # Restart with Space key
                if event.key == pygame.K_SPACE and game.game_over:
                    game.sound_manager.resume_music()
                    game.reset()
                    
                
                # Toggle sound with M key
                if event.key == pygame.K_m:
                    game.sound_manager.toggle_sound()
        
        # Fill the screen with black
        screen.fill(BLACK)
        
        # Draw game elements
        game.draw(screen)
        
        # Update the display
        pygame.display.update()
        
        # Control the game speed
        clock.tick(FPS)

if __name__ == "__main__":
    main()
