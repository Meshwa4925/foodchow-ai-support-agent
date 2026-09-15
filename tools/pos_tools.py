import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "pos.json"
)


def load_pos():
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_pos_status(outlet_id):
    pos_list = load_pos()

    for pos in pos_list:
        if pos["outlet_id"] == str(outlet_id):
            return {
                "success": True,
                "pos": pos
            }

    return {
        "success": False,
        "error": f"POS for outlet {outlet_id} not found"
    }


if __name__ == "__main__":
    print("--------------------------------")
    print("POS Tools Test")
    print("--------------------------------")

    print("\nTesting O001...")
    result = get_pos_status("O001")
    print(result)

    print("\nTesting O002...")
    result = get_pos_status("O002")
    print(result)

    print("\nTesting Unknown Outlet...")
    result = get_pos_status("O999")
    print(result)