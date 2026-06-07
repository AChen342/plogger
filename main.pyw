import sys
import pandas as pd
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gui import App
import zoneinfo
import logger

CALENDAR_KEYWORD = "Hotschedules"
CREDENTIALS_FILE = "credentials.json"

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

    local_tz = zoneinfo.ZoneInfo("America/New_York")
    today_local = datetime.now(local_tz).date()

    time_min = datetime.combine(today_local, datetime.min.time(), tzinfo=local_tz).isoformat()
    time_max = datetime.combine(today_local, datetime.max.time(), tzinfo=local_tz).isoformat()

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

def already_logged_today(log):
    """Returns True if a tip entry for today already exists in the daily sheet."""
    if log.df.empty:
        return False
    # Normalize sheet dates to date objects to avoid format mismatches
    # (e.g. Sheets may store "5/3/2026" but strftime produces "05/03/2026")
    today = datetime.now().date()
    sheet_dates = pd.to_datetime(log.df["Date"], format="%m/%d/%Y", errors="coerce").dt.date
    return today in sheet_dates.values

def main():
    # Check Google Calendar for a shift today
    if not is_work_day():
        logger.Logger()
        sys.exit(0)

    log = logger.Logger()

    if already_logged_today(log):
        print("Tip already logged for today. Exiting.")
        sys.exit(0)
    
    App(log).mainloop()

if __name__=="__main__":
    main()
