import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time
import csv
import os
from datetime import datetime
from pathlib import Path

def check_connection():
    """
    Check if there is an active internet connection by attempting to connect to Google.
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        # Attempt to make a GET request to Google with a 5-second timeout
        requests.get("https://www.google.com", timeout=5)
        return True  # Return True if the request is successful
    except requests.ConnectionError:
        # Return False if a connection error occurs (no internet connection)
        return False
    
import time

def log_status(status):

    """Logs the given status message to a file with a timestamp."""
    log_file = Path(__file__).resolve().parent.parent.parent / "logs" / "sync.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {status}\n")

def get_last_row_index():
    """Lit le dernier index sauvegardé depuis un fichier."""
    state_file = Path(__file__).resolve().parent.parent / "data" / "last_row.txt"
    if state_file.exists():
        return int(state_file.read_text().strip())
    return 0

def save_last_row_index(index):
    """Sauvegarde le dernier index traité."""
    state_file = Path(__file__).resolve().parent.parent / "data" / "last_row.txt"
    state_file.write_text(str(index))

def main():
    if not check_connection():
        log_status("FAILURE - No internet connection")
        print("Pas de connexion, synchronisation annulée.")
        return

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        key_file = Path(__file__).resolve().parent.parent / "config" / "faq-service-key.json"
        creds = ServiceAccountCredentials.from_json_keyfile_name(str(key_file), scope)
        client = gspread.authorize(creds)
        
        
        sheet_id = "1aTLOEaa4ImqiLUr1LS4BFAHvqf1n55bDj-ET2ie2frw"
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.sheet1
        all_rows = sheet.get_all_values()  # toutes les lignes brutes
        headers, data = all_rows[0], all_rows[1:]  # première ligne = entêtes

        last_index = get_last_row_index()
        new_rows = data[last_index:]  # uniquement les nouvelles lignes

        if not new_rows:
            log_status("INFO - Aucune nouvelle donnée")
            print("Aucune nouvelle donnée à synchroniser.")
            return

        # Créer le fichier CSV horodaté
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"new_data_{timestamp}.csv"
        pending_dir = Path(__file__).resolve().parent.parent / "data" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        filepath = pending_dir / filename

        with filepath.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(new_rows)

        # Mettre à jour l’index
        save_last_row_index(last_index + len(new_rows))

        log_status(f"SUCCESS - Fichier créé: {filename}")
        print(f"Synchronisation réussie. Fichier créé: {filepath}")

    except Exception as e:
        log_status(f"FAILURE - {str(e)}")
        print("Erreur pendant la synchro :", e)


if __name__ == "__main__":
        main()