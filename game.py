# Importing the necessary libraries
import pygame
import random


class Game:
    def __init__(self, screen, width=800, height=600):
        # Window size
        self.width = width
        self.height = height
        self.screen = screen
        self.clock = pygame.time.Clock()  # If it weren't, it would run faster on a fast machine, slower on a slow machine
        # Player
        self.player_x = 120  # The player is always 120 pixels from the left side
        self.player_y = height // 2  # The player's position on the y axis at the beginning
        self.player_radius = 20  # Player radius
        # Pipes
        self.pipe_width = 80  # Every pipe is 80 pixels wide
        self.pipe_gap = 180  # The gap is 180 pixels
        self.pipe_speed = 5  # They move 5 pixels to the left every frame (60 FPS: 5 × 60 = 300 pixels/second)
        self.pipes = []  # This is where the pipes will go
        self.score = 0  # Score (initially 0 points)
        raw_image = pygame.image.load("images/player.png").convert_alpha()  # This loads the image from your hard drive and converts it to retain its alpha channel
        size = self.player_radius * 2  # 40x40 pixel
        raw_image = pygame.transform.scale(raw_image, (size, size))  # Resize the raw image so that the length of its sides is equal to radius * 2
        self.player_image = self._make_rounded(raw_image, size)  # Convert it to a circular image
        self.spawn_pipe()  # Creating the first pipe
        
    def _make_rounded(self, image, size):
            rounded = pygame.Surface((size, size), pygame.SRCALPHA)  # Create a surface that supports transparency
            pygame.draw.circle(rounded, (255, 255, 255), (size // 2, size // 2), size // 2)  # Draws a white circle in the center of the transparent surface
            image.blit(rounded, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)  # Copies the transparent image onto the original, but compares each channel and chooses the smaller one because of special_flags=pygame.BLEND_RGBA_MIN, i.e. where there is transparency, it keeps the transparent one because 0 is always smaller, and where there is a white circle, it will always draw the original image because the pixel value will always be smaller than 255 (white)
            return image  # We will return with the modified image

    def spawn_pipe(self):
        gap_y = random.randint(90, self.height - 90)  # We don't want the gap to be too high or too low
        self.pipes.append({
            "x": self.width,  # The starting X coordinate (starting from the right edge of the window)
            "gap_y": gap_y  # The Y coordinate of the middle of the section between the top and bottom columns
        })

    def update(self, progress):
        self.player_y = int(progress * self.height)  # progress = 0.0 -> the player is at the top of the screen; progress = 0.5 -> in the middle of the screen; progress = 1.0 -> at the bottom of the screen
        # The loop iterates through them in order and shifts them to the left using the value of pipe_speed
        for pipe in self.pipes:
            pipe["x"] -= self.pipe_speed
        # If the last created pipe is already 300 pixels to the left, we create a new one
        if self.pipes[-1]["x"] < self.width - 300:
            self.spawn_pipe()
        # If the pipe goes completely out of the picture to the left, we delete it from the list of pipes and increase the score by one
        if self.pipes[0]["x"] < -self.pipe_width:
            self.pipes.pop(0)
            self.score += 1

    def draw(self):
        self.screen.fill((255, 214, 102))  # Fills the entire screen with one color
        # Rendering the player
        # We always start drawing with the upper left corner, so we move left and up with the radius value
        draw_x = self.player_x - self.player_radius
        draw_y = self.player_y - self.player_radius
        self.screen.blit(self.player_image, (draw_x, draw_y))  # Draw the image on the screen at the given coordinates
        # We iterate through the pipes
        for pipe in self.pipes:
            # Create the top column rectangle
            top_rect = pygame.Rect(
                # Top right corner of the top column
                pipe["x"],  # It will continuously shift to the left
                0,
                self.pipe_width,  # Column width
                pipe["gap_y"] - self.pipe_gap // 2  # Top column height is offset from the center of the gap between the two columns by 90 pixels, resulting in a gap of 180 pixels
            )
            # Create the bottom column rectangle
            bottom_rect = pygame.Rect(
                pipe["x"],  # It will continuously shift to the left
                pipe["gap_y"] + self.pipe_gap // 2,  # The Y coordinate of the right corner of the bottom column is 90 pixels forward of the center of the gap between the two columns, resulting in a gap of 180 pixels
                self.pipe_width,  # Column width
                self.height  # Pygame automatically cuts off the part that is off-screen, so it's no problem if the rectangle is 600 pixels high and hangs way over the screen
            )
            # Drawing columns
            pygame.draw.rect(self.screen, (0, 149, 255), top_rect)
            pygame.draw.rect(self.screen, (0, 149, 255), bottom_rect)
        
    def check_collision(self):
        # We create a rectangle because Pygame can calculate collisions fastest with rectangles
        player_rect = pygame.Rect(
            # Create a square whose sides are equal to the diameter of the circle
            self.player_x - self.player_radius,
            self.player_y - self.player_radius,
            self.player_radius * 2,
            self.player_radius * 2
        )
        # We iterate through the pipes
        for pipe in self.pipes:
            # Create the top column rectangle
            top_rect = pygame.Rect(
                # Top right corner of the top column
                pipe["x"],
                0,
                self.pipe_width,  # Column width
                pipe["gap_y"] - self.pipe_gap // 2  # Top column height is offset from the center of the gap between the two columns by 90 pixels, resulting in a gap of 180 pixels
            )
            # Create the bottom column rectangle
            bottom_rect = pygame.Rect(
                pipe["x"],
                pipe["gap_y"] + self.pipe_gap // 2,  # The Y coordinate of the right corner of the bottom column is 90 pixels forward of the center of the gap between the two columns, resulting in a gap of 180 pixels
                self.pipe_width,  # Column width
                self.height  # Pygame automatically cuts off the part that is off-screen, so it's no problem if the rectangle is 600 pixels high and hangs way over the screen
            )
            # If the top rectangle collides with the player, then True
            if player_rect.colliderect(top_rect):
                return True
            # If the bottom rectangle collides with the player, then True
            if player_rect.colliderect(bottom_rect):
                return True
        return False  # If the player does not collide with anything then False
