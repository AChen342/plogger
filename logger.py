import gspread
import pandas as pd
from datetime import datetime, timedelta
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from googleapiclient.discovery import build
from google.oauth2 import service_account
import sys

CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_NAME = "Outback Pay Logging"
CALENDAR_KEYWORD = "Hotschedules"
MIN_WAGE = 17.65


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def is_work_day():
    """Returns True if today has a shift in Google Calendar."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=creds)

    # Get start and end of today in UTC
    today = datetime.now().date()
    time_min = datetime.combine(today, datetime.min.time()).isoformat() + "Z"
    time_max = datetime.combine(today, datetime.max.time()).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="achen.w342@gmail.com",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    for event in events:
        title = event.get("summary", "")
        if CALENDAR_KEYWORD.lower() in title.lower():
            return True

    return False


def mainScreen():
    print("Pay Logger")
    print("What would you like to do? (Enter number)")
    print("1. Add New Log")
    print("2. View Logs")
    print("3. Delete Log")
    print("4. Add Payday")
    print("5. Done")


def checkNewWeek(prevDate):
    today = datetime.now()

    prevDateWeek = (prevDate.isocalendar()[0], prevDate.isocalendar()[1])
    currDateWeek = (today.isocalendar()[0], today.isocalendar()[1])

    if prevDateWeek != currDateWeek:
        return True
    
    return False


def checkNewMonth(prevDate):
    today = datetime.now()
    return (today.year, today.month) != (prevDate.year, prevDate.month)


def checkNewYear(last_date):
    today = datetime.now()
    return today.year != last_date.year



def weeklyLogs(weeklySheet, dfWeekly, df):
    if not checkNewWeek(datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y")):
        return

    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")

    # If weekly sheet has entries, only calculate from last entry onwards
    if not dfWeekly.empty:
        last_week_ending = pd.to_datetime(dfWeekly.iloc[-1]["Week Ending"], format="%m/%d/%Y")
        temp_df = temp_df[temp_df['Date'] > last_week_ending]

    if temp_df.empty:
        print("No new weeks to add.")
        return

    weekly = temp_df.groupby(pd.Grouper(key="Date", freq='W')).agg({
        'Hours'     : 'sum',
        'Card'      : 'sum',
        'Cash'      : 'sum',
        'Total Tip' : 'sum'
    }).reset_index()

    # get rid of weeks not worked
    weekly = weekly[weekly['Hours'] > 0]

    # drop current incomplete week
    today = pd.Timestamp.now()
    weekly = weekly[weekly['Date'] < today - pd.Timedelta(days=today.dayofweek)]

    if weekly.empty:
        print("No completed weeks to add.")
        return

    # format
    weekly['Date']      = weekly['Date'].dt.strftime('%m/%d/%Y')
    weekly              = weekly.rename(columns={'Date': 'Week Ending'})
    weekly['Card']      = weekly['Card'].round(2)
    weekly['Cash']      = weekly['Cash'].round(2)
    weekly['Total Tip'] = weekly['Total Tip'].round(2)

    # append to existing entries
    updated_dfWeekly = pd.concat([dfWeekly, weekly], ignore_index=True)
    set_with_dataframe(weeklySheet, updated_dfWeekly, include_index=False, resize=True)
    print("Weekly updated!")


def monthlyLogs(monthlySheet, dfMonthly, df):
    if not checkNewMonth(datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y")):
        return

    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")

    # If monthly sheet has entries, only calculate from last entry onwards
    if not dfMonthly.empty:
        last_month_ending = pd.to_datetime(dfMonthly.iloc[-1]["Month"], format="%m/%Y")
        temp_df = temp_df[temp_df['Date'] > last_month_ending]

    if temp_df.empty:
        print("No new months to add.")
        return

    monthly = temp_df.groupby(pd.Grouper(key="Date", freq='MS')).agg({
        'Hours'     : 'sum',
        'Card'      : 'sum',
        'Cash'      : 'sum',
        'Total Tip' : 'sum'
    }).reset_index()

    # drop empty months
    monthly = monthly[monthly['Hours'] > 0]

    # drop current incomplete month
    today = pd.Timestamp.now()
    monthly = monthly[monthly['Date'].dt.month != today.month]

    # format
    monthly['Date']      = monthly['Date'].dt.strftime('%m/%Y')
    monthly              = monthly.rename(columns={'Date': 'Month'})
    monthly['Card']      = monthly['Card'].round(2)
    monthly['Cash']      = monthly['Cash'].round(2)
    monthly['Total Tip'] = monthly['Total Tip'].round(2)

    # append to existing entries
    updated_dfMonthly = pd.concat([dfMonthly, monthly], ignore_index=True)
    set_with_dataframe(monthlySheet, updated_dfMonthly, include_index=False, resize=True)
    print("Monthly updated!")


def yearlyLogs(yearlySheet, dfYearly, df):
    if not checkNewYear(datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y")):
        return

    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'], format="%m/%d/%Y")

    # If yearly sheet has entries, only calculate from last entry onwards
    if not dfYearly.empty:
        last_year = pd.to_datetime(dfYearly.iloc[-1]["Year"], format="%Y")
        temp_df = temp_df[temp_df['Date'].dt.year > last_year.year]

    if temp_df.empty:
        print("No new years to add.")
        return

    yearly = temp_df.groupby(pd.Grouper(key="Date", freq='YS')).agg({
        'Hours'     : 'sum',
        'Card'      : 'sum',
        'Cash'      : 'sum',
        'Total Tip' : 'sum'
    }).reset_index()

    # drop empty years
    yearly = yearly[yearly['Hours'] > 0]

    # drop current incomplete year
    today = pd.Timestamp.now()
    yearly = yearly[yearly['Date'].dt.year != today.year]

    # format
    yearly['Date']      = yearly['Date'].dt.strftime('%Y')
    yearly              = yearly.rename(columns={'Date': 'Year'})
    yearly['Card']      = yearly['Card'].round(2)
    yearly['Cash']      = yearly['Cash'].round(2)
    yearly['Total Tip'] = yearly['Total Tip'].round(2)

    # append to existing entries
    updated_dfYearly = pd.concat([dfYearly, yearly], ignore_index=True)
    set_with_dataframe(yearlySheet, updated_dfYearly, include_index=False, resize=True)
    print("Yearly updated!")


def viewLogs(df):
    run = True
    while run:
        print("Which log would you like to view? (Enter number)")
        print("1. First few logs (shows first 10)")
        print("2. Recent few logs (shows recent 10)")
        print("3. Specific date")
        print("4. Show logs in range")
        print("5. Back")

        option = input()

        print("="*100)

        if option == "1":
            print(df.head(10))

        elif option == "2":
            print(df.tail(10))

        elif option == "3":
            print("Enter date of log (MM/DD/YYYY):")
            day = input().strip()
            print(df[df["Date"] == day])

        elif option == "4":
            print("Enter start date (MM/DD/YYYY): ")
            start = input().strip()

            print("Enter end date (MM/DD/YYYY): ")
            end = input().strip()

            # Work on a copy so the original df is never mutated
            temp_df = df.copy()
            temp_df['Date'] = pd.to_datetime(temp_df['Date'], format='%m/%d/%Y')
            startDate = pd.to_datetime(start, format='%m/%d/%Y')
            endDate = pd.to_datetime(end, format='%m/%d/%Y')

            mask = (temp_df['Date'] >= startDate) & (temp_df['Date'] <= endDate)
            filtered_df = temp_df.loc[mask].sort_values("Date").copy()

            filtered_df['Date'] = filtered_df['Date'].dt.strftime('%m/%d/%Y')

            print(filtered_df)

        elif option == "5":
            run = False

        print("="*100)


def addTip(df, worksheet):
    while True:
        while True:
            day = input("Enter Date (MM/DD/YYYY): ").strip()
            try:
                datetime.strptime(day, "%m/%d/%Y")
                break
            except ValueError:
                print("Invalid date. Use MM/DD/YYYY.")

        while True:
            try:
                card = float(input("Enter total card tip: ").strip())
                if card >= 0:
                    break
            except ValueError:
                print("Please enter a valid number for card tip.")

        while True:
            try:
                cash = float(input("Enter total cash tip: ").strip())
                if cash >= 0:
                    break
            except ValueError:
                print("Please enter valid number for cash tip.")

        while True:
            try:
                hours = float(input("Enter hours worked: ").strip())
                if hours > 0:
                    break
            except ValueError:
                print("Please enter valid hours.")

        totalTip = float(cash) + float(card)
        newLog = {
            "Date"      : day,
            "Hours"     : hours,
            "Card"      : card,
            "Cash"      : cash,
            "Total Tip" : totalTip
        }

        while True:
            print("Is the following information correct:")
            done = input(f"{newLog}\nPlease answer y/n: ").strip().lower()
            if done == "y" or done == "n":
                break

        if done == "y":
            break

    new_row_df = pd.DataFrame([newLog])
    updated_df = pd.concat([df, new_row_df], ignore_index=True)

    set_with_dataframe(worksheet, updated_df, include_index=False, resize=True)

    print("="*100)
    print("Log added successfully!")
    print(updated_df.tail(10))
    print("="*100)

    return updated_df


def deleteLog(df, worksheet):
    print("="*100)
    print(f"Recent logs:\n{df.tail(10)}")
    print("="*100)

    while True:
        day = input("Enter date of log to delete (MM/DD/YYYY): ").strip()
        try:
            datetime.strptime(day, "%m/%d/%Y")
            break
        except ValueError:
            print("Invalid date. Please use MM/DD/YYYY.")

    while True:
        confirm = input(f"You want to delete the log for {day}? Please answer y/n: ").strip().lower()
        if confirm == "y" or confirm == "n":
            break

    if confirm == "y":
        try:
            indices_to_drop = df[df['Date'] == day].index
            updated_df = df.drop(indices_to_drop).reset_index(drop=True)
        except Exception as e:
            print(e)
            return df

        set_with_dataframe(worksheet, updated_df, include_index=False, resize=True)

        print("="*100)
        print(f"Successfully deleted log for {day}!")
        print(updated_df.tail(10))
        print("="*100)

        return updated_df

    else:
        print("Deletion cancelled.")
        return df


def addPayDay(df, dfPayDay, payDaySheet):
    while True:
        # get start date
        if dfPayDay.empty:
            while True:
                start = input("Enter start date (MM/DD/YYYY): ").strip()
                try:
                    datetime.strptime(start, "%m/%d/%Y")
                    break
                except ValueError:
                    print("Invalid date. Please use MM/DD/YYYY.")
        else:
            start = dfPayDay.iloc[-1]["End Date"]
            start = (datetime.strptime(start, "%m/%d/%Y") + timedelta(days=1)).strftime("%m/%d/%Y")
        
        # get end date
        while True:
            end = input("Enter end date (MM/DD/YYYY): ").strip()
            try:
                datetime.strptime(end, "%m/%d/%Y")
                break
            except ValueError:
                print("Invalid date. Please use MM/DD/YYYY.")
        
        # get gross pay
        while True:
            try:
                gross = round(float(input("Enter gross pay: ").strip()), 2)
                if gross >= 0:
                    break
            except ValueError:
                print("Invalid gross pay amount. Please enter a valid dollar amount.")
        
        # get tax
        while True:
            try:
                tax = round(float(input("Enter tax: ").strip()), 2)
                if tax >= 0:
                    break
            except ValueError:
                print("Invalid tax amount. Please enter a valid dollar amount.")
    
        while True:
            print("Please confirm the following information:")
            confirm = input(f"Start: {start}, End: {end}, Gross Pay: {gross}, Tax: {tax}\nPlease answer y/n: ")
            
            if confirm == "y" or confirm == "n":
                break
        
        if confirm == "y":
            # Work on a copy so the original df is never mutated
            temp_df = df.copy()
            temp_df['Date'] = pd.to_datetime(temp_df['Date'], format='%m/%d/%Y')
            startDate = pd.to_datetime(start, format='%m/%d/%Y')
            endDate = pd.to_datetime(end, format='%m/%d/%Y')

            mask = (temp_df['Date'] >= startDate) & (temp_df['Date'] <= endDate)
            filtered_df = temp_df.loc[mask].sort_values("Date").copy()

            filtered_df['Date'] = filtered_df['Date'].dt.strftime('%m/%d/%Y')

            # calculations
            totalHours = filtered_df["Hours"].sum()
            workdayPay = round(gross - tax, 2)
            cardTotal = filtered_df["Card"].sum()
            cashTotal = filtered_df["Cash"].sum()
            totalTip = round(cardTotal + cashTotal, 2)
            beforeTax = round(totalTip + gross, 2)
            afterTax = round(beforeTax - tax, 2)
            hourlyAfterTax = round(afterTax/totalHours, 2)
            deviation = round(hourlyAfterTax - MIN_WAGE, 2)

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
                "Hourly Wage (After Taxes)" : hourlyAfterTax
            }

            new_row_df = pd.DataFrame([newLog])
            updated_dfPayDay = pd.concat([dfPayDay, new_row_df], ignore_index=True)

            set_with_dataframe(payDaySheet, updated_dfPayDay, include_index=False, resize=True)

            # display
            print("="*100)
            print("Successfully added!\nSummary: ")
            print(f"Between [{start}-{end}], you worked [{totalHours}hr(s)].")
            print(f"In that time you earned [${afterTax}] after taxes ([${beforeTax}] before taxes).")
            print(f"You earned [${cashTotal}] in cash tips and [${cardTotal}] in card tips")
            print(f"Gross pay was [${gross}] and tax taken was [${tax}], which means you got [${workdayPay}] from Work Pay.")
            print(f"Hourly wage after tax is [${hourlyAfterTax}], which is ", end="")
            if deviation >= 0:
                print(f"${deviation} above the minimum wage (${MIN_WAGE}).\n")
            else:
                print(f"${deviation} below the minimum wage (${MIN_WAGE}).\n")
            print(updated_dfPayDay.tail(10))
            print("="*100)
            break
            
    return updated_dfPayDay

def main():
    # Check Google Calendar for a shift today
    if not is_work_day():
        print("Today is not a workday. Enjoy your day off!")
        sys.exit(0)

    # Connect to Sheets
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open(SPREADSHEET_NAME)

    # "Daily" tab
    worksheet = sh.get_worksheet(0)
    df = get_as_dataframe(worksheet)

    # "Weekly" tab
    weeklySheet = sh.get_worksheet(1)
    dfWeekly = get_as_dataframe(weeklySheet)

    # "Monthly" tab
    monthlySheet = sh.get_worksheet(2)
    dfMonthly = get_as_dataframe(monthlySheet)

    # "Yearly" tab
    yearlySheet = sh.get_worksheet(3)
    dfYearly = get_as_dataframe(yearlySheet)

    # "PayDay" tab
    payDaySheet = sh.get_worksheet(4)
    dfPayDay = get_as_dataframe(payDaySheet)
    
    # update weekly, monthly, and yearly tabs
    weeklyLogs(weeklySheet, dfWeekly, df)
    monthlyLogs(monthlySheet, dfMonthly, df)
    yearlyLogs(yearlySheet, dfYearly, df)

    while True:
        mainScreen()
        option = input()

        if option == "1":
            df = addTip(df, worksheet)

        elif option == "2":
            viewLogs(df)
        
        elif option == "3":
            df = deleteLog(df, worksheet)
        
        elif option == "4":
            dfPayDay = addPayDay(df, dfPayDay, payDaySheet)
        
        elif option == "5":
            break
        
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()