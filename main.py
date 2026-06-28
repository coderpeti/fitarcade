# Importing the necessary libraries
import sys
import cv2 as cv
import pygame
import numpy as np
from math import sqrt

# Importing parts of the app
from pose_tracker import PoseTracker
from calibration import Calibration
from game import Game

# Window
WIN_WIDTH, WIN_HEIGHT = 1280, 720
CAM_WIDTH = 640
MENU_WIDTH = 640
GAME_WIDTH = 640

# Colors
C_BG = (255, 214, 102)
C_BLUE = (0, 149, 255)
C_WHITE = (240, 240, 240)
C_DARK_GRAY = (50,  50,  65)
C_GREEN = (60,  200, 120)

# States
S_MENU = "menu"
S_PICK_JOINT = "pick_joint"  # Only for "Custom"
S_CALIBRATE = "calibrate"
S_GAME = "game"
S_GAME_OVER = "game_over"

# Categories and auto landmark for the first three
CATEGORIES = ["Squat", "Pull-up", "Push-up", "Custom"]
AUTO_LANDMARK = "nose"   # Nose used for the three preset exercises

# Selectable joints for "Custom" mode (display name → PoseTracker key)
JOINTS = {
    "Head": "nose",
    "Left shoulder": "right_shoulder",
    "Right shoulder": "left_shoulder",
    "Left elbow": "right_elbow",
    "Right elbow": "left_elbow",
    "Left wrist": "right_wrist",
    "Right wrist": "left_wrist",
    "Left hip": "right_hip",
    "Right hip": "left_hip",
    "Left knee": "right_knee",
    "Right knee": "left_knee",
    "Left ankle": "right_ankle",
    "Right ankle": "left_ankle",
}

# Stick-figure skeleton for joint picker (normalized 0-1 coordinates)
# Joint points
STICK_NODES = {
    "nose": (0.50, 0.15),
    "left_shoulder": (0.65, 0.25),
    "right_shoulder": (0.35, 0.25),
    "left_elbow": (0.78, 0.42),
    "right_elbow": (0.22, 0.42),
    "left_wrist": (0.88, 0.58),
    "right_wrist": (0.12, 0.58),
    "left_hip": (0.62, 0.55),
    "right_hip": (0.38, 0.55),
    "left_knee": (0.65, 0.75),
    "right_knee": (0.35, 0.75),
    "left_ankle": (0.67, 0.95),
    "right_ankle": (0.33, 0.95),
}
# The bones that connect the joints
STICK_BONES = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("right_shoulder", "right_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("right_hip", "right_knee"),
    ("left_knee", "left_ankle"),
    ("right_knee", "right_ankle"),
    ("nose", "left_shoulder"),
    ("nose", "right_shoulder"),
]

# When creating a font, you only need to specify the size and whether it should be bold or not
def make_font(size, bold=False):
    return pygame.font.SysFont("segoeui", size, bold=bold)

def draw_text(surface, text, font, color, cx, cy):  # surface: surface for text; text: text to be printed; font: the previously created font object
    img = font.render(text, True, color)  # Converts text to image
    surface.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))  # Writes the text (image) onto the surface

def draw_button(surface, rect, text, font):  # surface: surface of the button; rect: rectangle of the button; text: text to be printed; font: the previously created font object
    mx, my = pygame.mouse.get_pos()  # Mouse coordinates
    mx_local = mx - 640  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
    hovered = rect.collidepoint(mx_local, my)  # If the mouse coordinates are inside the rectangle, then hovered
    base_color = C_BLUE  # Button color
    bg = tuple(min(255, c + 30) for c in base_color) if hovered else base_color  # If hovered then it will lighten by 30 or if the value is too high then it will stay at 255 if not then base value
    pygame.draw.rect(surface, bg, rect, border_radius=10)  # Draws the button with rounded corners
    draw_text(surface, text, font, (255, 255, 255), rect.centerx, rect.centery)  # Writes the text in the center of the button 

def cam_frame_to_surface(frame):
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)  # We convert the OpenCV BGR color channels to RGB, which pygame also uses
    frame_resized = cv.resize(frame_rgb, (CAM_WIDTH, WIN_HEIGHT))  # Resizes the camera image to the size of the game window
    transposed_img = np.transpose(frame_resized, (1, 0, 2))  # Swaps the axes of the NumPy array with the axes of Pygame ((height, width, channels) -> (width, height, channels))
    surf = pygame.surfarray.make_surface(transposed_img)  # Creates an object that can be drawn in PyGame
    return surf  # Returns the completed Surface object
 
def main():
    pygame.init()  # Initializing Pygame
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Create window
    pygame.display.set_caption("Fitarcade")  # Window title
    # Fonts
    f_title = make_font(42, bold=True)
    f_large = make_font(28, bold=True)
    f_medium = make_font(22)
    f_small = make_font(17)

    tracker = PoseTracker(camera_index=0)  # Setting up MediaPipe and the camera
    calibration = Calibration()
    game = None
 
    state = S_MENU  # The player is first taken to the menu
    selected_category = None  # No category selected yet (squat, custom, etc...)
    selected_landmark = None  # No landmark selected yet
    records = {c: 0 for c in CATEGORIES}  # Initially, the record for each category is 0
 
    RX = CAM_WIDTH  # X-start of right panel
    RW = WIN_WIDTH - CAM_WIDTH  # Right panel width
 
    clock = pygame.time.Clock()  # If it weren't, it would run faster on a fast machine, slower on a slow machine
 
    running = True  # As long as it's true, the game runs
    while running:
        ok = tracker.update()  # Reads the next frame from the camera and runs pose detection; the reason is true/false depending on whether an image was obtained or not
        # We reset the click on each frame so that only the click in that frame counts
        click = False
        click_pos = (0, 0)
        for event in pygame.event.get():  # Goes through the pygame event queue (all keystrokes, mouse movements, window closings, etc. go here)
            # Clicking the X button stops the main cycle
            if event.type == pygame.QUIT:
                running = False
            # # If I pressed the left mouse button, it recorded that there was a click and where
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # event.button == 1 means left mouse button
                click = True
                click_pos = event.pos
 
        screen.fill(C_BG)  # Draw background
 
        if ok and tracker.get_frame() is not None:  # If there is a working camera and a frame
            # If a joint (e.g. "nose") is selected, draw only that joint highlighted
            if selected_landmark:
                cam_surf = cam_frame_to_surface(
                    tracker.draw_selected_landmark(selected_landmark)
                )
            # If nothing is selected, all detected joints are drawn
            else:
                cam_surf = cam_frame_to_surface(tracker.draw_landmarks())
            screen.blit(cam_surf, (0, 0))  # Draws the camera image in the upper left corner of the main window
        # If there is no camera, a placeholder is drawn
        else:
            pygame.draw.rect(screen, C_DARK_GRAY, (0, 0, CAM_WIDTH, WIN_HEIGHT))
            draw_text(screen, "No camera", f_medium, C_DARK_GRAY, CAM_WIDTH // 2, WIN_HEIGHT // 2)

        # Create the right panel, but don't draw it because we'll still be writing things on the canvas
        right_surf = pygame.Surface((RW, WIN_HEIGHT))
        right_surf.fill(C_BG)

        # If we are in the start menu
        if state == S_MENU:
            # The game title and instructions are written in the middle of the right panel
            draw_text(right_surf, "Fitarcade", f_title, C_BLUE, RW // 2, 120)
            draw_text(right_surf, "Choose a category:", f_medium, C_DARK_GRAY, RW // 2, 155)
 
            btn_width, btn_height = 320, 64  # Button width and height
            btn_x = (RW - btn_width) // 2  # The buttons will be in the middle of the right panel on the x axis, since RW // 2 - btn_width // 2 = (RW - btn_width) // 2
            for i, category in enumerate(CATEGORIES):  # We iterate through all categories
                by = 210 + i * 85  # The Y coordinates of the category buttons will always increase by 85 because they are multiplied by 85 depending on their index
                rect = pygame.Rect(btn_x, by, btn_width, btn_height)  # Button rectangle
                rec_str = f"Record: {records[category]}"  # Record belonging to the category
                draw_button(right_surf, rect, category.upper(), f_large)  # Draws the button, with the category name written in all uppercase letters
                draw_text(right_surf, rec_str, f_small, C_DARK_GRAY, btn_x + btn_width // 2, by + 72)  # Write the record below the button, exactly in the middle of the button on the x-axis
                if click:
                    cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                    cy_abs = click_pos[1]
                    if rect.collidepoint(cx_abs, cy_abs):  # If the button was clicked
                        selected_category = category  # The button's category becomes the selected category
                        calibration.reset()  # This resets the object to its original state, meaning that the top and bottom positions are not specified in the fitness exercise
                        # If the category is "Custom" then the landmark will not be automatically selected, which is why it jumps to the "S_PICK_JOINT" state
                        if category == "Custom":
                            selected_landmark = None
                            state = S_PICK_JOINT
                        # If the category is anything else, it uses the automatic landmark and immediately jumps to the "S_CALIBRATE" state
                        else:
                            selected_landmark = AUTO_LANDMARK
                            state = S_CALIBRATE

        # If you need to choose a joint (Custom mode)
        elif state == S_PICK_JOINT:
            draw_text(right_surf, "Custom mode", f_title, C_BLUE, RW // 2, 80)  # The name of the category
            draw_text(right_surf, "Click on the joint you want to track", f_small, C_DARK_GRAY, RW // 2, 120)  # The instruction
            # Stick figure drawing area
            figure_cx, figure_cy = 210, 200  # The starting Y and X coordinates of the figure
            figure_width = 220  # Total width of the figure
            figure_height = 300  # Total height of the figure
 
            joint_circles = {}  # This is where we will store the screen coordinates of each joint in the form (x, y), the key is the name of the joint (e.g. "left_knee"); we will use it later for click testing
 
            for (a, b) in STICK_BONES:  # We iterate through the list that tells us which landmark to connect to which
                ax = int(figure_cx + STICK_NODES[a][0] * figure_width)  # The x coordinate of the joint, since we multiply it by its actual thickness, because it is scaled from 0-1 by default, and add it to the starting pixel of the stick figure
                ay = int(figure_cy + STICK_NODES[a][1] * figure_height)  # The y coordinate of the joint, since we multiply it by its actual thickness, because it is scaled from 0-1 by default, and add it to the starting pixel of the stick figure
                bx = int(figure_cx + STICK_NODES[b][0] * figure_width)  # The x coordinate of the joint, since we multiply it by its actual thickness, because it is scaled from 0-1 by default, and add it to the starting pixel of the stick figure
                by = int(figure_cy + STICK_NODES[b][1] * figure_height)  # The y coordinate of the joint, since we multiply it by its actual thickness, because it is scaled from 0-1 by default, and add it to the starting pixel of the stick figure
                pygame.draw.line(right_surf, C_DARK_GRAY, (ax, ay), (bx, by), 3)  # A line is drawn between the two joints
                # We save the coordinates of the joints to the dictionary
                joint_circles[a] = (ax, ay)
                joint_circles[b] = (bx, by)
                # Depending on whether the given joint is selected, it is displayed in a different color and size
                is_selected_a = (selected_landmark == a)
                is_selected_b = (selected_landmark == b)
                color_a  = C_GREEN if is_selected_a else C_BLUE
                color_b  = C_GREEN if is_selected_b else C_BLUE
                pygame.draw.circle(right_surf, color_a, (ax, ay), 10 if is_selected_a else 7)
                pygame.draw.circle(right_surf, color_b, (bx, by), 10 if is_selected_b else 7)

            # Head circle
            head_x, head_y = joint_circles["nose"]
            pygame.draw.circle(right_surf, C_DARK_GRAY, (head_x, head_y - 18), 16, 3)
 
            if click:
                cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                cy_abs = click_pos[1]
                for key, (x, y) in joint_circles.items():
                    dist = sqrt((cx_abs - x) ** 2 + (cy_abs - y) ** 2)  # Calculate the distance between the mouse position and the joint during the mouse click using Pythagoras' theorem
                    # If the distance between the joint and the mouse position is less than 18 pixels, the given joint is selected
                    if dist < 18:
                        selected_landmark = key
 
            # Confirm button
            if selected_landmark:
                # We output the name of the selected join after finding its nicely formatted version using a comprehensive list
                key = [k for k, v in JOINTS.items() if v == selected_landmark]
                draw_text(right_surf, f"Selected: {key[0]}", f_medium, C_DARK_GRAY, RW // 2, 550)
                # We create a button that, when clicked, advances the state to "S_CALIBRATE"
                confirm_rect = pygame.Rect((RW - 240) // 2, 570, 240, 50)
                draw_button(right_surf, confirm_rect, "Next →", f_medium)
                if click:
                    cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                    cy_abs = click_pos[1]
                    if confirm_rect.collidepoint(cx_abs, cy_abs):
                        state = S_CALIBRATE
 
            # Back button
            back_rect = pygame.Rect(16, WIN_HEIGHT - 60, 120, 40)
            draw_button(right_surf, back_rect, "← Back", f_small)
            if click and back_rect.collidepoint(click_pos[0] - RX, click_pos[1]):
                state = S_MENU
 
        elif state == S_CALIBRATE:
            draw_text(right_surf, selected_category.upper(), f_title, C_BLUE, RW // 2, 80)  # The selected category will be written at the top
            draw_text(right_surf, "Calibration", f_large, C_DARK_GRAY, RW // 2, 120)  # Window name under category name
 
            landmark_pos = tracker.get_landmark(selected_landmark) if ok else None  # Get the position of the selected landmark if there is a picture
            current_y = landmark_pos[1] if landmark_pos else None  # If there is one, we select the Y coordinate of the landmark
 
            # Status dots
            top_done = calibration.top_y is not None  # If the top position is already selected true
            bottom_done = calibration.bottom_y is not None  # If the bottom position is already selected true
 
            # TOP button
            top_rect = pygame.Rect((RW - 300) // 2, 200, 300, 62)
            top_label = "TOP saved" if top_done else "▲  I'm UP"  # If the top position is already saved, its text will be different
            draw_button(right_surf, top_rect, top_label, f_medium)
 
            draw_text(right_surf, "Go to the UP position of the exercise, then press", f_small, C_DARK_GRAY, RW // 2, 275)  # Instruction
 
            # BOTTOM button
            bottom_rect = pygame.Rect((RW - 300) // 2, 300, 300, 62)
            bottom_label = "BOTTOM saved" if bottom_done else "▼  I'm DOWN"  # If the top position is already saved, its text will be different
            draw_button(right_surf, bottom_rect, bottom_label, f_medium)
 
            draw_text(right_surf, "Go to the LOW position of the exercise, then press", f_small, C_DARK_GRAY, RW // 2, 375)  # Instruction
 
            # Live Y feedback
            if current_y is not None:  # If there is a current Y coordinate, it will be displayed on the screen
                draw_text(right_surf, f"Current Y: {current_y}px", f_small, C_DARK_GRAY, RW // 2, 610)
                if calibration.is_ready():  # If the calibration is complete (top and bottom positions are set)
                    progress = calibration.get_progress(current_y)  # We ask what percentage of the selected path we have traveled
                    bar_x, bar_y, bar_w, bar_height = RW // 2 - 100, 575, 200, 22  # The coordinates of the top left corner of the button and its width and height
                    pygame.draw.rect(right_surf, C_DARK_GRAY, (bar_x, bar_y, bar_w, bar_height), border_radius=6)  # Basis bar
                    pygame.draw.rect(right_surf, C_GREEN, (bar_x, bar_y, int(bar_w * progress), bar_height), border_radius=6)  # The moving bar that moves depending on what percentage we are at
                    draw_text(right_surf, f"{int(progress * 100)}%", f_small, C_WHITE, RW // 2, bar_y + 11)  # We print the percentage we are at on the bar
 
            # Click handling
            if click:
                cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                cy_abs = click_pos[1]
                # If we click the top button, we set the current Y coordinate to the top position
                if top_rect.collidepoint(cx_abs, cy_abs) and current_y is not None:
                    calibration.set_top(current_y)
                # If we click the bottom button, we set the current Y coordinate to the bottom position
                if bottom_rect.collidepoint(cx_abs, cy_abs) and current_y is not None:
                    calibration.set_bottom(current_y)
 
            # When the calibration is complete, the START button to start the game will appear
            if calibration.is_ready():
                start_rect = pygame.Rect((RW - 280) // 2, 475, 280, 66)
                draw_button(right_surf, start_rect, "START", f_large)
                # If clicked we switch to the "S_GAME" state
                if click:
                    cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                    cy_abs = click_pos[1]
                    if start_rect.collidepoint(cx_abs, cy_abs):
                        game = Game(right_surf, width=RW, height=WIN_HEIGHT)
                        state = S_GAME
 
            # Back button
            back_rect = pygame.Rect(16, WIN_HEIGHT - 60, 120, 40)
            draw_button(right_surf, back_rect, "← Back", f_small)
            # If we click on it, we either go back to the menu or the joint selector depending on which category we are in and the calibration is reset
            if click and back_rect.collidepoint(click_pos[0] - RX, click_pos[1]):
                if selected_category != "Custom":
                    state = S_MENU 
                    calibration.reset()
                else:
                    state = S_PICK_JOINT
                    calibration.reset()

        elif state == S_GAME:
            landmark_pos = tracker.get_landmark(selected_landmark) if ok else None  # Get the position of the selected landmark if there is a picture
            if landmark_pos:
                progress = calibration.get_progress(landmark_pos[1])  # We ask what percentage of the selected path we have traveled
            else:
                progress = 0.5   # Fallback to middle if pose is lost

            game.update(progress)  # Update game logic with current body position
 
            # Check collision BEFORE drawing, stops the game immediately on hit
            if game.check_collision():
                game.running = False
                state = S_GAME_OVER
            else:
                game.draw()  # Draw game onto the offscreen surface
                right_surf = game.screen  # Pass the changes to the right panel
                draw_text(right_surf, f"Score: {game.score}", f_large, C_DARK_GRAY, 65, 20)  # Display score
                draw_text(right_surf, f"Record: {records[selected_category]}", f_small, C_DARK_GRAY, 48, 46)  # Displaying the record of a certain category
 
        elif state == S_GAME_OVER:
            final_score = game.score if game else 0  # Save the final score to a variable if there is a game
            # If the final result is greater than or equal to the previous record, then we modify the record
            is_new_record = final_score >= records[selected_category]
            if is_new_record:
                records[selected_category] = final_score
 
            # We create a new interface that supports alpha channel, i.e. transparency, thanks to pygame.SRCALPHA
            overlay = pygame.Surface((RW, WIN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 200))
            right_surf.blit(overlay, (0, 0))
 
            center_y = WIN_HEIGHT // 2 - 185  # Center of the Y axis minus 185 pixels
            # If there is a new record, we write "NEW RECORD!"
            if is_new_record:
                draw_text(right_surf, "NEW RECORD!", f_title, C_BG, RW // 2, center_y)
            # If there is no new record, we simply write "GAME OVER"
            else:
                draw_text(right_surf, "Game over", f_title, C_WHITE, RW // 2, center_y)
 
            draw_text(right_surf, selected_category.upper(), f_medium, C_WHITE, RW // 2, center_y + 40)  # Display category
            # Display achieved score with new font
            draw_text(right_surf, f"{final_score}", make_font(72, bold=True), C_WHITE, RW // 2, center_y + 120)
            draw_text(right_surf, "score", f_medium, C_WHITE, RW // 2, center_y + 165)

            # If there is no new record, we output the old one
            if not is_new_record:
                draw_text(right_surf, f"Record: {records[selected_category]}", f_medium, C_BG, RW // 2, center_y + 190)
 
            # Buttons
            again_rect = pygame.Rect((RW - 260) // 2, center_y + 260, 260, 58)
            draw_button(right_surf, again_rect, "Again", f_large)
            menu_rect  = pygame.Rect((RW - 260) // 2, center_y + 332, 260, 50)
            draw_button(right_surf, menu_rect,  "Menu", f_large)
 
            if click:
                cx_abs = click_pos[0] - RX  # The mouse X coordinate is between 640-1280 on the right panel, but the rect X coordinate is between 0-640, so they would never meet if we didn't subtract from mx the number of pixels the right panel is away from the edge of the window
                cy_abs = click_pos[1]
                # If we click the again button, it will return to the "S_CALIBRATE" state and reset the calibration
                if again_rect.collidepoint(cx_abs, cy_abs):
                    calibration.reset()
                    state = S_CALIBRATE
                # If we click the menu button, the selected category, landmark will disappear, the calibration will be reset and we will return to the "S_MENU" state
                if menu_rect.collidepoint(cx_abs, cy_abs):
                    selected_category = None
                    selected_landmark = None
                    calibration.reset()
                    game = None
                    state = S_MENU

        screen.blit(right_surf, (RX, 0))  # Draw the right panel
 
        pygame.display.flip()  # Refresh the screen, without it we wouldn't see anything
        clock.tick(60)  # The cycle should run at most 60 times per second
 
    tracker.release()  # Release camera
    pygame.quit()  # Closes the window, freeing up resources used by Pygame
    sys.exit()  # Exits the Python program
 
# It will only run from this file, not imported into another one
if __name__ == "__main__":
    main()