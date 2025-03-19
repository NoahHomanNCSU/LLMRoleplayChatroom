import pygame
import random

# Game Configuration
WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 20
BALL_RADIUS = 10
COLOR_NEON_PINK = (255, 20, 147)
COLOR_NEON_BLUE = (0, 191, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

# Initialize pygame components
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Breakout: Cyberspace Obliteration")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - PADDLE_HEIGHT - 10, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 10
        
    def move(self, direction):
        if direction == "left" and self.rect.left > 0:
            self.rect.x -= self.speed
        if direction == "right" and self.rect.right < WIDTH:
            self.rect.x += self.speed

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.vx, self.vy = 5, -5

    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Bounce off the side walls
        if self.rect.left <= 0 or self.rect.right >= WIDTH:
            self.vx *= -1
        # Bounce off the top wall
        if self.rect.top <= 0:
            self.vy *= -1

class Block:
    def __init__(self, x, y, type):
        self.rect = pygame.Rect(x, y, 75, 30)
        self.type = type
        self.color = self.get_color()

    def get_color(self):
        if self.type == 'standard':
            return COLOR_NEON_BLUE
        elif self.type == 'reinforced':
            return COLOR_NEON_PINK

def create_blocks():
    blocks = []
    for row in range(5):
        for column in range(10):
            x = 80 * column
            y = 40 + row * 40
            block_type = 'standard' if random.random() > 0.3 else 'reinforced'
            blocks.append(Block(x, y, block_type))
    return blocks

def main():
    run = True
    paddle = Paddle()
    ball = Ball()
    blocks = create_blocks()

    while run:
        screen.fill(COLOR_BLACK)
        pygame.event.pump()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move("left")
        if keys[pygame.K_RIGHT]:
            paddle.move("right")
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        ball.move()
        
        # Bounce off paddle
        if ball.rect.colliderect(paddle.rect) and ball.vy > 0:
            ball.vy *= -1

        # Bounce off or destroy blocks
        for block in blocks[:]:
            if ball.rect.colliderect(block.rect):
                ball.vy *= -1
                if block.type == 'standard':
                    blocks.remove(block)
                elif block.type == 'reinforced':
                    block.type = 'standard'
                    block.color = block.get_color()

        # Draw elements
        pygame.draw.rect(screen, COLOR_WHITE, paddle.rect)
        pygame.draw.ellipse(screen, COLOR_WHITE, ball.rect)
        for block in blocks:
            pygame.draw.rect(screen, block.color, block.rect)
        
        if ball.rect.bottom >= HEIGHT:
            run = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()
