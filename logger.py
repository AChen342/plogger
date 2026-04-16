import gspread
import pandas as pd
from datetime import datetime, timedelta, timezone
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

    today_utc = datetime.now(timezone.utc).date()
    time_min = datetime.combine(today_utc, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    time_max = datetime.combine(today_utc, datetime.max.time(), tzinfo=timezone.utc).isoformat()

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


def aggregateLogs(sheet, dfAgg, df, freq, colName, dateFmt):
    if df.empty:
        print(f"No daily logs found; skipping {colName} update.")
        return

    last_date = datetime.strptime(df['Date'].iloc[-1], "%m/%d/%Y")

    # Pick the right check function based on frequency
    if freq == 'W':
        if not checkNewWeek(last_date):
            return
    elif freq == 'MS':
        if not checkNewMonth(last_date):
            return
    elif freq == 'YS':
        if not checkNewYear(last_date):
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
    aggregated['Date']      = aggregated['Date'].dt.strftime(dateFmt)
    aggregated              = aggregated.rename(columns={'Date': colName})
    aggregated['Card']      = aggregated['Card'].round(2)
    aggregated['Cash']      = aggregated['Cash'].round(2)
    aggregated['Total Tip'] = aggregated['Total Tip'].round(2)

    updated = pd.concat([dfAgg, aggregated], ignore_index=True)
    set_with_dataframe(sheet, updated, include_index=False, resize=True)
    print(f"{colName} updated!")


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

        totalTip = cash + card
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

    if df[df['Date'] == day].empty:
        print(f"No log found for {day}. Deletion cancelled.")
        return df

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
        dfPayDay = dfPayDay.dropna(how='all')

        # get start date
        if dfPayDay.empty or pd.isna(dfPayDay.iloc[-1]["End Date"]):
            while True:
                start = input("Enter start date (MM/DD/YYYY): ").strip()
                try:
                    datetime.strptime(start, "%m/%d/%Y")
                    break
                except ValueError:
                    print("Invalid date. Please use MM/DD/YYYY.")
        else:
            last_end_date = str(dfPayDay.iloc[-1]["End Date"])
            start = (datetime.strptime(last_end_date, "%m/%d/%Y") + timedelta(days=1)).strftime("%m/%d/%Y")        
        
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
            totalHours = round(filtered_df["Hours"].sum(), 2)
            workdayPay = round(gross - tax, 2)
            cardTotal = round(filtered_df["Card"].sum(), 2)
            cashTotal = round(filtered_df["Cash"].sum(), 2)
            totalTip = round(cardTotal + cashTotal, 2)
            beforeTax = round(totalTip + gross, 2)
            afterTax = round(beforeTax - tax, 2)
            hourlyAfterTax = round(afterTax / totalHours, 2)
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
                "Hourly Wage (After Taxes)" : hourlyAfterTax,
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
                print(f"${abs(deviation)} below the minimum wage (${MIN_WAGE}).\n")
            print(updated_dfPayDay.tail(10))
            print("="*100)
            break
            
    return updated_dfPayDay


def mainScreen():
    print("Pay Logger")
    print("What would you like to do? (Enter number)")
    print("1. Add New Log")
    print("2. View Logs")
    print("3. Delete Log")
    print("4. Add Payday")
    print("5. Done")


def main():
    # Check Google Calendar for a shift today
    if not is_work_day():
        print("Today is not a workday. Enjoy your day off!")
        sys.exit(0)

    # Connect to Sheets
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    sh = gc.open(SPREADSHEET_NAME)

    worksheet = sh.get_worksheet(0)
    df = get_as_dataframe(worksheet).dropna(how='all')

    weeklySheet = sh.get_worksheet(1)
    dfWeekly = get_as_dataframe(weeklySheet).dropna(how='all')

    monthlySheet = sh.get_worksheet(2)
    dfMonthly = get_as_dataframe(monthlySheet).dropna(how='all')

    yearlySheet = sh.get_worksheet(3)
    dfYearly = get_as_dataframe(yearlySheet).dropna(how='all')

    payDaySheet = sh.get_worksheet(4)
    dfPayDay = get_as_dataframe(payDaySheet).dropna(how='all')

    aggregateLogs(weeklySheet,  dfWeekly,  df, freq='W',   colName='Week Ending', dateFmt='%m/%d/%Y')
    aggregateLogs(monthlySheet, dfMonthly, df, freq='MS',  colName='Month',       dateFmt='%m/%Y')
    aggregateLogs(yearlySheet,  dfYearly,  df, freq='YS',  colName='Year',        dateFmt='%Y')

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