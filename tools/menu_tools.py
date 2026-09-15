import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "menus.json"
)


def load_menus():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_menu_status(outlet_id):
    menus = load_menus()

    for menu in menus:
        if menu["outlet_id"] == str(outlet_id):
            return {
                "success": True,
                "menu": menu
            }

    return {
        "success": False,
        "error": f"Menu for outlet {outlet_id} not found"
    }