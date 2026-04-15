import gspread
import pandas as pd
from datetime import datetime
from gspread_dataframe import get_as_dataframe, set_with_dataframe

def mainScreen():
    print("Pay Logger")
    print("What would you like to do? (Enter number)")
    print("1. Add New Log")
    print("2. Update Logs")
    print("3. View Logs")
    print("4. Delete Log")
    print("5. Done")

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
            done = input(f"{newLog}\nPlease answer yes or no: ").strip().lower()
            if done == "yes" or done == "no":
                break
        
        if done == "yes":
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
        confirm = input(f"You want to delete the log for {day}? Please answer yes or no: ").strip().lower()
        if confirm == "yes" or confirm == "no":
            break
    
    if confirm == "yes":
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

def main():    
    # Connect to sheets
    gc = gspread.service_account(filename="credentials.json")

    # Open up spreadsheet
    sh = gc.open("Outback Pay Logging")
    worksheet = sh.get_worksheet(0)

    # Load worksheet as df
    df = get_as_dataframe(worksheet)

    while True:
        mainScreen()
        option = input()
        
        if option == "1":
            df = addTip(df, worksheet)
        elif option == "3":
            viewLogs(df)
        elif option == "4":
            df = deleteLog(df, worksheet)
        elif option == "5":
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()