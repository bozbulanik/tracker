import time
import random
import math
import pynput

from pynput import keyboard, mouse
class TerminalGraph:
    def __init__(self, title="", width=80, height=20, x_label="X", y_label="Y", x_divisions=5, y_divisions=5, x_min = 0, x_max = 0, y_min = 0, y_max=0):
        self.title = title
        self.width = width
        self.height = height
        self.x_label = x_label
        self.y_label = y_label
        self.canvas = [[' ' for _ in range(width)] for _ in range(height)]
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.plot_width = width - 10  # Adjust for y-axis and padding
        self.plot_height = height - 5  # Adjust for x-axis and padding
        self.x_divisions = x_divisions
        self.y_divisions = y_divisions
        self.stream_data = []
                
    def clear(self):
        self.canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]

    def plot_point(self, x, y, marker='·', color='\033[96m'):
        plot_x = int(x) + 6  # Shift right to make space for y-axis
        plot_y = self.height - 4 - int(y)  # Shift up to make space for x-axis
        if 6 <= plot_x < self.width - 1 and 1 <= plot_y < self.height - 4:
            self.canvas[plot_y][plot_x] = f'{color}{marker}\033[0m'  # Color + marker + reset

    def plot_function(self, func, x_range, x_shift, y_shift, color='\033[96m', fixed=False):
        if(not fixed):
            self.x_min, self.x_max = x_range
            
        x_step = (self.x_max - self.x_min) / (self.plot_width - 1)
        y_values = [func(self.x_min + i * x_step + x_shift) + y_shift for i in range(self.plot_width)]

        marker_color = color
        self.y_min, self.y_max = min(y_values), max(y_values)

        # Check for division by zero
        if self.y_max == self.y_min:
            self.y_max += 1  # Avoid division by zero

        for i in range(self.plot_width):
            x = i
            y = (y_values[i] - self.y_min) / (self.y_max - self.y_min) * (self.plot_height - 1)
            if 0 <= y < self.plot_height:  # Ensure it fits within the plot area
                self.plot_point(x, y, color=marker_color)

    def plot_scatter(self, points, marker='·', color='\033[96m', fixed=False):
        if not points:
            return
        marker_color = color
        if not fixed:
            x_values, y_values = zip(*points)
            self.x_min, self.x_max = min(x_values), max(x_values)
            self.y_min, self.y_max = min(y_values), max(y_values)
    
        # Check for division by zero
        x_range = self.x_max - self.x_min
        y_range = self.y_max - self.y_min

        if x_range == 0:
            x_range += 1  # Avoid division by zero
        if y_range == 0:
            y_range += 1  # Avoid division by zero

        for x, y in points:
            plot_x = (x - self.x_min) / x_range * (self.plot_width - 1)
            plot_y = (y - self.y_min) / y_range * (self.plot_height - 1)
            if 0 <= plot_x < self.plot_width and 0 <= plot_y < self.plot_height:
                self.plot_point(plot_x, plot_y, marker, marker_color)
            
                
    def add_axes(self, time_chart=False):
        # Draw box
        for i in range(6, self.width - 1):
            self.canvas[1][i] = '─'  # Top border
            self.canvas[self.height - 4][i] = '─'  # Bottom border
        for i in range(1, self.height - 3):
            self.canvas[i][6] = '│'  # Left border
            self.canvas[i][self.width - 2] = '│'  # Right border

        # Draw corners
        self.canvas[1][6] = '┌'  # Top-left corner
        self.canvas[1][self.width - 2] = '┐'  # Top-right corner
        self.canvas[self.height - 4][6] = '└'  # Bottom-left corner
        self.canvas[self.height - 4][self.width - 2] = '┘'  # Bottom-right corner

        # Add axis labels
        x_label_pos = self.width // 2 - len(self.x_label) // 2
        for i, char in enumerate(self.x_label):
            self.canvas[self.height - 2][x_label_pos + i] = char

        # Y-axis label in top left corner
        for i, char in enumerate(self.y_label):
            if i < self.height - 5:  # Ensure it doesn't overflow
                self.canvas[1][i] = char
        # Title
        title_label_pos = self.width // 2 - len(self.title) // 2
        for i, char in enumerate(self.title):
            self.canvas[0][title_label_pos + i] = char
        
        # Add tick marks and values
        for i in range(self.x_divisions):
            x_tick_pos = 6 + (self.plot_width - 1) * i // (self.x_divisions - 1)
            if(time_chart):
                x_value = f"{60 - (60 * i // (self.x_divisions - 1))}s"
            else:
                x_value = f"{self.x_min + (self.x_max - self.x_min) * i / (self.x_divisions - 1):.2f}"
                
            for j, char in enumerate(x_value):
                if self.height - 3 < self.height and x_tick_pos - len(x_value)//2 + j < self.width:
                    self.canvas[self.height - 3][x_tick_pos - len(x_value)//2 + j] = char

        for i in range(self.y_divisions):
            y_tick_pos = self.height - 4 - (self.plot_height - 1) * i // (self.y_divisions - 1)
            y_value = f"{self.y_min + (self.y_max - self.y_min) * i / (self.y_divisions - 1):.2f}"
            for j, char in enumerate(y_value):
                if y_tick_pos < self.height and 1 + j < 6:
                    self.canvas[y_tick_pos][1 + j] = char

    def stream(self, value, fixed=False):
        current_time = time.time()
        self.stream_data.append((current_time, value))
        self.stream_data = [(t, v) for t, v in self.stream_data if current_time - t <= 60]

        if not self.stream_data:
            return

        current_time = time.time()
        if(fixed):
            y_range = self.y_max - self.y_min
            
        else:
            y_values = [v for _, v in self.stream_data]
            self.y_min, self.y_max = min(y_values), max(y_values)
            y_range = max(self.y_max - self.y_min, 0.1)
        
        for t, y in self.stream_data:
            x = self.plot_width - 1 - ((current_time - t) / 60) * (self.plot_width - 1)
            plot_y = (y - self.y_min) / y_range * (self.plot_height - 1)
            if 0 <= plot_y < self.plot_height:  # Ensure y is within the plot range
                self.plot_point(x + 6, plot_y)

        
    def draw(self, time_chart=False):
        self.add_axes(time_chart)
        for row in self.canvas:
            print(''.join(row))

    # FOR TUI
    def get_size(self):
        return [self.width, self.height]


def main():
    graph = TerminalGraph(width=80, height=20, x_label="X", y_label="Value", x_divisions=10, y_divisions=16, x_min=0, x_max=15, y_min=0, y_max=15)
    xvals = []

    points = [(0,0),(2,5),(6,10),(2,20),(9,2)]
    points2 = [(0, 7), (2, 3), (3, 2), (4, 5), (5, 3), (6, 6), (7, 6)]
    
    #graph.plot_scatter(points2)
    graph.plot_scatter(points, color='\033[91m')
    print("Scatter plot:")
    graph.draw()
    """
    while True:
        graph.clear()
        value = random.randint(4,7)
        graph.stream(value)
        

        print("\033[H\033[J", end="")
        graph.draw()
        print("Now: " + str(value))
        time.sleep(1)
     """
if __name__ == "__main__":
    main()

