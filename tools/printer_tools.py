import json
import os

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "printers.json"
)


def load_printers():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_printer_status(outlet_id):
    printers = load_printers()

    results = []

    for printer in printers:
        if printer["outlet_id"] == str(outlet_id):
            results.append(printer)

    if not results:
        return {
            "success": False,
            "error": f"No printer found for outlet {outlet_id}"
        }

    return {
        "success": True,
        "printers": results
    }