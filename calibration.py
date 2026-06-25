class Calibration:
    def __init__(self):
        self.top_y = None  # Upper limit Y coordinate
        self.bottom_y = None  # Lower limit Y coordinate
        self.active = False

    # This will restore the object to its original state
    def reset(self):
        self.top_y = None
        self.bottom_y = None
        self.active = False

    def set_top(self, y):
        self.top_y = y  # Sets the upper Y limit
        self._check_ready()

    def set_bottom(self, y):
        self.bottom_y = y  # Sets the lower Y limit
        self._check_ready()

    def _check_ready(self):  # Private helper function (_)
        # If there is an upper and lower point, then it is active
        if self.top_y is not None and self.bottom_y is not None:
            self.active = True

    def get_progress(self, current_y):
        # If no upper or lower limit is set then we cannot calculate percentages
        if self.top_y is None or self.bottom_y is None:
            return 0.0
        # Simplification
        top = self.top_y
        bottom = self.bottom_y
        # Avoid division by zero
        if bottom == top:
            return 0.0
        progress = (current_y - top) / (bottom - top)  # We divide the distance of the current Y value from the upper limit by the distance between the upper and lower limits; this tells us what percentage of the total range we have moved
        # Clamping
        # Cannot go below zero
        if progress < 0:
            progress = 0
        # Cannot go above one
        if progress > 1:
            progress = 1
        return progress  # Return with progress
        
    def is_ready(self):
        # Returns whether we are ready to calculate progress
        return self.active