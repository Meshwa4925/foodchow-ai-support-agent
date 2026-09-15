import json
import os

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "payments.json"
)


def load_payments():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_payment_status(order_id):
    payments = load_payments()

    for payment in payments:
        if payment["order_id"] == str(order_id):
            return {
                "success": True,
                "payment": payment
            }

    return {
        "success": False,
        "error": f"Payment information for order {order_id} not found"
    }