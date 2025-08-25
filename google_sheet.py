# google_sheet.py
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

def get_worksheet(name: str):
    """Return worksheet object by sheet name"""
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(name)

def read_all_records(sheet_name: str):
    ws = get_worksheet(sheet_name)
    return ws.get_all_records()

def append_row(sheet_name: str, row: list):
    ws = get_worksheet(sheet_name)
    ws.append_row(row, value_input_option="RAW")

def update_cell(sheet_name: str, cell: str, value):
    ws = get_worksheet(sheet_name)
    # gspread expects a 2D array for update with range; wrap value
    ws.update(cell, [[value]])
