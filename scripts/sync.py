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
    log_file = Path(__file__).resolve().parent.parent / "logs" / "sync.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {status}\n")

    def main():
        if not check_connection():
            log_status("FAILURE - No internet connection")
            print("Pas de connexion, synchronisation annulée.")
            return

        try:
            # Scopes pour Google Sheets / Drive
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]

            # Emplacement de la clé de service dans la nouvelle arborescence
            key_file = Path(__file__).resolve().parent.parent / "config" / "faq-service-key.json"
            if not key_file.exists():
                raise FileNotFoundError(f"Clé de service introuvable: {key_file}")

            creds = ServiceAccountCredentials.from_json_keyfile_name(str(key_file), scope)
            client = gspread.authorize(creds)

            sheet = client.open("FAQ ChatBot (réponses)").sheet1
            rows = sheet.get_all_records()

            # Créer le fichier CSV horodaté dans data/pending/
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"new_data_{timestamp}.csv"
            pending_dir = Path(__file__).resolve().parent.parent / "data" / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            filepath = pending_dir / filename

            with filepath.open("w", newline="", encoding="utf-8") as csvfile:
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

            log_status(f"SUCCESS - Fichier créé: {filename}")
            print(f"Synchronisation réussie. Fichier créé: {filepath}")

        except Exception as e:
            log_status(f"FAILURE - {str(e)}")
            print("Erreur pendant la synchro :", e)


    if __name__ == "__main__":
        main()