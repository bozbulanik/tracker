"""
    File name: tracker.py
    Author: Emek Kırarslan (bozbulanik)
    E-mail: "kirarslanemek@gmail.com"
    Date created: 13/10/2024 - 20:14:44
    Date last modified: 15/10/2024
    Python Version: 3.12.6
    Version: 0.0.1
    License: GNU-GPLv3
    Status: Production
"""    
from pynput import keyboard, mouse
import os
import csv
import time
import math
from datetime import datetime
import subprocess
import click

DPI = 96
INCH_TO_METER = 0.0254  # 1 inch = 0.0254 meters
LOG_INTERVAL = 100  # 1 minute in seconds

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_HELP_TEXT = r"""
  __               __          
 / /________ _____/ /_____ ____
/ __/ __/ _ `/ __/  '_/ -_) __/ 
\__/_/  \_,_/\__/_/\_\\__/_/   
                               
Usage: tracker [OPTIONS] COMMAND [ARGS] 

tracker - activity tracker for my personal use [version 0.0.1]
by bozbulanik

Commands:
    start                 Starts the tracker.
    tui                   Start the graphical (TUI) version.
    report                Generate and display a report of the results.
    help [COMMAND]        Show general help or help about a specific subcommand.

Options:
    -d, --dir DIRECTORY   Start the program with the specified directory for log file.
    -h, --help            Show this help message and exit.
    -l, --log             Print program logs.
    -v, --version         Print version.

"""

START_HELP_TEXT = r"""
Usage: tracker [OPTIONS] start 

tracker-start for tracker

Options:
    -d, --dir DIRECTORY   Start the program with the specified directory for log file.
    
Description:
    Starts the tracking app in the background and logs what it tracked to log.csv file.

Examples:
    tracker start
    tracker -d /path/to/dir start
"""
TUI_HELP_TEXT = r"""
Usage: tracker [OPTIONS] tui 

tracker-tui for tracker

Options:
    -d, --dir DIRECTORY   Start the program with the specified directory for log file.

Description:
    Starts the TUI app for real-time activity tracking.
    Logs what it tracked to log.csv file.

Examples:
    tracker tui
    tracker -d /path/to/dir tui
"""
REPORT_HELP_TEXT = r"""
Usage: tracker [OPTIONS] report 

tracker-report for tracker

Options:
    -d, --dir DIRECTORY   Start the program with the specified directory for log file.

Description:
    Prints a report from a specified log.csv file to the terminal.

Examples:
    tracker report
    tracker -d /path/to/dir report
"""
HELP_HELP_TEXT = r"""
Usage: tracker help [COMMAND]

tracker-help for tracker

Description:
    Prints a help text or a help text for specified command.

Examples:
    tracker help
    tracker help tui
    tracker help start
"""


class Tracker:
    def __init__(self, log_dir=None, print_log=None):
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

        self.log_dir = log_dir
        
        if(self.log_dir == None):
            self.log_file_path = "log.csv"
        else:
            os.makedirs(self.log_dir, exist_ok=True)
            self.log_file_path = os.path.join(self.log_dir, 'log.csv')
        
        keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_press)
        mouse_listener = mouse.Listener(on_click=lambda x, y, b, p: self.on_mouse_click(x, y, b, p), on_move=self.on_mouse_move, on_scroll=self.on_mouse_scroll)

        keyboard_listener.start()
        mouse_listener.start()

        self.print_log = print_log

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

        if app_name in self.app_counts:
            self.app_counts[app_name] += 1
        else:
            self.app_counts[app_name] = 1

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

        
        file_exists = os.path.exists(self.log_file_path)
        
        with open(self.log_file_path, 'a', newline='') as csv_file:
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
                    if(self.print_log):
                        print("Logged.")
                    elapsed_time = 0
        except KeyboardInterrupt:
            print("Tracker stopped.")

    def run_tui(self):
        print(self.print_log)
        print(self.log_file_path)

class CLIGroup(click.Group):
    def format_help(self, ctx, formatter):
        formatter.write(DEFAULT_HELP_TEXT)

    def get_command(self, ctx, cmd_name):
        """Handle invalid commands."""
        cmd = click.Group.get_command(self, ctx, cmd_name)
        if cmd is None:
            click.echo(f"\nInvalid command: {cmd_name} \n\nPlease type (tracker help) to see available commands.\n")
            ctx.exit()
        return cmd

    

@click.group(cls=CLIGroup, context_settings=CONTEXT_SETTINGS, invoke_without_command=True, epilog='Check out https://github.com/bozbulanik/tracker for more details.')
@click.option('-d', '--dir', type=click.Path(dir_okay=True, file_okay=False, resolve_path=True), help="Specify the directory to save log.csv.")
@click.option('-l', '--log', is_flag=True, help="Print program logs.")
@click.version_option(version='0.0.1')
@click.pass_context
def tracker_cli(ctx, dir, log):
    ctx.ensure_object(dict)
    ctx.obj['DIR'] = dir
    ctx.obj['LOG'] = log
    
    if ctx.invoked_subcommand is None:
        click.echo(DEFAULT_HELP_TEXT)
            

@tracker_cli.command(name='start')
@click.pass_context
def start_tracking(ctx):
    """Starts the tracking app."""
    print("Tracking starts.")

    tracker = Tracker(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    tracker.run()

@tracker_cli.command(name='tui')
@click.pass_context
def start_tui(ctx):
    """Starts the TUI version of the app."""
    print("Starting TUI version...")
    tracker = Tracker(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    tracker.run_tui()
    
@tracker_cli.command(name='report')
@click.option('-d', '--dir', type=click.Path(exists=True), help="Directory to read the log.csv from.")
def report_usage(dir):
    """Prints the reports of the tracker's current usage statistics."""
    log_file = os.path.join(dir or '', 'log.csv')
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            print(file.read())
    else:
        print(f"No log file found in {log_file}.")

@tracker_cli.command(name='help', options_metavar='[COMMAND]')
@click.argument('command', required=False)
def help_command(command):
    """Prints help text."""
    if command:
        match command:
            case "start":
                print(START_HELP_TEXT)
            case "tui":
                print(TUI_HELP_TEXT)
            case "report":
                print(REPORT_HELP_TEXT)
            case "help":
                print(HELP_HELP_TEXT) # I know...
            case _:
                print("\nInvalid argument. Please type (tracker help) to see available commands.\n")
    else:
        click.echo(DEFAULT_HELP_TEXT)


def main():
    try:
        tracker_cli(prog_name="tracker", standalone_mode=False)
    except click.exceptions.UsageError as e:
        click.echo(f"\n{e} \n\nPlease type (tracker help) to see available options.\n")
                    
        
if __name__ == "__main__":
    main()
