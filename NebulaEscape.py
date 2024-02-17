import pygame
import os
import math
import random
import button

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 120

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Nebula Escape")

# Initialize game variables
score = 0
prev_score = 0
scroll = 0
start_game = False
sam_displayed = False # Astronaut 1
start_time = 0
ale_displayed = False # Astronaut 2
ale_start_time = 0

# Framerate lock
clock = pygame.time.Clock()

# Colors
RED = (255, 0, 0)
GREEN = (50, 205, 50)
WHITE = (255, 255, 255)

# Fonts
font = pygame.font.SysFont("Retro Gaming", 30)

# Load images
sam = pygame.image.load("img/sam/sam.png")
sam_rect = sam.get_rect()
ale = pygame.image.load("img/alejandra/alejandra.png")
ale_rect = ale.get_rect()
menu = pygame.image.load("img/background/bg2.png").convert()
button_start = pygame.image.load("img/menu/start.png").convert()
button_restart = pygame.image.load("img/menu/restart.png").convert()
rocket_img = pygame.image.load("img/weapons/rocket.png").convert_alpha()
BG = pygame.image.load("img/background/bg1.png").convert()
BG_width = BG.get_width()
tiles = math.ceil(SCREEN_WIDTH / BG_width) + 1

# Sounds
shot = "sfx/shot.mp3"
death = "sfx/death.mp3"
rescued = "sfx/rescue.mp3"
shot_sound = pygame.mixer.Sound(shot)
death_sound = pygame.mixer.Sound(death)
rescued_sound = pygame.mixer.Sound(rescued)

# Player actions
moving_left = False
moving_right = False
moving_up = False
moving_down = False
shoot = False

# Classes
class Character(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        pygame.sprite.Sprite.__init__(self)
        # Class attributes
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.max_health = health
        self.health = health
        self.shoot_cooldown = 0
        self.direction = 1
        self.flip = False
        self.animation_list = []
        self.prev_frame_index = -1
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #ai specific
        self.vision = pygame.Rect(0, 0, 300, 20)
        self.direction = 0
        self.last_direction_change = pygame.time.get_ticks()

        # Load animations
        animation_types = ["Default", "Dead", "Spawn"]
        for animation in animation_types:
            # Reset temp list
            temp_list = []
            # Count sprite images
            num_frames = len(os.listdir(f"img\\{self.char_type}\\{animation}"))
            for i in range(num_frames):
                img = pygame.image.load(f"img\\{self.char_type}\\{animation}\\{i}.png").convert_alpha()
                img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        # Set initial image and position
        self.img = self.animation_list[self.action][self.frame_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)

    def sounds(self):
        if self.shoot_cooldown == 1:
            shot_sound.play()

    # Method to hold different updates & character collision
    def update(self):
        self.update_animation()
        self.check_alive()
        self.sounds()
        # Update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Character collision
        if pygame.sprite.spritecollide(player, rocket_group, True):
            if player.alive:
                player.health -= 5
        if pygame.sprite.spritecollide(enemy2, rocket_group, True):
            if enemy2.alive:
                enemy2.health -= 10
        if pygame.sprite.spritecollide(player, asteroid_group, False):
            if player.alive:
                player.health -= 50
        for enemy2_instance in enemy2_list:
            if pygame.sprite.spritecollide(enemy2_instance, rocket_group, True):
                if enemy2_instance.alive:
                    enemy2_instance.health -= 10

    # Movement method
    def move(self, moving_left, moving_right, moving_up, moving_down):
        # Reset movement variables
        dx = 0
        dy = 0

        # Movement variables
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        if moving_up:
            dy = -self.speed
        if moving_down:
            dy = self.speed

        # Check floor collision
        if self.rect.bottom + dy > 600:
            dy = 600 - self.rect.bottom

        # Update position
        self.rect.x += dx
        self.rect.y += dy

        # Check boundaries
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = 20
            rocket = Rocket(self.rect.centerx + (0.7 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            rocket_group.add(rocket)

    # Method for AI behavior
    def ai(self, player, enemy_group):
        if self.alive and player.alive:
            if self.alive and player.alive:
                if self.vision.colliderect(player.rect):
                    self.shoot()
                    return  # If player is in vision, stop moving and shoot

            # Check if it's time to change direction
            current_time = pygame.time.get_ticks()
            if current_time - self.last_direction_change > 1000:
                # Change direction after 1 second
                directions = [-1, 1, -2, 2]
                if self.direction in directions:
                    directions.remove(self.direction)  # Remove current direction
                self.direction = random.choice(directions)
                self.last_direction_change = current_time

            # Move according to the chosen direction
            moving_left = (self.direction == -1)
            moving_right = (self.direction == 1)
            moving_up = (self.direction == -2)
            moving_down = (self.direction == 2)
            self.move(moving_left, moving_right, moving_up, moving_down)

            for enemy in enemy_group:
                if enemy != self:  # Avoid self-collision check
                    if pygame.sprite.collide_rect(self, enemy):
                        # Adjust movement to avoid collision
                        if self.rect.centerx < enemy.rect.centerx:
                            move_left = True
                            move_right = False
                        else:
                            move_left = False
                            move_right = True

                        if self.rect.centery < enemy.rect.centery:
                            move_up = True
                            move_down = False
                        else:
                            move_up = False
                            move_down = True

                        # Move in the opposite direction to avoid collision
                        self.move(move_left, move_right, move_up, move_down)

        self.vision.center = (self.rect.centerx + 150 * self.direction, self.rect.centery)

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100
        # Update img for current frame
        self.img = self.animation_list[self.action][self.frame_index]
        # Check time since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            # Check if the first frame of the "Death" animation is played
        if self.action == 1 and self.frame_index == 0 and self.prev_frame_index != 0:
            death_sound.play()  # Trigger death sound
        self.prev_frame_index = self.frame_index
        # Switch from spawn animation to Default
        if self.action == 2 and self.frame_index == len(self.animation_list[self.action]) - 1:
            # After the last frame of the inactive animation, switch to action 0
            self.update_action(0)
        # Loop animation
        if self.frame_index >= len(self.animation_list[self.action]):
           if self.action == 1:
               self.frame_index = len(self.animation_list[self.action]) - 1
           else:
            self.frame_index = 0

    def update_action(self, new_action):
        # Check if new action != previous action
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            if self.action == 1 and self.frame_index == len(self.animation_list[self.action]) - 1:
                self.rect.y = 5000
            self.update_action(1)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        # Calculate health_bar ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed,):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        num_frames = len(os.listdir(f"img\\{self.char_type}"))
        for i in range(num_frames):
            img = pygame.image.load(f"img\\{self.char_type}\\{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
            self.animation_list.append(img)
        self.img = self.animation_list[self.frame_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)

    def asteroid_move(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100
        # Update img for current frame
        self.img = self.animation_list[self.frame_index]
        # Check time since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # Loop animation
        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0

    def draw(self):
        screen.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)

class Pod(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        num_frames = len(os.listdir(f"img\\{self.char_type}"))
        for i in range(num_frames):
            img = pygame.image.load(f"img\\{self.char_type}\\{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
            self.animation_list.append(img)
        self.img = self.animation_list[self.frame_index]
        self.rect = self.img.get_rect()
        self.rect.center = (x, y)
        self.initial_y = y
        self.amplitude = 50
        self.frequency = 0.05
        self.time_elapsed = -3

    # Sinusoidal left movement
    def pod_move(self):
        self.rect.x -= self.speed
        self.rect.y = self.initial_y + self.amplitude * math.sin(self.frequency * self.time_elapsed)
        self.time_elapsed += 1

    # Check pod collision
    def pod_collision(self, player_group):
        if pygame.sprite.spritecollideany(self, player_group):
            rescued_sound.play()
            self.speed +=5000

    def update_animation(self):
        # Update animation
        ANIMATION_COOLDOWN = 100
        # Update img for current frame
        self.img = self.animation_list[self.frame_index]
        # Check time since last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # Loop animation
        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0

    def draw(self):
        screen.blit(pygame.transform.flip(self.img, self.flip, False), self.rect)

class Rocket(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 13
        self.image = rocket_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # Move rocket
        self.rect.x += (self.direction * (self.speed * 0.5))
        # Check if rocket has left screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

# Method to reset the game back to its initial values
def reset_game():
    global score, prev_score, scroll, sam_displayed, ale_displayed, pod, pod2

    prev_score = 0
    score = 0
    scroll = 0
    sam_displayed = False
    ale_displayed = False

    # Reset player
    player.rect.x = 200
    player.rect.y = 200
    player.health = 100
    player.speed = 4
    player.update_action(0)
    player.alive = True

    # Reset enemies
    enemy.rect.x = 1199
    enemy.rect.y = 200
    enemy.speed = 3
    enemy.alive = True

    enemy2.rect.x = 600
    enemy2.rect.y = 400
    enemy2.speed = 4
    enemy2.health = 60
    enemy2.alive = True
    enemy2.update_action(2)

    # Clear any remaining enemy2 instances
    for new_enemy2 in enemy2_list:
        new_enemy2.kill()
    enemy2_list.clear()

    # Clear any remaining rockets
    rocket_group.empty()

    # Remove any remaining instances of the pod
    pod_group.empty()
    pod.kill()

    # Respawn the pod
    pod = Pod("pod", 2200, 200, 3, 1)
    pod2 = Pod("pod2", 5200, 200, 3, 1)
    pod_group.add(pod)
    pod_group.add(pod2)

    # Add player and enemies back to their respective groups
    player_group.add(player)
    enemy_group.add(enemy)
    enemy_group.add(enemy2)

# Create instances of classes
player = Character("player",200, 200, 3, 4, 100)
health_bar = HealthBar(10, 10, player.health, player.health)
pod = Pod("pod", 2200, 200, 3, 1)
pod2 = Pod("pod2", 5200, 200, 3, 1)
enemy = Asteroid("enemy", 1200, 200, 4, 3)
enemy2 = Character("enemy2", 600, 400, 3, 4, 60)
enemy2.update_action(2) #initial action set to 2
start_button = button.Button(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 80, button_start, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 80, button_restart, 1)

# Groups
rocket_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
asteroid_group = pygame.sprite.Group()
pod_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy2_group = pygame.sprite.Group()

# Add instances to groups
asteroid_group.add(enemy)
enemy_group.add(enemy)
enemy_group.add(enemy2)
pod_group.add(pod)
pod_group.add(pod2)
player_group.add(player)

enemy2_list = []

# Main game loop
run = True
while run:

    clock.tick(FPS)

    # Initiate main menu
    if start_game == False:
        screen.blit(menu, (0, 0))
        if start_button.draw(screen):
            start_game = True

    else:
        # Game logic
        # Display background
        for i in range(0, tiles):
            screen.blit(BG, (i * BG_width + scroll, 0))

        # Scroll BG
        if not player.alive:
            scroll -= 0
        else:
            scroll -= 2

        # Reset scroll
        if abs(scroll) > BG_width:
            scroll = 0

        # Handle score increase and score related spawns
        if enemy.rect.left == SCREEN_WIDTH:
            score += 1
            if (score - prev_score) % 5 == 0:
                enemy.speed += 1
                prev_score = score
            if score % 5 == 0:
                new_enemy2 = Character("enemy2", random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), 3, 4, 60)
                new_enemy2.update_action(2)
                enemy2_list.append(new_enemy2)
                prev_score = score#

        # Check if player collides with 1st pod
        if pygame.sprite.collide_rect(player, pod):
            sam_displayed = True
            start_time = pygame.time.get_ticks()

        # Display Sam if rescued
        if sam_displayed:
            screen.blit(sam, (10, 80))
            draw_text("Sam rescued!", font, WHITE, 10, 150)

        # Check if the time limit for the display has passed
        current_time = pygame.time.get_ticks()
        if sam_displayed and current_time - start_time >= 2500:
            sam_displayed = False # Stop displaying Sam

        # Check if player collides with 1nd pod
        if pygame.sprite.collide_rect(player, pod2):
            ale_displayed = True
            ale_start_time = pygame.time.get_ticks()

        # Display Ale if rescued
        if ale_displayed:
            screen.blit(ale, (10, 80))
            draw_text("Alejandra rescued!", font, WHITE, 10, 150)

        # Check if the time limit for the display has passed
        current_time = pygame.time.get_ticks()
        if ale_displayed and current_time - ale_start_time >= 2500:
            ale_displayed = False # Stop displaying Ale

        if not player.alive:
            enemy.speed = 0

        # Update and draw player
        player.update()
        player.draw()

        # Update and draw asteroid
        enemy.update_animation()
        enemy.asteroid_move()
        enemy.draw()

        # Update and draw 1st pod
        pod.update()
        pod.pod_collision(player_group)
        pod.pod_move()
        pod.update_animation()
        pod.draw()

        # Update and draw 2nd pod
        pod2.update()
        pod2.update()
        pod2.pod_collision(player_group)
        pod2.pod_move()
        pod2.update_animation()
        pod2.draw()

        # Update and draw enemy2
        enemy2.update()
        enemy2.ai(player, enemy_group)
        enemy2.draw()

        # Update and draw rocket_group
        rocket_group.update()
        rocket_group.draw(screen)

        # Update and draw additional instances of enemy2
        for enemy2_instance in enemy2_list:
            enemy2_instance.update()
            enemy2_instance.ai(player, enemy_group)
            enemy2_instance.draw()

        # Add additional instances of enemy2 to the respective group
        for new_enemy2 in enemy2_list:
            enemy2_group.add(new_enemy2)

        health_bar.draw(player.health)

        draw_text(f"HEALTH: {player.health}", font, WHITE, 10, 25)
        draw_text(f"Score: {score}", font, WHITE, 10, 50)

        # Update player actions if alive, otherwise handle restart button
        if player.alive:
            #shoot rockets
            if shoot:
               player.shoot()

            player.move(moving_left, moving_right, moving_up, moving_down)

        else:
            if restart_button.draw(screen):
                reset_game()

    # Event handling loop
    for event in pygame.event.get():
        #Quit Game
        if event.type == pygame.QUIT:
            run = False
        #Input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_w:
                moving_up = True
            if event.key == pygame.K_s:
                moving_down = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_ESCAPE:
                run = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_w:
                moving_up = False
            if event.key == pygame.K_s:
                moving_down = False
            if event.key == pygame.K_SPACE:
                shoot = False



    pygame.display.update()

pygame.quit()