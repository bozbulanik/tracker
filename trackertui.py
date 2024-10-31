import urwid
from plotter import *

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
        self.text = urwid.Text("Live acitivities")
        
        # Graph setup
        self.graph = TerminalGraph(title="Urwid Example", width=45, height=10, x_label="X", y_label="Value", x_divisions=5, y_divisions=8, x_min=0, x_max=15, y_min=0, y_max=15)
        self.graph_widget = [TerminalGraphWidget(self.graph) for _ in range(4)]
        self.graph_grid = urwid.GridFlow(self.graph_widget, cell_width=50, h_sep=2, v_sep=1, align='left')
        
        # App pile with title and line box
        self.app_title = urwid.Text("Application Items")
        self.app_texts = [urwid.Text(f"Item {i}") for i in range(1, 10)]
        self.app_pile = urwid.Pile([urwid.AttrMap(w, "list") for w in self.app_texts])
        
        # Combine app title and pile in a line box
        self.app_box = urwid.LineBox(urwid.Pile([self.app_title, self.app_pile]))

        # Key pile with title and line box
        self.key_title = urwid.Text("Key Items")
        self.key_texts = [urwid.Text(f"Item {i}") for i in range(1, 10)]
        self.key_pile = urwid.Pile([urwid.AttrMap(w, "list") for w in self.key_texts])
        
        # Combine key title and pile in a line box
        self.key_box = urwid.LineBox(urwid.Pile([self.key_title, self.key_pile]))

        # Add a gap between app_box and key_box
        self.gap = urwid.Text("")  # Empty text for gap

        # Combine app_box, gap, and key_box into texts_pile
        self.texts_pile = urwid.Pile([self.app_box, self.gap, self.key_box])
        
        # Layout
        self.column = urwid.Columns([('weight', 50, self.graph_grid), ('weight', 30, self.texts_pile)], dividechars=1)
        self.allpile = urwid.Pile([self.text, self.column])

        # Filler and Padding
        self.filler = urwid.Filler(self.allpile, valign="middle")
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


class ReportType(urwid.WidgetWrap):
    def __init__(self, name, detail_widget):
        self.content = name
        self.detail_widget = detail_widget  # Store the detail widget associated with this report type
        t = urwid.AttrWrap(urwid.Text(self.content), "report_type", "report_type_selected")
        super().__init__(t)

    def selectable(self):
        return True
    
    def keypress(self, size, key):
        return key

class ReportList(urwid.WidgetWrap):
    def __init__(self):
        urwid.register_signal(self.__class__, ['show_details'])
        self.walker = urwid.SimpleFocusListWalker([])
        lb = urwid.ListBox(self.walker)
        super().__init__(lb)

    def modified(self):
        focus_w, _ = self.walker.get_focus()
        urwid.emit_signal(self, 'show_details', focus_w.detail_widget)  # Emit the detail widget

    def set_data(self, report_types):
        urwid.disconnect_signal(self.walker, 'modified', self.modified)

        while len(self.walker) > 0:
            self.walker.pop()
        
        self.walker.extend(report_types)
        urwid.connect_signal(self.walker, "modified", self.modified)
        self.walker.set_focus(0)

class ReportDetails(urwid.WidgetWrap):
    def __init__(self):
        placeholder = urwid.Text("No details available")
        super().__init__(placeholder)
        
    def set_report_type(self, detail_widget):
        # Update to the provided detail widget
        self._w = detail_widget


class TimelyStatistics(urwid.WidgetWrap):
    def __init__(self, time):
        t = urwid.Text(time)
        f = urwid.Filler(t)
        p = urwid.Padding(f, align="center")
        super().__init__(p)


class ReportPage(urwid.WidgetWrap):
    def __init__(self):
        yesterday = TimelyStatistics("Yesterday")
        lastweek = TimelyStatistics("Last Week")
        lastmonth = TimelyStatistics("Last Month")
        lastyear = TimelyStatistics("Last Year")

        detail2 = urwid.WidgetWrap(urwid.Pile([
            urwid.Text("Test2 Details"),
            urwid.Button("Perform Action")
        ]))
        self.report_types = [
            ReportType("Yesterday", yesterday),
            ReportType("Last Week", lastweek),
            ReportType("Last Month", lastmonth),
            ReportType("Last Year", lastyear),
            ReportType("Productivity", detail2)
        ]
        self.list_view = ReportList()
        self.list_view.set_data(self.report_types)
        self.detail_view = ReportDetails()
        urwid.connect_signal(self.list_view, 'show_details', self.show_details)
        col_rows = urwid.raw_display.Screen().get_cols_rows()
        h = col_rows[0] - 2
                
        f1 = urwid.Filler(self.list_view, valign='top', height=h)
        f2 = urwid.Filler(self.detail_view, valign='top')
        c_list = urwid.LineBox(f1, title="Report Type", title_align="left")
        c_details = urwid.LineBox(f2, title="Details", title_align="left")
        
        columns = urwid.Columns([('weight', 30, c_list), ('weight', 70, c_details)])
        super().__init__(columns)
        
    def show_details(self, detail_widget):
        self.detail_view.set_report_type(detail_widget)

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
        self.tab_names = ["Activity", "Reports"]
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
            ('list', 'light gray', 'black'),
            ("report_type", "light gray", "black"),
            ("report_type_selected", "black", "dark red"),
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
