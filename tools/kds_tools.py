import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "kds.json"
)


def load_kds():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_kds_status(outlet_id):
    kds_list = load_kds()

    for kds in kds_list:
        if kds["outlet_id"] == str(outlet_id):
            return {
                "success": True,
                "kds": kds
            }

    return {
        "success": False,
        "error": f"KDS for outlet {outlet_id} not found"
    }