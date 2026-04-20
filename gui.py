import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import logger
from datetime import datetime

class App(ThemedTk):
    # style
    FONT_BOLD = ("Courier", 10, "bold")
    FONT = ("Courier", 10)


    def __init__(self):
        super().__init__()
        self.set_theme("yaru")
        self.logger = logger.Logger()

        self.title("Pay Logger")
        self.geometry("800x700")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # validation cmds
        self.monthCmd = (self.register(self.checkMonth), "%P")
        self.dayCmd = (self.register(self.checkDay), "%P")
        self.yearCmd = (self.register(self.checkYear), "%P")
        self.moneyCmd = (self.register(self.checkMoney), "%P")

        self.frames = {}
        pages = (HomeScreen, NewLog, ViewLogs, DeleteLogs, NewPayDay)
        for Page in pages:
            frame = Page(self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(HomeScreen)

    def show_frame(self, page):
        self.frames[page].tkraise()

    # validation functions
    def checkMonth(self, month):
        if month == "":
            return True
        
        if not month.isdigit():
            return False
        
        if len(month) > 2:
            return False
        
        month = int(month)
        return 1 <= month <= 12

    def checkDay(self, day):
        if day == "":
            return True
        
        if not day.isdigit():
            return False
        
        if len(day) > 2:
            return False
        
        day = int(day)
        return 1 <= day <= 31

    def checkYear(self, year):
        if year == "":
            return True
        
        if not year.isdigit():
            return False
        
        if len(year) > 4:
            return False
        
        return True

    def checkMoney(self, amount):
        if amount == "":
            return True
        
        if amount.count(".") > 1:
            return False
        
        try:
            float(amount)
        except ValueError:
            return False
        
        if "." in amount:
            decimals = amount.split(".")[1]
            if len(decimals) > 2:
                return False
            
        return True
    
    def validateFullDate(self, month, day, year):
        try:
            date = datetime.strptime(f"{month}/{day}/{year}", "%m/%d/%Y")
        except ValueError:
            return None

        return date

        
class HomeScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        titleLabel = tk.Label(self, text="Pay Logger", font=("Arial", 16))
        titleLabel.pack(pady=10)

        promptLabel = tk.Label(self, text="What would you like to do?", font=("Arial", 16))
        promptLabel.pack(pady=10)

        # buttons
        ttk.Button(self, text="Add New Log", 
                              command=lambda : master.show_frame(NewLog)).pack()

        ttk.Button(self, text="View Logs", 
                  command=lambda : master.show_frame(ViewLogs)).pack()

        ttk.Button(self, text="Delete Log",
                  command=lambda : master.show_frame(DeleteLogs)).pack()

        ttk.Button(self, text="Add Payday",
                    command=lambda : master.show_frame(NewPayDay)).pack()
        
        ttk.Button(self, text="Done", command=master.destroy).pack()

class NewLog(ttk.Frame):    
    # Column widths
    COL_DATE  = 14
    COL_HOURS = 10
    COL_CARD  = 10
    COL_CASH  = 10
    COL_TOTAL = 10

    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1) 
        
        # used to show current logs
        self.display = tk.Text(inner, height=23, width=50, font=self.master.FONT)
        self.display.grid(row=0, column=0, columnspan=2, pady=10)
        self.display.config(state="disabled")
        self.refreshDisplay()

        # Enter date for new log
        tk.Label(inner, text="Enter Date:", font=self.master.FONT_BOLD).\
            grid(row=1, column=0, sticky="e", padx=5, pady=5)
        dateFrame = ttk.Frame(inner)
        dateFrame.grid(row=1, column=1, sticky="w")

        # enter month
        self.month = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.monthCmd)
        self.month.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/", font=self.master.FONT_BOLD).pack(side=tk.LEFT)

        # enter day
        self.day = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.dayCmd)
        self.day.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/", font=self.master.FONT_BOLD).pack(side=tk.LEFT)

        # enter year
        self.year = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=self.master.yearCmd)
        self.year.pack(side=tk.LEFT)

        # enter card tip
        tk.Label(inner, text="Enter card tip:", font=self.master.FONT_BOLD).\
            grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.cardTip = ttk.Entry(inner, width=30, validate="key", validatecommand=self.master.moneyCmd)
        self.cardTip.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # enter cash tip
        tk.Label(inner, text="Enter cash tip:", font=self.master.FONT_BOLD).\
            grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.cashTip = ttk.Entry(inner, width=30, validate="key", validatecommand=self.master.moneyCmd)
        self.cashTip.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # enter hours
        tk.Label(inner, text="Enter hours worked:", font=self.master.FONT_BOLD).\
            grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.hours = ttk.Entry(inner, width=30, validate="key", validatecommand=self.master.moneyCmd)
        self.hours.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # button style 
        btnStyle = ttk.Style()
        btnStyle.configure("My.TButton", font=self.master.FONT_BOLD)

        # submit button
        ttk.Button(inner, text="Submit", style="My.TButton",
                   command=self.submitLog).grid(row=5, column=0, pady=10)

        # back button
        ttk.Button(inner, text="Back", style="My.TButton",
                  command=lambda: master.show_frame(HomeScreen)).grid(row=5, column=1, pady=10)

        # error messages
        self.errMessage = tk.Label(inner, text="", fg="red", font=self.master.FONT)
        self.errMessage.grid(row=6, column=0, columnspan=2)
    
    def formatRow(self, date, hours, card, cash, total):
        return (
            f"{str(date):<{self.COL_DATE}}"
            f"{str(hours):<{self.COL_HOURS}}"
            f"{str(card):<{self.COL_CARD}}"
            f"{str(cash):<{self.COL_CASH}}"
            f"{str(total):<{self.COL_TOTAL}}"
        )
    
    def submitLog(self):
        month = self.month.get()
        day = self.day.get()
        year = self.year.get()

        card = self.cardTip.get()
        cash = self.cashTip.get()
        hours = self.hours.get()

        # Check empty fields
        if not (month and day and year and card and cash and hours):
            self.errMessage.config(text="*Please fill in all fields!", font=self.master.FONT)
            return

        # check full date        
        date = self.master.validateFullDate(month, day, year)
        if date is None:
            self.errMessage.config(text="Invalid Date!", font=self.master.FONT)
            return

        # Convert numbers
        card = float(card)
        cash = float(cash)
        hours = float(hours)

        formatted_date = date.strftime("%m/%d/%Y")

        newEntry = (formatted_date, card, cash, hours)
        self.master.logger.addTip(newEntry)
        self.clearEntries()
        self.refreshDisplay()

    def clearEntries(self):
        # clear entries and refresh display
        self.month.delete(0, tk.END)
        self.day.delete(0, tk.END)
        self.year.delete(0, tk.END)

        self.cardTip.delete(0, tk.END)
        self.cashTip.delete(0, tk.END)
        self.hours.delete(0, tk.END)
    
    def refreshDisplay(self):
        logs = self.master.logger.df.tail(10)

        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)

        # header
        header = self.formatRow("Date", "Hours", "Card", "Cash", "Total")
        self.display.tag_configure("header", font=self.master.FONT_BOLD)
        self.display.insert(tk.END, header + "\n", "header")

        # rows
        for _, row in logs.iterrows():
            line = self.formatRow(
                row['Date'],
                row['Hours'],
                row['Card'],
                row['Cash'],
                row['Total Tip']

            )
            self.display.insert(tk.END, line + "\n")

        self.display.config(state="disabled")

class ViewLogs(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        inner.grid_columnconfigure(0, weight=1)

        text_frame = ttk.Frame(inner)
        text_frame.grid(row=0, column=0, pady=10)

        self.display = tk.Text(text_frame, height=21, width=80, wrap="none")
        self.display.grid(row=0, column=0)

        self.display.config(state="disabled")

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.display.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(
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

        ttk.Button(inner, text="View Tips Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllTipLogs()), width=25)\
            .grid(row=1, column=0, pady=3)

        ttk.Button(inner, text="View Weekly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllWeeklyLogs()), width=25)\
            .grid(row=2, column=0, pady=3)

        ttk.Button(inner, text="View Monthly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllMonthlyLogs()), width=25)\
            .grid(row=3, column=0, pady=3)

        ttk.Button(inner, text="View Yearly Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllYearlyLogs()), width=25)\
            .grid(row=4, column=0, pady=3)

        ttk.Button(inner, text="View Payday Logs",
                  command=lambda: self.displayLogs(self.master.logger.viewAllPaydayLogs()), width=25)\
            .grid(row=5, column=0, pady=3)

        ttk.Button(inner, text="Back", width=25,
                  command=lambda: master.show_frame(HomeScreen))\
            .grid(row=6, column=0, pady=10)

    def displayLogs(self, text):
        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)
        self.display.insert(tk.END, text)
        self.display.config(state="disabled")

class DeleteLogs(ttk.Frame):
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

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        listBoxFrame = ttk.Frame(inner)
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
        v_scroll = ttk.Scrollbar(listBoxFrame, orient="vertical", command=self.log_list.yview)
        v_scroll.grid(row=1, column=1, sticky="ns")

        h_scroll = ttk.Scrollbar(listBoxFrame, orient="horizontal", command=self.log_list.xview)
        h_scroll.grid(row=2, column=0, sticky="ew")

        self.log_list.config(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        listBoxFrame.grid_columnconfigure(0, weight=1)

        # Buttons
        ttk.Button(inner, text="Load Logs", width=25,
                  command=self.loadLogs).grid(row=1, column=0, pady=5)

        ttk.Button(inner, text="Delete Selected", width=25,
                  command=self.deleteSelected).grid(row=2, column=0, pady=5)

        ttk.Button(inner, text="Back", width=25,
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

class NewPayDay(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        # show current payday logs
        self.display = tk.Text(inner, height=21, width=80, wrap="none")
        self.display.grid(row=0, column=0, columnspan=2, pady=10)
        self.display.config(state="disabled")
        # display current payday logs
        self.refreshDisplay()
        
        # date frame
        tk.Label(inner, text="Enter Start/End Dates:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        dateFrame = ttk.Frame(inner)
        dateFrame.grid(row=1, column=1, sticky="w")

        # start date month
        self.startMonth = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.monthCmd)
        self.startMonth.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/").pack(side=tk.LEFT)

        # start date day
        self.startDay = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.dayCmd)
        self.startDay.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/").pack(side=tk.LEFT)

        # start date year
        self.startYear = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=self.master.yearCmd)
        self.startYear.pack(side=tk.LEFT)

        tk.Label(dateFrame, text=" to ").pack(side=tk.LEFT)
        
        #end date month
        self.endMonth = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.monthCmd)
        self.endMonth.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/").pack(side=tk.LEFT)

        # end  date day
        self.endDay = ttk.Entry(dateFrame, width=3, validate="key", validatecommand=self.master.dayCmd)
        self.endDay.pack(side=tk.LEFT)

        tk.Label(dateFrame, text="/").pack(side=tk.LEFT)

        # end date year
        self.endYear = ttk.Entry(dateFrame, width=5, validate="key", validatecommand=self.master.yearCmd)
        self.endYear.pack(side=tk.LEFT)

        # gross pay
        tk.Label(inner, text="Enter Gross Pay:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.grossPay = ttk.Entry(inner, width=15, validate="key", validatecommand=self.master.moneyCmd)
        self.grossPay.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # tax amount
        tk.Label(inner, text="Enter Tax Taken:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.taxAmount = ttk.Entry(inner, width=15, validate="key", validatecommand=self.master.moneyCmd)
        self.taxAmount.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # frame for buttons
        btnFrame = ttk.Frame(inner)
        btnFrame.grid(row=4, column=0, columnspan=2, pady=10)

        # submit button
        ttk.Button(btnFrame, text="Submit", command=self.submitLog).pack(side=tk.LEFT, padx=5)

        # back button
        ttk.Button(btnFrame, text="Back",
                  command=lambda : master.show_frame(HomeScreen)).pack(side=tk.LEFT, padx=5)

        # error messages
        self.errMessage = tk.Label(inner, text="", fg="red")
        self.errMessage.grid(row=6, column=0, columnspan=2)
    
    def checkFormFilled(self):
        if not (self.startMonth.get() and self.startDay.get() and self.startYear.get()):
            self.errMessage.config(text="*Please fill in start date!")
            return False
        
        if not (self.endMonth.get() and self.endDay.get() and self.endYear.get()):
            self.errMessage.config(text="*Please fill in end date!")
            return False

        if not self.grossPay.get():
            self.errMessage.config(text="*Please enter gross pay amount!")
            return False
        
        if not self.taxAmount.get():
            self.errMessage.config(text="*Please enter tax amount!")
            return False

        return True
    
    def clearEntries(self):
        self.startMonth.delete(0, tk.END)
        self.startDay.delete(0, tk.END)
        self.startYear.delete(0, tk.END)

        self.endMonth.delete(0, tk.END)
        self.endDay.delete(0, tk.END)
        self.endYear.delete(0, tk.END)

        self.grossPay.delete(0, tk.END)
        self.taxAmount.delete(0, tk.END)

    def refreshDisplay(self):
        currLogs = self.master.logger.viewLast20PayDayLogs()

        self.display.config(state="normal")
        self.display.delete("1.0", tk.END)
        self.display.insert(tk.END, currLogs)
        self.display.config(state="disabled")

    def submitLog(self):
        # check if form is filled
        if not self.checkFormFilled():
            return
        
        # check full start date
        fullStartDate = self.master.validateFullDate(self.startMonth.get(), 
                                               self.startDay.get(),
                                               self.startYear.get())
        
        if fullStartDate is None:
            self.errMessage.config(text="Invalid Start Date!")
            return
        
        # check full end date
        fullEndDate = self.master.validateFullDate(self.endMonth.get(),
                                             self.endDay.get(),
                                             self.endYear.get())

        if fullEndDate is None:
            self.errMessage.config(text="Invalid End Date!")
            return

        # convert gross pay and tax amount to float
        gross = float(self.grossPay.get())
        tax = float(self.taxAmount.get())

        newEntry = (fullStartDate, fullEndDate, gross, tax)
        self.master.logger.addPayDay(newEntry)

        # clear all entries after submission
        self.clearEntries()
        
        # display update payday logs
        self.refreshDisplay()

App().mainloop()