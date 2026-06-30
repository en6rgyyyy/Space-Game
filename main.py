import pygame
import sys
import random
import os

pygame.mixer.init()
pygame.init()


info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if sys.platform == 'android' else 0)
pygame.display.set_caption("Stars")

clock = pygame.time.Clock()

PLAYER_SIZE = 50

enemies = []
ENEMY_COUNT = 20

SCORE = 0

bullets = []
BULLET_SPEED = 6

explosions = []

STAR_COUNT = 85

running = True
game_over = False

# Шрифт
font = pygame.font.SysFont(None, 40)

# SOUNDTRACK
pygame.mixer.music.load(os.path.abspath("sound/space.mp3"))
pygame.mixer.music.play()

# Панель для кнопок
PANEL_HEIGHT = int(HEIGHT * 0.2)
control_panel_rect = pygame.Rect(0, HEIGHT - PANEL_HEIGHT, WIDTH, PANEL_HEIGHT)

# Кнопки (responsive позиции)
touch_controls = True
BUTTON_SIZE = int(WIDTH * 0.1)

left_btn = pygame.Rect(30, HEIGHT - PANEL_HEIGHT + 25, BUTTON_SIZE, BUTTON_SIZE)
right_btn = pygame.Rect(WIDTH - 100, HEIGHT - PANEL_HEIGHT + 25, BUTTON_SIZE, BUTTON_SIZE)
fire_btn = pygame.Rect(WIDTH // 2 - BUTTON_SIZE // 2, HEIGHT - PANEL_HEIGHT + 15, BUTTON_SIZE, BUTTON_SIZE)

left_pressed = False
right_pressed = False
fire_pressed = False
fire_cooldown = 0

# Фон
class Star:
    def __init__(self, WIDTH, HEIGHT):
        self.width = WIDTH
        self.height = HEIGHT 
        self.x, self.y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.speed = random.randint(1, 2)
        self.size = random.randint(1, 3)

    def update(self, WIDTH, HEIGHT):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, screen):
        star = pygame.Rect(self.x, self.y, self.size, self.size)
        pygame.draw.rect(screen, (255, 255, 255), star)

# Игрок
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 5
    
    def update(self, keys):
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed

# Враг
class Enemy:
    def __init__(self):
        self.respawn()

    def respawn(self):
        self.size = random.randint(30, 80)

        if self.size <= 50: 
            self.hp = 1 

        elif self.size <= 65: 
            self.hp = 2

        else: self.hp = 3

        self.max_hp = self.hp

        self.speed = max(2, 6 - self.hp)
        
        self.rect = pygame.Rect(
            random.randint(0, WIDTH - self.size),
            random.randint(-300, -40),
            self.size,
            self.size
        )

        self.image = pygame.transform.scale(enemy_image, (self.size, self.size))
    
    def take_damage(self, bullet_damege):
        self.hp -= bullet_damege
        if self.hp <= 0:
            return True
        return False
    
    def update(self):
        self.rect.y += self.speed

        if self.rect.y > HEIGHT:
            self.respawn()

    def draw(self):
        screen.blit(self.image, self.rect)

# Пули
class Bullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 10, 20)
        self.damage = 1
        self.speed = 6

    def update(self):
        self.rect.y -= self.speed

    def draw(self, surface):
        surface.blit(bullet_image, self.rect)


class Explosion:
    def __init__(self, x, y):
        self.frames = explosion_frames
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 0.1 
        self.done = False

    def update(self):
        self.index += self.speed
        if self.index >= len(self.frames):
            self.done = True
        else:
            self.image = self.frames[int(self.index)]

    def draw(self, surface):
        surface.blit(self.image, self.rect)


# Стартовое Меню (адаптировал для touch)
class Menu:
    def __init__(self):
        self.active = True
        self.options = ['START', 'EXIT']
        self.selected = 0
        self.font = font
        self.option_rects = []
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):  
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selected]

        elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.FINGERDOWN:
                x, y = int(event.x * WIDTH), int(event.y * HEIGHT)
            else:
                x, y = event.pos
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(x, y):
                    self.selected = i
                    return self.options[i]  
            
        return None
             
    def update(self):
        pass

    def draw(self):
        screen.fill((0, 0, 0))
        draw_background()

        self.option_rects = []
        for i, text in enumerate(self.options):
            color = (80, 250, 250) if i == self.selected else (255, 255, 255)
            menu_surf = self.font.render(text, True, color)
            menu_rect = menu_surf.get_rect(topleft=(WIDTH//2 - 40, 210 + i * 40))
            screen.blit(menu_surf, menu_rect.topleft)
            self.option_rects.append(menu_rect)

# Настройки игры (адаптировал для touch)
class Settings:
    def __init__(self):
        self.active = False
        self.options = ["VOLUME", "BACK"]
        self.selected = 0
        self.volume_level = 5  # От 0 до 10
        self.font = font
        self.option_rects = []

        self.update_volume()

    def update_volume(self):
        real_volume = self.volume_level / 10.0  

        pygame.mixer.music.set_volume(real_volume)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif self.options[self.selected] == "VOLUME":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    if self.volume_level > 0:
                        self.volume_level -= 1
                        self.update_volume()
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self.volume_level < 10:
                        self.volume_level += 1
                        self.update_volume()
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                if self.options[self.selected] == "BACK" or event.key == pygame.K_ESCAPE:
                    self.active = False
                    return 'BACK'

        elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.FINGERDOWN:
                x, y = int(event.x * WIDTH), int(event.y * HEIGHT)
            else:
                x, y = event.pos
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(x, y):
                    self.selected = i
                    if self.options[i] == "BACK":
                        self.active = False
                        return 'BACK'

        return None

    def draw(self):
        screen.fill((0, 0, 0))
        draw_background()  

        title = pygame.font.SysFont(None, 60).render("НАСТРОЙКИ", True, (100, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        self.option_rects = []
        for i, option in enumerate(self.options):
            if option == "VOLUME":
                text = f"VOLUME: {self.volume_level}"
            else:
                text = option

            color = (100, 255, 255) if i == self.selected else (200, 200, 200)
            surf = self.font.render(text, True, color)
            option_rect = surf.get_rect(center=(WIDTH // 2, 220 + i * 70))
            screen.blit(surf, option_rect.topleft)
            self.option_rects.append(option_rect)

        hint = pygame.font.SysFont(None, 30).render("< > или A D — изменить | ENTER — назад", True, (150, 150, 150))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))

stars = [Star(WIDTH, HEIGHT) for _ in range(STAR_COUNT)]

# Абсолютные пути для ассетов
enemy_image = pygame.image.load(os.path.abspath("gif/meteor.gif")).convert_alpha()

player_image = pygame.image.load(os.path.abspath("sprites_small/sprite_player.png"))
player_image = pygame.transform.scale(player_image, (PLAYER_SIZE, PLAYER_SIZE))

bullet_image = pygame.image.load(os.path.abspath("sprites_small/sprite_bullet.png"))

explosion_frames = []
for i in range(2):
    img = pygame.image.load(os.path.abspath(f"sprites_small/explosion_{i}.png")).convert_alpha()
    img = pygame.transform.scale(img, (70, 70))
    explosion_frames.append(img)

menu = Menu()
menu.active = True

settings = Settings()
settings.active = False

STATE_MENU = "menu"
STATE_SETTINGS = "settings"
STATE_GAME = "game"

game_state = STATE_MENU


# Рестарт (игрок выше для панели)
def restart_game():
    global player, enemies, SCORE, game_over
    player = Player(
        WIDTH // 2, 
        HEIGHT - PLAYER_SIZE - PANEL_HEIGHT - 40 
    )
    enemies.clear()
    for _ in range(ENEMY_COUNT):
        enemies.append(Enemy())
    
    bullets.clear()
    SCORE = 0
    game_over = False

restart_game()

def draw_background():
    for star in stars:
        star.update(WIDTH, HEIGHT)
        star.draw(screen)

def update_bullets(bullets):
    global SCORE

    for bullet in bullets[:]:
        bullet.update()

        if bullet.rect.y < -20:
            bullets.remove(bullet)
            continue

        for meteor in enemies[:]:
            if bullet.rect.colliderect(meteor.rect):
                
                if meteor.take_damage(bullet.damage):
                    explosions.append(Explosion(
                        meteor.rect.centerx,
                        meteor.rect.centery
                    ))
                    
                    bullets.remove(bullet)
                    meteor.respawn()

                    SCORE += meteor.max_hp * 10
                else:
                    if bullet in bullets:
                        bullets.remove(bullet)
                break        
   
def borders_screen():
    player.rect.x = max(0, min(player.rect.x, WIDTH - PLAYER_SIZE))
    player.rect.y = max(0, min(player.rect.y, HEIGHT - PLAYER_SIZE - PANEL_HEIGHT))  

# Запуск
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == STATE_MENU:
            result = menu.handle_event(event)

            if result == "START":
                game_state = STATE_GAME

            elif result == "EXIT":
                running = False

        elif game_state == STATE_SETTINGS:
            result = settings.handle_event(event)

            if result == "BACK":
                if not game_over:
                    game_state = STATE_GAME
                else:
                    game_state = STATE_MENU

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                restart_game()

            if event.key == pygame.K_SPACE and not game_over:
                bullet_x = player.rect.x + PLAYER_SIZE // 2 - 5
                bullet_y = player.rect.y
                bullets.append(Bullet(bullet_x - 11, bullet_y))

            if event.key == pygame.K_ESCAPE:
                if game_state == STATE_GAME:
                    game_state = STATE_SETTINGS
        
        if touch_controls:
            if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.FINGERDOWN:
                    x, y = int(event.x * WIDTH), int(event.y * HEIGHT)
                else:
                    x, y = event.pos

                if left_btn.collidepoint(x, y):
                    left_pressed = True
                if right_btn.collidepoint(x, y):
                    right_pressed = True
                if fire_btn.collidepoint(x, y):
                    fire_pressed = True

                # Для game_over restart text
                if game_state == STATE_GAME and game_over and 'restart_rect' in globals() and restart_rect.collidepoint(x, y):
                    restart_game()

            elif event.type in (pygame.FINGERUP, pygame.MOUSEBUTTONUP):
                left_pressed = False
                right_pressed = False
                fire_pressed = False

    if not game_over:
        keys = pygame.key.get_pressed()
        player.update(keys)
        
    if game_state == STATE_MENU:
        menu.draw()
        pygame.display.flip()

    elif game_state == STATE_SETTINGS:
        settings.draw()
        pygame.display.flip()

    elif game_state == STATE_GAME:
        borders_screen()

        if not game_over:
            if touch_controls:
                if left_pressed:
                    player.rect.x -= player.speed
                if right_pressed:
                    player.rect.x += player.speed
                
                if fire_pressed:
                    fire_cooldown += 1
                    if fire_cooldown >= 7:  
                        bullets.append(Bullet(player.rect.centerx - 16, player.rect.top))
                        fire_cooldown = 0
            else:
                keys = pygame.key.get_pressed()
                player.update(keys)

        player_rect = pygame.Rect(player.rect.x, player.rect.y, PLAYER_SIZE, PLAYER_SIZE)
        screen.fill((0, 0, 0))
        
        # Фон
        draw_background()

        for i, meteor in enumerate(enemies[:]):
            meteor.update()
            meteor.draw()

            if player.rect.colliderect(meteor.rect):
                explosions.append(Explosion(
                    player.rect.centerx,
                    player.rect.centery
                ))
                game_over = True
                
        for i in range(len(enemies[:])):
            meteor_a = enemies[i]

            for j in range(i+1, len(enemies[:])):
                meteor_b = enemies[j]

                if meteor_a.rect.colliderect(meteor_b.rect):
                    explosions.append(Explosion(
                        meteor_b.rect.centerx,
                        meteor_b.rect.centery
                    ))                   
                    meteor_b.respawn()

        screen.blit(player_image, (player.rect.x, player.rect.y))

        txt = font.render(f"Score: {SCORE}", True, (250, 250, 250))
        screen.blit(txt, (10, 10))

        if touch_controls and game_state == STATE_GAME:
            # Рисуем панель
            pygame.draw.rect(screen, (30, 30, 30), control_panel_rect)  
            pygame.draw.line(screen, (100, 100, 100), (0, HEIGHT - PANEL_HEIGHT), (WIDTH, HEIGHT - PANEL_HEIGHT), 2)  

            def draw_solid_button(rect, pressed, icon_text, is_fire=False):
                base_color = (100, 100, 100) if not is_fire else (150, 50, 50)  
                highlight_color = (150, 150, 150) if not is_fire else (200, 80, 80)
                shadow_color = (50, 50, 50) if not is_fire else (100, 30, 30)
                
                if pressed:
                    base_color = tuple(max(0, c - 30) for c in base_color)
                    highlight_color = tuple(max(0, c - 30) for c in highlight_color)
                    shadow_color = tuple(max(0, c - 30) for c in shadow_color)
                
                # Основной прямоугольник
                pygame.draw.rect(screen, base_color, rect)
                
                # Bevel
                pygame.draw.line(screen, highlight_color, (rect.left, rect.top), (rect.right, rect.top), 2)  
                pygame.draw.line(screen, highlight_color, (rect.left, rect.top), (rect.left, rect.bottom), 2)  
                pygame.draw.line(screen, shadow_color, (rect.left, rect.bottom), (rect.right, rect.bottom), 2)  
                pygame.draw.line(screen, shadow_color, (rect.right, rect.top), (rect.right, rect.bottom), 2)  
                
                # Градиент
                for i in range(rect.height // 2):
                    grad_color = tuple(int(base_color[j] + (highlight_color[j] - base_color[j]) * (i / (rect.height // 2))) for j in range(3))
                    pygame.draw.line(screen, grad_color, (rect.left, rect.top + i), (rect.right, rect.top + i))
                
                # Иконка
                icon_font = pygame.font.SysFont(None, 40, bold=True)
                icon = icon_font.render(icon_text, True, (220, 220, 220))  
                screen.blit(icon, (rect.centerx - icon.get_width()//2, rect.centery - icon.get_height()//2))
            
            # Рисуем кнопки
            draw_solid_button(left_btn, left_pressed, "<")
            draw_solid_button(right_btn, right_pressed, ">")
            draw_solid_button(fire_btn, fire_pressed, "FIRE", is_fire=True)

        # Пули
        update_bullets(bullets)

        for bullet in bullets[:]:
            bullet.draw(screen)

        for explosion in explosions[:]:
            explosion.update()
            explosion.draw(screen)

            if explosion.done:
                explosions.remove(explosion)
        
        if game_over:
            font_gameOver = pygame.font.SysFont(None, 50)
            font_restart = pygame.font.SysFont(None, 30)
            text_gameOver = font_gameOver.render("GAME OVER", True, (255, 255, 255))
            text_restart = font_restart.render("RESTART - R", True, (255, 255, 255))
            go_rect = text_gameOver.get_rect(topleft=(WIDTH//2 - 120, HEIGHT//2 - 36))
            restart_rect = text_restart.get_rect(topleft=(WIDTH//2 - 65, HEIGHT//2 + 12))
            screen.blit(text_gameOver, go_rect.topleft)
            screen.blit(text_restart, restart_rect.topleft)

        pygame.display.flip()

pygame.quit()
sys.exit()
