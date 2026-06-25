# Importing the necessary libraries
import cv2 as cv
import mediapipe as mp

class PoseTracker:
    # All objects have LANDMARKS in common
    LANDMARKS = {
        "nose": 0,
        "left_eye": 2,
        "right_eye": 5,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
    }

    def __init__(self, camera_index=0):  # If nothing is specified, camera 0 should be used
        self.cap = cv.VideoCapture(camera_index)  # Open camera
        self.mp_pose = mp.solutions.pose  # Save the pose estimation module
        self.mp_drawing = mp.solutions.drawing_utils  # To draw landmarks
        # Creating an AI model that recognizes a real human body
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,  # Video mode
            model_complexity=1,  # The complexity of the model is medium
            smooth_landmarks=True,  # Smooths the movement of landmarks
            min_detection_confidence=0.5,  # The model must be at least 50% sure that there is a person in the image
            min_tracking_confidence=0.5  # Mennyire bízhat a követésben
            )
            
        self.frame = None  # The current camera frame will be stored for later
        self.results = None

    def update(self):
        success, frame = self.cap.read()
        # If image failed to read then exits
        if not success:
            return False
        frame = cv.flip(frame, 1)  # Horizontal mirroring
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)  # OpenCV works with BGR while MediaPipe expects RGB, so we convert it
        self.results = self.pose.process(rgb)  # Finds body parts
        self.frame = frame  # Save the current frame
        return True  # Successful run
    
    def get_landmark(self, name):
        # Checks if such landmark exists
        if name not in self.LANDMARKS:
            return None
        # Checks if there is any recognition at all
        if (
            self.results is None  # True if tracker.update() has not run yet
            or self.results.pose_landmarks is None  # True if the model ran but did not find a person
        ):
            return None
        h, w, _ = self.frame.shape  # Query image size
        landmark_id = self.LANDMARKS[name]  # Find the landmark ID ("left_shoulder" -> 11)
        landmark = self.results.pose_landmarks.landmark[landmark_id]  # Retrieve Landmark object
        # Since we get the coordinates normalized, we scale them to pixel coordinates
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        return (x, y)  # Return with coordinates
    
    def draw_landmarks(self):
        # Checks if there is any recognition at all
        if (
            self.results is None  # True if tracker.update() has not run yet
            or self.results.pose_landmarks is None  # True if the model ran but did not find a person
        ):
            return self.frame
        output = self.frame.copy()  # Making a copy because list is immutable
        # Draws the skeleton on the given frame
        self.mp_drawing.draw_landmarks(
            output,  # This is the picture itself
            self.results.pose_landmarks,  # This contains the recognition result
            self.mp_pose.POSE_CONNECTIONS  # This predefined list tells you which points to connect with a line
        )
        return output  # The function returns the modified image
    
    def draw_selected_landmark(self, landmark_name):
        output = self.draw_landmarks()  # Drawing a complete skeleton
        point = self.get_landmark(landmark_name)  # Finds the selected point
        if point is not None:
            cv.circle(
                output,  # This is the picture itself
                point,  # Coordinate
                10,  # Radius of the circle
                (0, 255, 0),  # Color
                -1  # Line thickness filled
            )
        return output

    def get_frame(self):
        return self.frame  # Returns the current frame
    
    def release(self):
        self.cap.release()  # Closes the camera connection
        self.pose.close()  # Close MediaPipe object
        cv.destroyAllWindows()  # Close all windows