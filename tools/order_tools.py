import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "orders.json"
)


def load_orders():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_order(order_id):
    orders = load_orders()

    for order in orders:
        if order["order_id"] == str(order_id):
            return {
                "success": True,
                "order": order
            }

    return {
        "success": False,
        "error": f"Order {order_id} not found"
    }


def get_order_status(order_id):
    result = get_order(order_id)

    if not result["success"]:
        return result

    return {
        "success": True,
        "order_id": str(order_id),
        "status": result["order"]["status"]
    }