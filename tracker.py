from pynput import keyboard, mouse
import os
import csv
import time
import math
from datetime import datetime
import subprocess

DPI = 96
INCH_TO_METER = 0.0254  # 1 inch = 0.0254 meters
LOG_INTERVAL = 100  # 1 minute in seconds

class Tracker:

    def __init__(self):
        self.key_press_count: int = 0
        self.left_mouse_click_count: int = 0
        self.right_mouse_click_count: int = 0
        self.middle_mouse_click_count: int = 0
        self.mouse_movement_distance: float = 0.0
        self.mouse_scroll_distance: float = 0.0
        self.last_mouse_position: tuple = None
        self.key_counts: dict = {}
        self.app_counts: dict = {}
        self.app_start_time: float = 0

        keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_press)
        mouse_listener = mouse.Listener(on_click=lambda x, y, b, p: self.on_mouse_click(x, y, b, p), on_move=self.on_mouse_move, on_scroll=self.on_mouse_scroll)

        keyboard_listener.start()
        mouse_listener.start()

    def clear_counts(self):
        self.key_press_count = 0
        self.left_mouse_click_count = 0
        self.right_mouse_click_count = 0
        self.middle_mouse_click_count = 0
        self.mouse_movement_distance = 0
        self.mouse_scroll_distance = 0
        self.last_mouse_position = None
        self.key_counts.clear()
        self.app_counts.clear()
        self.app_start_time = 0

    def get_current_focused_app(self) -> str:
        try:
            terminal_pid = subprocess.check_output(['xdotool', 'getwindowfocus', 'getwindowpid'], stderr=subprocess.STDOUT).strip().decode("utf-8")
            ps_info = subprocess.check_output(['ps', '--pid', terminal_pid, '-o', 'comm=']).strip().decode('utf-8')
            terminal_app = os.environ.get('TERM')
            if ps_info == terminal_app:
                try:
                    child_pids_output = subprocess.check_output(['ps', '--ppid', terminal_pid, '-o', 'pid=,comm=']).decode('utf-8').strip()
                    if child_pids_output:
                        child_processes = [line.split() for line in child_pids_output.splitlines()]
                        child_pid, child_comm = child_processes[0]
                        try:
                            grandchild_output = subprocess.check_output(['ps', '--ppid', child_pid, '-o', 'comm=']).decode('utf-8').strip()
                            if grandchild_output:
                                return grandchild_output
                            else:
                                return child_comm
                        except subprocess.CalledProcessError:
                            return child_comm
                    else:
                        return ps_info
                except subprocess.CalledProcessError:
                    return ps_info
            else:
                return ps_info
        except subprocess.CalledProcessError:
            return "i3"
            
    def log_app_usage(self):
        app_name = self.get_current_focused_app()

        if self.app_start_time == 0:
            self.app_start_time = time.time()
        
        elapsed_time = int(time.time() - self.app_start_time)

        #print(str(app_name) + " is working for " + str(elapsed_time) + " seconds.")
        if app_name in self.app_counts:
            self.app_counts[app_name] += elapsed_time
        else:
            self.app_counts[app_name] = elapsed_time
            
        self.app_start_time = time.time()

    def on_keyboard_press(self, key):
        self.key_press_count += 1
        key_char = getattr(key, 'char', str(key).replace('Key.', ''))
        self.key_counts[key_char] = self.key_counts.get(key_char, 0) + 1

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            if button == mouse.Button.left:
                self.left_mouse_click_count += 1
            elif button == mouse.Button.right:
                self.right_mouse_click_count += 1
            elif button == mouse.Button.middle:
                self.middle_mouse_click_count += 1

    def on_mouse_move(self, x, y):
        if self.last_mouse_position:
            dx = x - self.last_mouse_position[0]
            dy = y - self.last_mouse_position[1]
            pixel_distance = math.sqrt(dx**2 + dy**2)
            meter_distance = (pixel_distance / DPI) * INCH_TO_METER
            self.mouse_movement_distance += meter_distance

        self.last_mouse_position = (x, y)

    def on_mouse_scroll(self,x, y, dx, dy):
        self.mouse_scroll_distance += (abs(dx) + abs(dy)) * 0.001

    def log(self):
        now = datetime.now()
        log_date = now.strftime("%d/%m/%Y")
        log_time = now.strftime("%H:%M:%S")

        key_counts_sorted = dict(sorted(self.key_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        app_counts_sorted = dict(sorted(self.app_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        log_data = [
            log_date,
            log_time,
            self.left_mouse_click_count,
            self.right_mouse_click_count,
            self.middle_mouse_click_count,
            self.key_press_count,
            self.mouse_movement_distance,
            self.mouse_scroll_distance,
            key_counts_sorted or "None",
            app_counts_sorted or "None",
        ]

        file_exists = os.path.exists('log.csv')
        with open('log.csv', 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(['Log Date', 'Log Time', 'Left Click', 'Right Click', 'Middle Click', 'Keypress', 'Mouse Distance (meters)', 'Scroll Distance (delta accumulation)', 'Most Used Keys (presses)', 'Most Used Apps (seconds)'])
            writer.writerow(log_data)

        self.clear_counts()

    def run(self):
        elapsed_time = 0
        try:
            while True:
                self.log_app_usage()
                elapsed_time += 1
                if elapsed_time >= LOG_INTERVAL:
                    self.log()
                    print("Logged.")
                    elapsed_time = 0
        except KeyboardInterrupt:
            print("Tracker stopped.")

if __name__ == "__main__":
    tracker = Tracker()
    tracker.run()

