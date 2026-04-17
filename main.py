import sys
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gui import App

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

def main():
    # Check Google Calendar for a shift today
    if not is_work_day():
        sys.exit(0)
    else:
        App().mainloop()

if __name__=="__main__":
    main()
