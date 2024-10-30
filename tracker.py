"""
    File name: tracker.py
    Author: Emek Kırarslan (bozbulanik)
    E-mail: "kirarslanemek@gmail.com"
    Date created: 13/10/2024 - 20:14:44
    Date last modified: 30/10/2024
    Python Version: 3.12.6
    Version: 0.0.1
    License: GNU-GPLv3
    Status: Production
"""    

from helpers import *
from pynput import keyboard, mouse
import os
import csv
import time
import math
from datetime import datetime
import subprocess
import click
from rich.console import Console
from rich import print
import ast
from rich.table import Table
from rich.align import Align
import urwid
import socket
import sys
from plotter import *

DPI = 96
INCH_TO_METER = 0.0254  # 1 inch = 0.0254 meters
LOG_INTERVAL = 1800  # 30 minutes

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class TerminalGraphWidget(urwid.WidgetWrap):
    def __init__(self, graph):
        self.text = urwid.Text("", align="center")
        self.graph = graph
        self.line_box = urwid.LineBox(self.text)
        self.filler = urwid.Filler(self.line_box, valign="middle")
        self.padding = urwid.Padding(self.filler, align="center", width=int(self.graph.get_size()[0]+10))
        super().__init__(self.padding)

    def update(self):
        canvas = "\n".join("".join(row).replace('\033[96m', '').replace('\033[0m', '') for row in self.graph.canvas)
        self.text.set_text(canvas)

class LivePage(urwid.WidgetWrap):
    def __init__(self):
        self.graph = TerminalGraph(title="Urwid Example", width=30, height=10, x_label="X", y_label="Value", x_divisions=5, y_divisions=8, x_min=0, x_max=15, y_min=0, y_max=15)
        self.graph_widget = [TerminalGraphWidget(self.graph), TerminalGraphWidget(self.graph), TerminalGraphWidget(self.graph), TerminalGraphWidget(self.graph)]
        self.graph_grid = urwid.GridFlow(self.graph_widget, cell_width=45, h_sep=2, v_sep=1, align='left')
        
        self.texts = [urwid.Text(f"Item {i}") for i in range(1, 10)]
        self.pile = urwid.Pile(self.texts)

        self.column = urwid.Columns([self.graph_grid, self.pile], dividechars=1)
        # Filler and Padding
        self.filler = urwid.Filler(self.column, valign="middle")
        self.padding = urwid.Padding(self.filler, align="center")
        self.scrollable = urwid.Scrollable(self.padding)
        super().__init__(self.scrollable)

    def update_graph(self, loop, user_data):
        self.graph.clear()
        x_range = (0, 2 * math.pi)
        self.graph.plot_function(math.sin, x_range, x_shift=time.time(), y_shift=0)
        self.graph.add_axes()
        #self.graph.draw()
        for x in self.graph_widget:
            x.update()
        loop.set_alarm_in(0.1, self.update_graph)

class ReportPage(urwid.WidgetWrap):
    def __init__(self):
        self.text = urwid.Text(f"Report Page")
        self.text = urwid.Filler(self.text)
        super().__init__(self.text)

class FooterWidget(urwid.WidgetWrap):
    def __init__(self, left_text, right_text):
        self.footer_text_left = urwid.Text(left_text, align="left")
        self.footer_text_right = urwid.Text(right_text, align="right")
        footer_elements = urwid.Columns([('weight', 1, self.footer_text_left),('weight', 1, self.footer_text_right)])
        footer = urwid.AttrMap(footer_elements, 'footer')
        super().__init__(footer)

    def update_text(self, text):
        self.footer_text_left.set_text(text)
         
class TUI(object):
    def __init__(self, log_dir, print_log):
        self.tab_names = ["Live", "Reports"]
        self.pages = [LivePage(), ReportPage()]
        self.current_tab = 0

        self.header = self.build_header()
        self.footer = FooterWidget(" STATUS","arrows: navigate, q: quit")
        self.view = urwid.Frame(header=self.header, footer=self.footer, body=self.pages[self.current_tab])

        self.palette = [
            ("selected", "black", "light blue"),
            ("default", "light gray", "black"),
            ('footer', 'black', 'white'),
            ('header', 'light gray', 'black'),
        ]

    def build_header(self):
        columns = []
        for idx, name in enumerate(self.tab_names):
            txt = urwid.Text(name, align='center')
            button = urwid.AttrMap(txt, None, focus_map="reversed")
            if idx == self.current_tab:
                button = urwid.AttrMap(button, "selected")
            columns.append(('weight', 1, button))
        return urwid.Columns(columns)

    def refresh_view(self):
        self.view.header = self.build_header()
        self.view.body = self.pages[self.current_tab]

    def unhandled_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == 'right':
            self.current_tab = (self.current_tab + 1) % len(self.tab_names)
        elif key == 'left':
            self.current_tab = (self.current_tab - 1) % len(self.tab_names)
        self.refresh_view()

    def run(self):
        self.refresh_view()
        self.loop = urwid.MainLoop(self.view, unhandled_input=self.unhandled_input, palette=self.palette)
        self.loop.set_alarm_in(0.1, self.pages[0].update_graph)
        self.loop.run()


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
        self.console = Console()

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
    def create_socket_lock(self, port=65432):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("localhost", port))
        except OSError:
            print("Another instance is already running.")
            sys.exit()
        return s
        
    def run(self):
        elapsed_time = 0
        lock = self.create_socket_lock()
        try:
            while True:
                self.log_app_usage()
                elapsed_time += 1
                if elapsed_time >= LOG_INTERVAL:
                    self.log()
                    if(self.print_log):
                        now = datetime.now()
                        log_date = now.strftime("%d/%m/%Y")
                        log_time = now.strftime("%H:%M:%S")
                        #self.console.log("Logged", log_locals=False, highlight=True)
                        
                        print(f"[{log_time}] - Logged.")
                    elapsed_time = 0
                time.sleep(1)
        except KeyboardInterrupt:
            self.log()
            now = datetime.now()
            log_time = now.strftime("%H:%M:%S")
            print(f"\n[{log_time}] Tracker stopped. Last activities are logged.")

        lock.close()
        
    def run_tui(self):
        print("Log: " + str(self.print_log))
        print("Path: " + self.log_file_path)

    def merge_dict(self, d, m):
        for key, value in m.items():
            if key in d:
                d[key] += value
            else:
                d[key] = value

        return d
                
    def report(self):
        grid = Table("Name", "Value",title="Tracker Statistics", expand=True, highlight=True, box=None)
        total_left_mouse_click = 0
        total_right_mouse_click = 0
        total_middle_mouse_click = 0
        total_key_press = 0
        total_mouse_movement = 0
        total_mouse_scroll = 0
        most_used_keys_statistics = {}
        most_used_apps_statistics = {}
        
        with open(self.log_file_path, 'r', newline='') as csv_file:
            reader = csv.reader(csv_file)
            reader.__next__()
            lines = list(reader)
            
            for row in lines:
                total_left_mouse_click += int(row[2])
                total_right_mouse_click += int(row[3])
                total_middle_mouse_click += int(row[4])
                total_key_press += int(row[5])
                total_mouse_movement += float(row[6])
                total_mouse_scroll += float(row[7])

                muks_dict = ast.literal_eval(row[8])
                most_used_keys_statistics = self.merge_dict(most_used_keys_statistics, muks_dict if row[8] != "None" else {})

                muas_dict = ast.literal_eval(row[9])
                most_used_apps_statistics = self.merge_dict(most_used_apps_statistics, muas_dict if row[9] != "None" else {})

        total_sum_muks = sum(most_used_keys_statistics.values())
        total_sum_muas = sum(most_used_apps_statistics.values())
        most_used_keys_statistics = dict(sorted(most_used_keys_statistics.items(), key=lambda x: x[1], reverse=True))     
        most_used_apps_statistics = dict(sorted(most_used_apps_statistics.items(), key=lambda x: x[1], reverse=True))     

        percentage_data_muks = {key: (value / total_sum_muks) * 100 for key, value in most_used_keys_statistics.items()}
        percentage_data_muas = {key: (value / total_sum_muas) * 100 for key, value in most_used_apps_statistics.items()}

        
        grid.add_row("Left Mouse Click" , str(total_left_mouse_click))
        grid.add_row("Right Mouse Click" , str(total_right_mouse_click))
        grid.add_row("Middle Mouse Click" , str(total_middle_mouse_click))
        grid.add_row("Key Press", str(total_key_press))
        grid.add_row("Mouse Movement" , f"{total_mouse_movement:.2f} meters")
        grid.add_row("Mouse Scroll" , f"{total_mouse_scroll:.2f} px")
        
        muks_result = ""
        for key, percentage in list(percentage_data_muks.items())[:5]:
            total_presses = most_used_keys_statistics[key]
            muks_result += f"{key}  - {percentage:.2f}%  -  {total_presses} presses" + "\n"

        grid.add_row("Top 5 Most Used Keys", muks_result)

        muas_result = ""
        for app, percentage in list(percentage_data_muas.items())[:5]:
            total_seconds = most_used_apps_statistics[app]
            total_minutes = total_seconds // 60
            muas_result += f"{app}  - {percentage:.2f}%  -  {total_minutes} minutes" + "\n"

        grid.add_row("Top 5 Most Used Apps", muas_result)
        
        print(grid)
                

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
    print("Starting tracker...")
    print("LOG INTERVAL: " + str(int(LOG_INTERVAL / 60)) + " minutes")
    tracker = Tracker(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    tracker.run()

@tracker_cli.command(name='tui')
@click.pass_context
def start_tui(ctx):
    """Starts the TUI version of the app."""
    print("Starting tracker-tui...")
    #tracker = Tracker(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    #tracker.run_tui()
    tui = TUI(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    tui.run()
@tracker_cli.command(name='report')
@click.pass_context
def report_usage(ctx):
    """Prints the reports of the tracker's current usage statistics."""
    tracker = Tracker(log_dir=ctx.obj['DIR'], print_log=ctx.obj['LOG'])
    tracker.report()    
        
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


