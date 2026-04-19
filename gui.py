import tkinter as tk
import logger
from datetime import datetime

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.logger = logger.Logger()

        self.title("Pay Logger")
        self.geometry("800x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frames = {}
        pages = (HomeScreen, NewLog, ViewLogs, DeleteLogs, NewPayDay)
        for Page in pages:
            frame = Page(self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(HomeScreen)

    def show_frame(self, page):
        self.frames[page].tkraise()
        
class HomeScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        titleLabel = tk.Label(self, text="Pay Logger", font=("Arial", 16))
        titleLabel.pack(pady=10)

        promptLabel = tk.Label(self, text="What would you like to do?", font=("Arial", 16))
        promptLabel.pack(pady=10)

        # buttons
        tk.Button(self, text="Add New Log", 
                              command=lambda : master.show_frame(NewLog)).pack()

        tk.Button(self, text="View Logs", 
                  command=lambda : master.show_frame(ViewLogs)).pack()

        tk.Button(self, text="Delete Log",
                  command=lambda : master.show_frame(DeleteLogs)).pack()

        tk.Button(self, text="Add Payday",
                    command=lambda : master.show_frame(NewPayDay)).pack()
        
        tk.Button(self, text="Done", command=master.destroy).pack()

class NewLog(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = tk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1) 
        
        # validation functions
        def checkMonth(month):
            if month == "":
                return True

            if not month.isdigit():
                return False

            if len(month) > 2:
                return False

            month = int(month)
            return 1 <= month <= 12

        monthCmd = (self.register(checkMonth), "%P")
       
        def checkDay(day):
            if day == "":
                return True

            if not day.isdigit():
                return False

            if len(day) > 2:
                return False

            day = int(day)
            return 1 <= day <= 31
        
        dayCmd = (self.register(checkDay), "%P")

        # used to show current logs
        self.display = tk.Text(inner, height=21, width=50)
        self.display.grid(row=0, column=0, columnspan=2, pady=10)
        self.display.config(state="disabled")
        self.refreshDisplay()

        tk.Label(inner, text="Enter Date:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        date_frame = tk.Frame(inner)
        date_frame.grid(row=1, column=1, sticky="w")

        def checkYear(value):
            if value == "":
                return True

            if not value.isdigit():
                return False

            if len(value) > 4:
                return False

            return True
        
        yearCmd = (self.register(checkYear), "%P")

        def validateMoney(value):
            if value == "":
                return True

            if value.count(".") > 1:
                return False
            
            try:
                float(value)
            except ValueError:
                return False
            
            if "." in value:
                decimals = value.split(".")[1]
                if len(decimals) > 2:
                    return False
            
            return True

        checkMoney = (self.register(validateMoney), "%P")

        # enter month
        self.month = tk.Entry(date_frame, width=3, validate="key", validatecommand=monthCmd)
        self.month.pack(side=tk.LEFT)

        tk.Label(date_frame, text="/").pack(side=tk.LEFT)

        # enter day
        self.day = tk.Entry(date_frame, width=3, validate="key", validatecommand=dayCmd)
        self.day.pack(side=tk.LEFT)

        tk.Label(date_frame, text="/").pack(side=tk.LEFT)

        # enter year
        self.year = tk.Entry(date_frame, width=5, validate="key", validatecommand=yearCmd)
        self.year.pack(side=tk.LEFT)

        # enter card tip
        tk.Label(inner, text="Enter card tip:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.cardTip = tk.Entry(inner, width=30, validate="key", validatecommand=checkMoney)
        self.cardTip.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # enter cash tip
        tk.Label(inner, text="Enter cash tip:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.cashTip = tk.Entry(inner, width=30, validate="key", validatecommand=checkMoney)
        self.cashTip.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # enter hours
        tk.Label(inner, text="Enter hours worked:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.hours = tk.Entry(inner, width=30, validate="key", validatecommand=checkMoney)
        self.hours.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # submit button
        tk.Button(inner, text="Submit", command=self.submitLog).grid(row=5, column=0, pady=10)

        # back button
        tk.Button(inner, text="Back", 
                  command=lambda: master.show_frame(HomeScreen)).grid(row=5, column=1, pady=10)

        # error messages
        self.message = tk.Label(inner, text="", fg="red")
        self.message.grid(row=6, column=0, columnspan=2)
    
    def submitLog(self):
        month = self.month.get()
        day = self.day.get()
        year = self.year.get()

        card = self.cardTip.get()
        cash = self.cashTip.get()
        hours = self.hours.get()

        # Check empty fields
        if not (month and day and year and card and cash and hours):
            self.message.config(text="*Please fill in all fields!")
            return

        # Validate full date
        try:
            date = datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y")
        except ValueError:
            self.message.config(text="*Invalid date!")
            return

        # Convert numbers
        card = float(card)
        cash = float(cash)
        hours = float(hours)

        formatted_date = date.strftime("%m/%d/%Y")

        newEntry = (formatted_date, card, cash, hours)
        self.master.logger.addTip(newEntry)

        # clear entries and refresh display
        self.month.delete(0, tk.END)
        self.day.delete(0, tk.END)
        self.year.delete(0, tk.END)

        self.cardTip.delete(0, tk.END)
        self.cashTip.delete(0, tk.END)
        self.hours.delete(0, tk.END)
        self.refreshDisplay()

    def refreshDisplay(self):
        currLogs = self.master.logger.viewLast20TipLogs()

        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)
        self.display.insert(tk.END, currLogs)
        self.display.config(state="disabled")

class ViewLogs(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = tk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        inner.grid_columnconfigure(0, weight=1)

        text_frame = tk.Frame(inner)
        text_frame.grid(row=0, column=0, pady=10)

        self.display = tk.Text(text_frame, height=21, width=80, wrap="none")
        self.display.grid(row=0, column=0)

        self.display.config(state="disabled")

        # Vertical scrollbar
        v_scrollbar = tk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.display.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Horizontal scrollbar
        h_scrollbar = tk.Scrollbar(
            text_frame,
            orient="horizontal",
            command=self.display.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Link scrollbars to text widget
        self.display.config(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        # Make horizontal scrollbar stretch
        text_frame.grid_columnconfigure(0, weight=1)

        tk.Button(inner, text="View Tips Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllTipLogs()), width=25)\
            .grid(row=1, column=0, pady=3)

        tk.Button(inner, text="View Weekly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllWeeklyLogs()), width=25)\
            .grid(row=2, column=0, pady=3)

        tk.Button(inner, text="View Monthly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllMonthlyLogs()), width=25)\
            .grid(row=3, column=0, pady=3)

        tk.Button(inner, text="View Yearly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllYearlyLogs()), width=25)\
            .grid(row=4, column=0, pady=3)

        tk.Button(inner, text="View Payday Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllPaydayLogs()), width=25)\
            .grid(row=5, column=0, pady=3)

        tk.Button(inner, text="Back", width=25,
                  command=lambda: master.show_frame(HomeScreen))\
            .grid(row=6, column=0, pady=10)

    def displayLogs(self, text):
        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)
        self.display.insert(tk.END, text)
        self.display.config(state="disabled")

class DeleteLogs(tk.Frame):
    # Column widths
    COL_DATE  = 14
    COL_HOURS = 10
    COL_CARD  = 10
    COL_CASH  = 10
    COL_TOTAL = 10

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self._index_map = []

        inner = tk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        listBoxFrame = tk.Frame(inner)
        listBoxFrame.grid(row=0, column=0, pady=10)

        # Header label
        self.header = tk.Label(
            listBoxFrame,
            text=self._formatRow("Date", "Hours", "Card", "Cash", "Total"),
            font=("Courier", 10, "bold"),
            anchor="w",
            justify="left"
        )
        self.header.grid(row=0, column=0, sticky="w")

        # Listbox
        self.log_list = tk.Listbox(listBoxFrame, width=80, height=20, font=("Courier", 10))
        self.log_list.grid(row=1, column=0)

        # Scrollbars
        v_scroll = tk.Scrollbar(listBoxFrame, orient="vertical", command=self.log_list.yview)
        v_scroll.grid(row=1, column=1, sticky="ns")

        h_scroll = tk.Scrollbar(listBoxFrame, orient="horizontal", command=self.log_list.xview)
        h_scroll.grid(row=2, column=0, sticky="ew")

        self.log_list.config(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        listBoxFrame.grid_columnconfigure(0, weight=1)

        # Buttons
        tk.Button(inner, text="Load Logs", width=25,
                  command=self.loadLogs).grid(row=1, column=0, pady=5)

        tk.Button(inner, text="Delete Selected", width=25,
                  command=self.deleteSelected).grid(row=2, column=0, pady=5)

        tk.Button(inner, text="Back", width=25,
                  command=lambda: master.show_frame(HomeScreen)).grid(row=3, column=0, pady=10)

    def _formatRow(self, date, hours, card, cash, total):
        """Format a row with fixed-width columns so everything lines up."""
        return (
            f"{str(date):<{self.COL_DATE}}"
            f"{str(hours):<{self.COL_HOURS}}"
            f"{str(card):<{self.COL_CARD}}"
            f"{str(cash):<{self.COL_CASH}}"
            f"{str(total):<{self.COL_TOTAL}}"
        )

    def loadLogs(self):
        self.log_list.delete(0, tk.END)
        logs = self.master.logger.df

        for i, row in logs.iterrows():
            line = self._formatRow(
                row['Date'],
                row['Hours'],
                row['Card'],
                row['Cash'],
                row['Total Tip']
            )
            self.log_list.insert(tk.END, line)

        self._index_map = list(logs.index)

    def deleteSelected(self):
        selected = self.log_list.curselection()
        if not selected:
            return

        listbox_pos = selected[0]
        df_index = self._index_map[listbox_pos]

        self.log_list.delete(listbox_pos)
        self._index_map.pop(listbox_pos)

        self.master.logger.deleteLog(df_index)

class NewPayDay(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        tk.Button(self, text="Back",
                  command=lambda : master.show_frame(HomeScreen)).pack()