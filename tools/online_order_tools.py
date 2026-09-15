import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "online_orders.json"
)


def load_online_orders():
    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_online_order_status(outlet_id):
    online_orders = load_online_orders()

    for outlet in online_orders:
        if outlet["outlet_id"] == str(outlet_id):
            return {
                "success": True,
                "online_order": outlet
            }

    return {
        "success": False,
        "error": f"Online ordering information for outlet {outlet_id} not found"
    }


if __name__ == "__main__":

    print("--------------------------------")
    print("Online Ordering Tools Test")
    print("--------------------------------")

    print("\nTesting O001...")
    result = get_online_order_status("O001")
    print(result)

    print("\nTesting O002...")
    result = get_online_order_status("O002")
    print(result)

    print("\nTesting Unknown Outlet...")
    result = get_online_order_status("O999")
    print(result)