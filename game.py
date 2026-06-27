# Importing the necessary libraries
import pygame
import random


class Game:
    def __init__(self, width=800, height=600):
        pygame.init()  # Initializing pygame
        # Window size
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))  # Create window
        pygame.display.set_caption("Fitarcade")  # Window title
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
        self.running = True  # As long as it's true, the game runs
        self.spawn_pipe()  # Creating the first pipe

    def spawn_pipe(self):
        gap_y = random.randint(150, self.height - 150)  # We don't want the gap to be too high or too low
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
        self.screen.fill((30, 30, 30))  # Fills the entire screen with one color
        # Rendering the player
        pygame.draw.circle(
            self.screen,  # Surface
            (0, 255, 0),  #  Color
            (self.player_x, self.player_y),  # Center
            self.player_radius  # Radius
        )
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
            pygame.draw.rect(self.screen, (0, 200, 0), top_rect)
            pygame.draw.rect(self.screen, (0, 200, 0), bottom_rect)
        pygame.display.flip()  # Until this runs, the user won't see what we drew

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

    def handle_events(self):
        for event in pygame.event.get():  # We iterate through all the events that have occurred since the previous frame
            # If the user has closed the window, running will be false
            if event.type == pygame.QUIT:
                self.running = False

    def tick(self):
        self.clock.tick(60)  # We set the FPS to 60 on all machines