import gspread
from google.oauth2.service_account import Credentials

SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Y95NKo7vMZdvcImZiTLEn4Cl6sl8b7CYIiVanhkhh70/edit?gid=0#gid=0'
SERVICE_ACCOUNT_FILE = 'service-account-key.json'
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]

def get_sheet(worksheet_name='Shipments'):
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(SHEET_URL)
        return spreadsheet.worksheet(worksheet_name)
    except Exception as e:
        print(f"[Engine ERROR] get_sheet: {e}")
        return None

def get_shipment_data(shipment_id: str) -> dict | None:
    print(f"[Engine INFO] Fetching all data for shipment: {shipment_id}")
    shipments_sheet = get_sheet('Shipments')
    if not shipments_sheet: return None
    try:
        cell = shipments_sheet.find(shipment_id, in_column=1)
        if cell is None:
            print(f"[Engine INFO] Shipment ID '{shipment_id}' not found.")
            return None
        shipment_details = dict(zip(shipments_sheet.row_values(1), shipments_sheet.row_values(cell.row)))

        # FIX: Only process rows that have a real Shipment_ID value. This kills the "From: ()" bug.
        history_sheet = get_sheet('LocationHistory')
        if history_sheet:
            all_history = history_sheet.get_all_records()
            shipment_history = [row for row in all_history if row.get('Shipment_ID')]
            shipment_details['LocationHistory'] = sorted(shipment_history, key=lambda x: x.get('Timestamp', ''), reverse=True)
        else:
            shipment_details['LocationHistory'] = []

        comm_sheet = get_sheet('CommunicationLog')
        if comm_sheet:
            all_comms = comm_sheet.get_all_records()
            shipment_comms = [row for row in all_comms if row.get('Shipment_ID')]
            shipment_details['CommunicationLog'] = sorted(shipment_comms, key=lambda x: x.get('Timestamp', ''), reverse=True)
        else:
            shipment_details['CommunicationLog'] = []
        
        print("[Engine INFO] Successfully fetched and filtered all related data.")
        return shipment_details
    except Exception as e:
        print(f"[Engine ERROR] get_shipment_data: {e}")
        return None

def update_shipment_location(shipment_id: str, new_city: str, new_lat: str, new_lon: str) -> bool:
    try:
        sheet = get_sheet()
        cell = sheet.find(shipment_id, in_column=1)
        if not sheet or not cell: return False
        sheet.update_cell(cell.row, 3, new_city) # CurrentLocation_City
        sheet.update_cell(cell.row, 4, new_lat)  # CurrentLocation_Lat
        sheet.update_cell(cell.row, 5, new_lon)  # CurrentLocation_Lon
        return True
    except Exception as e: return False

def save_corrected_address(shipment_id: str, corrected_address: str) -> bool:
    try:
        sheet = get_sheet()
        cell = sheet.find(shipment_id, in_column=1)
        if not sheet or not cell: return False
        sheet.update_cell(cell.row, 11, corrected_address) # RecipientAddress
        sheet.update_cell(cell.row, 12, corrected_address) # VerifiedAddress
        return True
    except Exception as e: return False
