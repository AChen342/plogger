import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import logger
from datetime import datetime

class App(ThemedTk):
    FONT_BOLD = ("Courier", 10, "bold")
    FONT      = ("Courier", 10)

    # Tip log column widths
    COL_DATE  = 14
    COL_HOURS = 10
    COL_CARD  = 10
    COL_CASH  = 10
    COL_TOTAL = 10

    # Payday log column widths
    PAY_COLS = [14, 14, 10, 10, 10, 12, 10, 10, 10, 12, 12, 10]

    # Period log column widths
    COL_PERIOD = 16

    def __init__(self):
        super().__init__()
        self.set_theme("yaru")
        self.logger = logger.Logger()

        self.title("Pay Logger")
        self.geometry("800x700")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure button style once
        ttk.Style().configure("My.TButton", font=self.FONT_BOLD)

        # Validation commands
        self.monthCmd = (self.register(self.checkMonth), "%P")
        self.dayCmd   = (self.register(self.checkDay),   "%P")
        self.yearCmd  = (self.register(self.checkYear),  "%P")
        self.moneyCmd = (self.register(self.checkMoney), "%P")

        self.frames = {}
        for Page in (HomeScreen, NewLog, ViewLogs, DeleteLogs, NewPayDay):
            frame = Page(self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomeScreen)

    def show_frame(self, page):
        self.frames[page].tkraise()

    # --- Validation ---
    def checkMonth(self, v):
        if v == "": return True
        if not v.isdigit() or len(v) > 2: return False
        return 1 <= int(v) <= 12

    def checkDay(self, v):
        if v == "": return True
        if not v.isdigit() or len(v) > 2: return False
        return 1 <= int(v) <= 31

    def checkYear(self, v):
        if v == "": return True
        return v.isdigit() and len(v) <= 4

    def checkMoney(self, v):
        if v == "": return True
        if v.count(".") > 1: return False
        try: float(v)
        except ValueError: return False
        if "." in v and len(v.split(".")[1]) > 2: return False
        return True

    def validateFullDate(self, month, day, year):
        try:
            return datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y")
        except ValueError:
            return None

    # --- Shared formatting ---
    @staticmethod
    def fmt(v):
        """Format a value as a 2dp float, or string if not numeric."""
        try: return f"{float(v):.2f}"
        except (ValueError, TypeError): return str(v)

    def formatTipRow(self, date, hours, card, cash, total):
        return (
            f"{str(date):<{self.COL_DATE}}"
            f"{self.fmt(hours):<{self.COL_HOURS}}"
            f"{self.fmt(card):<{self.COL_CARD}}"
            f"{self.fmt(cash):<{self.COL_CASH}}"
            f"{self.fmt(total):<{self.COL_TOTAL}}"
        )

    def formatPeriodRow(self, period, hours, card, cash, total):
        return (
            f"{str(period):<{self.COL_PERIOD}}"
            f"{self.fmt(hours):<{self.COL_HOURS}}"
            f"{self.fmt(card):<{self.COL_CARD}}"
            f"{self.fmt(cash):<{self.COL_CASH}}"
            f"{self.fmt(total):<{self.COL_TOTAL}}"
        )

    def formatPaydayRow(self, start, end, hours, gross, tax, work, card, cash, tip, before, after, hourly):
        vals = [str(start), str(end),
                self.fmt(hours), self.fmt(gross), self.fmt(tax), self.fmt(work),
                self.fmt(card), self.fmt(cash), self.fmt(tip),
                self.fmt(before), self.fmt(after), self.fmt(hourly)]
        return "".join(f"{v:<{w}}" for v, w in zip(vals, self.PAY_COLS))

    # --- Shared widget helpers ---
    @staticmethod
    def makeScrolledText(parent, height, width):
        """Create a read-only tk.Text with vertical + horizontal scrollbars."""
        frame = ttk.Frame(parent)
        text = tk.Text(frame, height=height, width=width, wrap="none")
        text.grid(row=0, column=0)
        text.config(state="disabled")
        v = ttk.Scrollbar(frame, orient="vertical",   command=text.yview)
        h = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        v.grid(row=0, column=1, sticky="ns")
        h.grid(row=1, column=0, sticky="ew")
        text.config(yscrollcommand=v.set, xscrollcommand=h.set)
        frame.grid_columnconfigure(0, weight=1)
        return frame, text

    @staticmethod
    def renderRows(display, font_bold, header, rows):
        """Write a bold header + data rows into a scrolled Text widget."""
        display.config(state="normal")
        display.delete("1.0", tk.END)
        display.tag_configure("header", font=font_bold)
        display.insert(tk.END, header + "\n", "header")
        for row in rows:
            display.insert(tk.END, row + "\n")
        display.config(state="disabled")


class HomeScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        inner = ttk.Frame(self)
        inner.grid(row=0, column=0, pady=50)

        tk.Label(inner, text="Pay Logger",             font=master.FONT_BOLD).grid(row=0, column=0)
        tk.Label(inner, text="What would you like to do?", font=master.FONT_BOLD).grid(row=1, column=0)

        buttons = [
            ("Add New Log", NewLog),
            ("View Logs",   ViewLogs),
            ("Delete Log",  DeleteLogs),
            ("Add Payday",  NewPayDay),
        ]
        for i, (label, page) in enumerate(buttons, start=2):
            ttk.Button(inner, text=label, style="My.TButton",
                       command=lambda p=page: master.show_frame(p)).grid(row=i, column=0)

        ttk.Button(inner, text="Done", style="My.TButton",
                   command=master.destroy).grid(row=len(buttons) + 2, column=0)


class NewLog(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        # Display
        self.display = tk.Text(inner, height=23, width=50, font=master.FONT)
        self.display.grid(row=0, column=0, columnspan=2, pady=10)
        self.display.config(state="disabled")
        self.refreshDisplay()

        # Date
        tk.Label(inner, text="Enter Date:", font=master.FONT_BOLD).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        dateFrame = ttk.Frame(inner)
        dateFrame.grid(row=1, column=1, sticky="w")
        self.month = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.monthCmd)
        self.month.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.day = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.dayCmd)
        self.day.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.year = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=master.yearCmd)
        self.year.pack(side=tk.LEFT)

        # Tip / Hours fields
        fields = [
            ("Enter card tip:",     "cardTip"),
            ("Enter cash tip:",     "cashTip"),
            ("Enter hours worked:", "hours"),
        ]
        for i, (label, attr) in enumerate(fields, start=2):
            tk.Label(inner, text=label, font=master.FONT_BOLD).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(inner, width=30, validate="key", validatecommand=master.moneyCmd)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=5)
            setattr(self, attr, entry)

        ttk.Button(inner, text="Submit", style="My.TButton", command=self.submitLog).grid(row=5, column=0, pady=10)
        ttk.Button(inner, text="Back",   style="My.TButton", command=lambda: master.show_frame(HomeScreen)).grid(row=5, column=1, pady=10)

        self.errMessage = tk.Label(inner, text="", fg="red", font=master.FONT)
        self.errMessage.grid(row=6, column=0, columnspan=2)

    def submitLog(self):
        month, day, year = self.month.get(), self.day.get(), self.year.get()
        card, cash, hours = self.cardTip.get(), self.cashTip.get(), self.hours.get()

        if not (month and day and year and card and cash and hours):
            self.errMessage.config(text="*Please fill in all fields!")
            return

        date = self.master.validateFullDate(month, day, year)
        if date is None:
            self.errMessage.config(text="*Invalid date!")
            return

        self.master.logger.addTip((date.strftime("%m/%d/%Y"), float(card), float(cash), float(hours)))
        self.clearEntries()
        self.refreshDisplay()

    def clearEntries(self):
        for w in (self.month, self.day, self.year, self.cardTip, self.cashTip, self.hours):
            w.delete(0, tk.END)

    def refreshDisplay(self):
        logs = self.master.logger.df.tail(10)
        header = self.master.formatTipRow("Date", "Hours", "Card", "Cash", "Total")
        rows = [self.master.formatTipRow(r['Date'], r['Hours'], r['Card'], r['Cash'], r['Total Tip'])
                for _, r in logs.iterrows()]
        App.renderRows(self.display, self.master.FONT_BOLD, header, rows)


class ViewLogs(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)

        text_frame, self.display = App.makeScrolledText(inner, height=21, width=80)
        self.display.config(font=master.FONT)
        text_frame.grid(row=0, column=0, pady=10)

        buttons = [
            ("View Tips Logs",    self.loadTipLogs),
            ("View Weekly Logs",  self.loadWeeklyLogs),
            ("View Monthly Logs", self.loadMonthlyLogs),
            ("View Yearly Logs",  self.loadYearlyLogs),
            ("View Payday Logs",  self.loadPaydayLogs),
        ]
        for i, (label, cmd) in enumerate(buttons, start=1):
            ttk.Button(inner, text=label, style="My.TButton", command=cmd, width=25).grid(row=i, column=0, pady=3)

        ttk.Button(inner, text="Back", style="My.TButton", width=25,
                   command=lambda: master.show_frame(HomeScreen)).grid(row=len(buttons) + 1, column=0, pady=10)

    def _render(self, header, rows):
        App.renderRows(self.display, self.master.FONT_BOLD, header, rows)

    def loadTipLogs(self):
        df = self.master.logger.df[::-1]
        self._render(
            self.master.formatTipRow("Date", "Hours", "Card", "Cash", "Total"),
            [self.master.formatTipRow(r['Date'], r['Hours'], r['Card'], r['Cash'], r['Total Tip'])
             for _, r in df.iterrows()]
        )

    def _loadPeriodLogs(self, df, col_name):
        self._render(
            self.master.formatPeriodRow(col_name, "Hours", "Card", "Cash", "Total Tip"),
            [self.master.formatPeriodRow(r[col_name], r['Hours'], r['Card'], r['Cash'], r['Total Tip'])
             for _, r in df.iterrows()]
        )

    def loadWeeklyLogs(self):  self._loadPeriodLogs(self.master.logger.dfWeekly[::-1],  'Week Ending')
    def loadMonthlyLogs(self): self._loadPeriodLogs(self.master.logger.dfMonthly[::-1], 'Month')
    def loadYearlyLogs(self):  self._loadPeriodLogs(self.master.logger.dfYearly[::-1],  'Year')

    def loadPaydayLogs(self):
        df = self.master.logger.dfPayDay[::-1]
        self._render(
            self.master.formatPaydayRow("Start", "End", "Hours", "Gross", "Tax", "Work Pay",
                                        "Card", "Cash", "Tips", "Before Tax", "After Tax", "Hourly"),
            [self.master.formatPaydayRow(
                r['Start Date'], r['End Date'], r['Total Hours'], r['Gross Pay'], r['Tax'],
                r['Workday Pay'], r['Card Total'], r['Cash Total'], r['Tip Total'],
                r['Before Taxes'], r['After Taxes'], r['Hourly Wage (After Taxes)'])
             for _, r in df.iterrows()]
        )


class DeleteLogs(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self._index_map = []

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        listBoxFrame = ttk.Frame(inner)
        listBoxFrame.grid(row=0, column=0, pady=10)

        self.header = tk.Label(listBoxFrame,
            text=master.formatTipRow("Date", "Hours", "Card", "Cash", "Total"),
            font=master.FONT_BOLD, anchor="w", justify="left")
        self.header.grid(row=0, column=0, sticky="w")

        self.log_list = tk.Listbox(listBoxFrame, width=80, height=20, font=master.FONT)
        self.log_list.grid(row=1, column=0)

        v_scroll = ttk.Scrollbar(listBoxFrame, orient="vertical",   command=self.log_list.yview)
        h_scroll = ttk.Scrollbar(listBoxFrame, orient="horizontal", command=self.log_list.xview)
        v_scroll.grid(row=1, column=1, sticky="ns")
        h_scroll.grid(row=2, column=0, sticky="ew")
        self.log_list.config(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        listBoxFrame.grid_columnconfigure(0, weight=1)

        self.loadLogs()

        ttk.Button(inner, text="Refresh Logs",    width=25, style="My.TButton", command=self.loadLogs).grid(row=1, column=0, pady=5)
        ttk.Button(inner, text="Delete Selected", width=25, style="My.TButton", command=self.deleteSelected).grid(row=2, column=0, pady=5)
        ttk.Button(inner, text="Back",            width=25, style="My.TButton", command=lambda: master.show_frame(HomeScreen)).grid(row=3, column=0, pady=10)

    def loadLogs(self):
        self.log_list.delete(0, tk.END)
        logs = self.master.logger.df[::-1]
        for _, row in logs.iterrows():
            self.log_list.insert(tk.END, self.master.formatTipRow(
                row['Date'], row['Hours'], row['Card'], row['Cash'], row['Total Tip']))
        self._index_map = list(logs.index)

    def deleteSelected(self):
        selected = self.log_list.curselection()
        if not selected:
            return
        pos = selected[0]
        self.log_list.delete(pos)
        self.master.logger.deleteLog(self._index_map.pop(pos))


class NewPayDay(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        # Display
        display_frame, self.display = App.makeScrolledText(inner, height=10, width=80)
        self.display.config(font=master.FONT)
        display_frame.grid(row=0, column=0, columnspan=2, pady=10)
        self.refreshDisplay()

        # Start/End dates
        tk.Label(inner, text="Enter Start/End Dates:", font=master.FONT_BOLD).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        dateFrame = ttk.Frame(inner)
        dateFrame.grid(row=1, column=1, sticky="w")

        self.startMonth = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.monthCmd)
        self.startMonth.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.startDay = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.dayCmd)
        self.startDay.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.startYear = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=master.yearCmd)
        self.startYear.pack(side=tk.LEFT)

        tk.Label(dateFrame, text=" to ", font=master.FONT_BOLD).pack(side=tk.LEFT)

        self.endMonth = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.monthCmd)
        self.endMonth.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.endDay = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=master.dayCmd)
        self.endDay.pack(side=tk.LEFT)
        tk.Label(dateFrame, text="/", font=master.FONT_BOLD).pack(side=tk.LEFT)
        self.endYear = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=master.yearCmd)
        self.endYear.pack(side=tk.LEFT)

        # Gross / Tax
        tk.Label(inner, text="Enter Gross Pay:", font=master.FONT_BOLD).grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.grossPay = ttk.Entry(inner, width=15, validate="key", validatecommand=master.moneyCmd)
        self.grossPay.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(inner, text="Enter Tax Taken:", font=master.FONT_BOLD).grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.taxAmount = ttk.Entry(inner, width=15, validate="key", validatecommand=master.moneyCmd)
        self.taxAmount.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        btnFrame = ttk.Frame(inner)
        btnFrame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btnFrame, text="Submit", style="My.TButton", command=self.submitLog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btnFrame, text="Back",   style="My.TButton", command=lambda: master.show_frame(HomeScreen)).pack(side=tk.LEFT, padx=5)

        self.errMessage = tk.Label(inner, text="", fg="red", font=master.FONT)
        self.errMessage.grid(row=5, column=0, columnspan=2)

    def checkFormFilled(self):
        if not (self.startMonth.get() and self.startDay.get() and self.startYear.get()):
            self.errMessage.config(text="*Please fill in start date!"); return False
        if not (self.endMonth.get() and self.endDay.get() and self.endYear.get()):
            self.errMessage.config(text="*Please fill in end date!"); return False
        if not self.grossPay.get():
            self.errMessage.config(text="*Please enter gross pay amount!"); return False
        if not self.taxAmount.get():
            self.errMessage.config(text="*Please enter tax amount!"); return False
        return True

    def clearEntries(self):
        for w in (self.startMonth, self.startDay, self.startYear,
                  self.endMonth,   self.endDay,   self.endYear,
                  self.grossPay,   self.taxAmount):
            w.delete(0, tk.END)

    def refreshDisplay(self):
        df = self.master.logger.dfPayDay[::-1].head(20)
        header = self.master.formatPaydayRow("Start", "End", "Hours", "Gross", "Tax", "Work Pay",
                                             "Card", "Cash", "Tips", "Before Tax", "After Tax", "Hourly")
        rows = [self.master.formatPaydayRow(
                    r['Start Date'], r['End Date'], r['Total Hours'], r['Gross Pay'], r['Tax'],
                    r['Workday Pay'], r['Card Total'], r['Cash Total'], r['Tip Total'],
                    r['Before Taxes'], r['After Taxes'], r['Hourly Wage (After Taxes)'])
                for _, r in df.iterrows()]
        App.renderRows(self.display, self.master.FONT_BOLD, header, rows)

    def submitLog(self):
        if not self.checkFormFilled():
            return

        startDate = self.master.validateFullDate(self.startMonth.get(), self.startDay.get(), self.startYear.get())
        if startDate is None:
            self.errMessage.config(text="*Invalid Start Date!"); return

        endDate = self.master.validateFullDate(self.endMonth.get(), self.endDay.get(), self.endYear.get())
        if endDate is None:
            self.errMessage.config(text="*Invalid End Date!"); return

        self.master.logger.addPayDay((startDate, endDate, float(self.grossPay.get()), float(self.taxAmount.get())))
        self.clearEntries()
        self.refreshDisplay()


App().mainloop()