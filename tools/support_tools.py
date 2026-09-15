import uuid


def create_support_ticket(
    customer_issue,
    priority="medium",
    order_id=None,
    restaurant_id=None,
    outlet_id=None
):
    ticket_id = "FC-" + str(uuid.uuid4())[:8].upper()

    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": "created",
        "priority": priority,
        "customer_issue": customer_issue,
        "order_id": order_id,
        "restaurant_id": restaurant_id,
        "outlet_id": outlet_id,
        "message": "Support ticket created successfully."
    }