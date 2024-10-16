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
