import gspread
import pandas as pd
from datetime import datetime, timedelta
from gspread_dataframe import get_as_dataframe, set_with_dataframe

CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Outback Pay Logging"
MIN_WAGE = 17.65

class Logger():
    def __init__(self):
        # Connect to Sheets
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open(SPREADSHEET_NAME)

        # get each tab in sheets
        self.worksheet = sh.worksheet('Daily')
        self.df = get_as_dataframe(self.worksheet).dropna(how='all')

        self.weeklySheet = sh.worksheet('Weekly')
        self.dfWeekly = get_as_dataframe(self.weeklySheet).dropna(how='all')

        self.monthlySheet = sh.worksheet('Monthly')
        self.dfMonthly = get_as_dataframe(self.monthlySheet).dropna(how='all')

        self.yearlySheet = sh.worksheet('Yearly')
        self.dfYearly = get_as_dataframe(self.yearlySheet).dropna(how='all')

        self.payDaySheet = sh.worksheet('Payday')
        self.dfPayDay = get_as_dataframe(self.payDaySheet).dropna(how='all')

        self.aggregateLogs(self.weeklySheet,  self.dfWeekly,  self.df, freq='W',   colName='Week Ending', dateFmt='%m/%d/%Y')
        self.aggregateLogs(self.monthlySheet, self.dfMonthly, self.df, freq='MS',  colName='Month',       dateFmt='%m/%Y')
        self.aggregateLogs(self.yearlySheet,  self.dfYearly,  self.df, freq='YS',  colName='Year',        dateFmt='%Y')

    def checkNewWeek(self, prevDate):
        today = datetime.now()

        prevDateWeek = (prevDate.isocalendar()[0], prevDate.isocalendar()[1])
        currDateWeek = (today.isocalendar()[0], today.isocalendar()[1])

        if prevDateWeek != currDateWeek:
            return True
        
        return False

    def checkNewMonth(self, prevDate):
        today = datetime.now()
        return (today.year, today.month) != (prevDate.year, prevDate.month)

    def checkNewYear(self, last_date):
        today = datetime.now()
        return today.year != last_date.year

    def aggregateLogs(self, sheet, dfAgg, df, freq, colName, dateFmt):
        if df.empty:
            print(f"No daily logs found; skipping {colName} update.")
            return

        last_date = datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y")

        # Pick the right check function based on frequency
        if freq == 'W':
            if not self.checkNewWeek(last_date):
                return
        elif freq == 'MS':
            if not self.checkNewMonth(last_date):
                return
        elif freq == 'YS':
            if not self.checkNewYear(last_date):
                return

        temp_df = df.copy()
        temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")

        # Only calculate from after the last already-logged period
        if not dfAgg.empty:
            last_period = pd.to_datetime(dfAgg.iloc[-1][colName], format=dateFmt)
            temp_df = temp_df[temp_df['Date'] > last_period]

        if temp_df.empty:
            print(f"No new {colName.lower()} entries to add.")
            return

        aggregated = temp_df.groupby(pd.Grouper(key="Date", freq=freq)).agg({
            'Hours'     : 'sum',
            'Card'      : 'sum',
            'Cash'      : 'sum',
            'Total Tip' : 'sum'
        }).reset_index()

        # Drop periods with no hours worked
        aggregated = aggregated[aggregated['Hours'] > 0]

        # Drop the current incomplete period
        today = pd.Timestamp.now()
        if freq == 'W':
            aggregated = aggregated[aggregated['Date'] < today - pd.Timedelta(days=today.dayofweek)]
        elif freq == 'MS':
            aggregated = aggregated[aggregated['Date'].dt.month != today.month]
        elif freq == 'YS':
            aggregated = aggregated[aggregated['Date'].dt.year != today.year]

        if aggregated.empty:
            print(f"No completed {colName.lower()} periods to add.")
            return

        # Format
        aggregated['Date'] = aggregated['Date'].dt.strftime(dateFmt)
        aggregated = aggregated.rename(columns={'Date': colName})
        aggregated['Card'] = aggregated['Card'].round(2)
        aggregated['Cash'] = aggregated['Cash'].round(2)
        aggregated['Total Tip'] = aggregated['Total Tip'].round(2)

        updated = pd.concat([dfAgg, aggregated], ignore_index=True)
        set_with_dataframe(sheet, updated, include_index=False, resize=True)
        print(f"{colName} updated!")

    def sortByDate(self, df):
        temp_df = df.copy()
        temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")
        temp_df = temp_df.sort_values(by="Date")
        temp_df["Date"] = temp_df["Date"].dt.strftime("%m/%d/%Y")

        return temp_df

    def addTip(self, newEntry):
        day, card, cash, hours = newEntry

        totalTip = cash + card
        newLog = {
            "Date"      : day,
            "Hours"     : hours,
            "Card"      : card,
            "Cash"      : cash,
            "Total Tip" : totalTip
        }

        new_row_df = pd.DataFrame([newLog])
        updated_df = pd.concat([self.df, new_row_df], ignore_index=True)
        sorted_df = self.sortByDate(updated_df)

        set_with_dataframe(self.worksheet, sorted_df, include_index=False, resize=True)
        self.df = sorted_df

    def deleteLog(self, index):
        self.df = self.df.drop(index).reset_index(drop=True)
        set_with_dataframe(self.worksheet, self.df, include_index=False, resize=True)

    def addPayDay(self, newEntry):
        start, end, gross, tax = newEntry

        start = start.strftime("%m/%d/%Y")
        end = end.strftime("%m/%d/%Y")

        temp_df = self.df.copy()
        temp_df['Date'] = pd.to_datetime(temp_df['Date'], format='%m/%d/%Y')
        startDate = pd.to_datetime(start, format='%m/%d/%Y')
        endDate = pd.to_datetime(end, format='%m/%d/%Y')

        mask = (temp_df['Date'] >= startDate) & (temp_df['Date'] <= endDate)
        filtered_df = temp_df.loc[mask].sort_values("Date").copy()

        filtered_df['Date'] = filtered_df['Date'].dt.strftime('%m/%d/%Y')

        # calculations
        totalHours = round(filtered_df["Hours"].sum(), 2)
        workdayPay = round(gross - tax, 2)
        cardTotal = round(filtered_df["Card"].sum(), 2)
        cashTotal = round(filtered_df["Cash"].sum(), 2)
        totalTip = round(cardTotal + cashTotal, 2)
        beforeTax = round(totalTip + gross, 2)
        afterTax = round(beforeTax - tax, 2)
        hourlyAfterTax = round(afterTax / totalHours, 2)

        newLog = {
            "Start Date"                : start,
            "End Date"                  : end,
            "Total Hours"               : totalHours,
            "Gross Pay"                 : gross,
            "Tax"                       : tax,
            "Workday Pay"               : workdayPay,
            "Card Total"                : cardTotal,
            "Cash Total"                : cashTotal,
            "Tip Total"                 : totalTip,
            "Before Taxes"              : beforeTax,
            "After Taxes"               : afterTax,
            "Hourly Wage (After Taxes)" : hourlyAfterTax,
        }

        new_row_df = pd.DataFrame([newLog])
        updated_dfPayDay = pd.concat([self.dfPayDay, new_row_df], ignore_index=True)

        set_with_dataframe(self.payDaySheet, updated_dfPayDay, include_index=False, resize=True)
        self.dfPayDay = updated_dfPayDay