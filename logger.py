import gspread
import pandas as pd
from datetime import datetime
from gspread_dataframe import get_as_dataframe, set_with_dataframe

CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Outback Pay Logging"
MIN_WAGE = 17.65
LEGACY_CUTOFF = pd.Timestamp("2025-08-01")

class Logger():
    def __init__(self):
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open(SPREADSHEET_NAME)

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

        self.aggregateLogs(self.weeklySheet,  self.dfWeekly,  self.df, freq='W',   colName='Week Ending', dateFmt='%m/%d/%Y', dfAttr='dfWeekly')
        self.aggregateLogs(self.monthlySheet, self.dfMonthly, self.df, freq='MS',  colName='Month',       dateFmt='%m/%Y',    dfAttr='dfMonthly')
        self.aggregateLogs(self.yearlySheet,  self.dfYearly,  self.df, freq='YS',  colName='Year',        dateFmt='%Y',       dfAttr='dfYearly')

    def aggregateLogs(self, sheet, dfAgg, df, freq, colName, dateFmt, dfAttr=None):
        if df.empty:
            print(f"No daily logs found; skipping {colName} update.")
            return

        temp_df = df.copy()
        temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")

        if not dfAgg.empty:
            last_period = pd.to_datetime(dfAgg.iloc[-1][colName], format=dateFmt)

            if freq == 'W':
                cutoff = last_period
                temp_df = temp_df[temp_df['Date'] > cutoff]
            elif freq == 'MS':
                cutoff = last_period + pd.offsets.MonthEnd(0)
                temp_df = temp_df[temp_df['Date'] > cutoff]
            elif freq == 'YS':
                cutoff = last_period + pd.offsets.YearEnd(0)
                temp_df = temp_df[temp_df['Date'] > cutoff]

        if temp_df.empty:
            print(f"No new {colName.lower()} entries to add.")
            return

        aggregated = temp_df.groupby(pd.Grouper(key="Date", freq=freq)).agg({
            'Hours'     : 'sum',
            'Card'      : 'sum',
            'Cash'      : 'sum',
            'Total Tip' : 'sum'
        }).reset_index()

        aggregated = aggregated[aggregated['Hours'] > 0]

        today = pd.Timestamp.now()
        if freq == 'W':
            week_start = today - pd.Timedelta(days=today.dayofweek)
            aggregated = aggregated[aggregated['Date'] < week_start]
        elif freq == 'MS':
            aggregated = aggregated[
                (aggregated['Date'].dt.year != today.year) |
                (aggregated['Date'].dt.month != today.month)
            ]
        elif freq == 'YS':
            aggregated = aggregated[aggregated['Date'].dt.year != today.year]

        if aggregated.empty:
            print(f"No completed {colName.lower()} periods to add.")
            return

        aggregated['Date'] = aggregated['Date'].dt.strftime(dateFmt)
        aggregated = aggregated.rename(columns={'Date': colName})
        aggregated['Card'] = aggregated['Card'].round(2)
        aggregated['Cash'] = aggregated['Cash'].round(2)
        aggregated['Total Tip'] = aggregated['Total Tip'].round(2)

        if not dfAgg.empty:
            existing_periods = set(dfAgg[colName].astype(str))
            aggregated = aggregated[~aggregated[colName].astype(str).isin(existing_periods)]

        if aggregated.empty:
            print(f"No new {colName.lower()} periods to add after deduplication.")
            return

        updated = pd.concat([dfAgg, aggregated], ignore_index=True)
        set_with_dataframe(sheet, updated, include_index=False, resize=True)
        if dfAttr:
            setattr(self, dfAttr, updated)
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

        startDate = pd.Timestamp(start)
        endDate   = pd.Timestamp(end)
        startStr  = start.strftime("%m/%d/%Y")
        endStr    = end.strftime("%m/%d/%Y")

        workdayPay = round(gross - tax, 2)

        if endDate < LEGACY_CUTOFF:
            # Legacy entry: no tip data, zero everything tip-related
            newLog = {
                "Start Date"                : startStr,
                "End Date"                  : endStr,
                "Total Hours"               : 0,
                "Gross Pay"                 : gross,
                "Tax"                       : tax,
                "Workday Pay"               : workdayPay,
                "Card Total"                : 0,
                "Cash Total"                : 0,
                "Tip Total"                 : 0,
                "Before Taxes"              : gross,
                "After Taxes"               : workdayPay,
                "Hourly Wage (After Taxes)" : 0,
            }
        else:
            temp_df = self.df.copy()
            temp_df['Date'] = pd.to_datetime(temp_df['Date'], format='%m/%d/%Y')

            mask = (temp_df['Date'] >= startDate) & (temp_df['Date'] <= endDate)
            filtered_df = temp_df.loc[mask].sort_values("Date").copy()
            filtered_df['Date'] = filtered_df['Date'].dt.strftime('%m/%d/%Y')

            totalHours = round(filtered_df["Hours"].sum(), 2)
            if totalHours == 0:
                print("No hours found in date range — check your start/end dates.")
                return

            cardTotal       = round(filtered_df["Card"].sum(), 2)
            cashTotal       = round(filtered_df["Cash"].sum(), 2)
            totalTip        = round(cardTotal + cashTotal, 2)
            beforeTax       = round(totalTip + gross, 2)
            afterTax        = round(beforeTax - tax, 2)
            hourlyAfterTax  = round(afterTax / totalHours, 2)

            newLog = {
                "Start Date"                : startStr,
                "End Date"                  : endStr,
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