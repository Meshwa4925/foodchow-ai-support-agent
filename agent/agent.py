import re
import json

from agent.rag_connector import get_relevant_knowledge
from agent.tool_registry import run_tool
from agent.memory import ConversationMemory
from planner import AgentPlanner


# ============================================================
# GLOBAL OBJECTS
# ============================================================

planner = AgentPlanner()
memory = ConversationMemory()

active_support_ticket = None

active_ticket_context = {
    "issue_type": None,
    "outlet_id": None,
    "order_id": None
}


# ============================================================
# 1. ISSUE CLASSIFICATION
# ============================================================

def classify_issue(message):

    text = message.lower().strip()

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------
    # Payment words have highest priority.
    # Example:
    # "Payment for order 1024 was successful but order is pending"
    # => payment
    # --------------------------------------------------------

    payment_keywords = [
        "payment",
        "paid",
        "money deducted",
        "amount deducted",
        "payment deducted",
        "transaction",
        "refund",
        "payment failed",
        "payment pending",
        "payment successful",
        "payment success",
        "money was deducted",
        "amount was deducted"
    ]

    if any(keyword in text for keyword in payment_keywords):
        return "payment"

    # --------------------------------------------------------
    # ORDER STATUS
    # --------------------------------------------------------
    # Important:
    # "My order 1024 is still pending"
    # => order
    #
    # It should NOT become payment unless payment is mentioned.
    # --------------------------------------------------------

    order_keywords = [
        "order is pending",
        "order still pending",
        "order is still pending",
        "order pending",
        "order stuck",
        "order is stuck",
        "order hasn't arrived",
        "order has not arrived",
        "order not confirmed",
        "order is not confirmed",
        "order failed",
        "order status",
        "order status is pending",
        "my order",
        "order number",
        "order id",
        "order #"
    ]

    if any(keyword in text for keyword in order_keywords):
        return "order"

    # --------------------------------------------------------
    # PRINTER
    # --------------------------------------------------------

    printer_keywords = [
        "printer",
        "printing",
        "print",
        "receipt",
        "printer offline"
    ]

    if any(keyword in text for keyword in printer_keywords):
        return "printer"

    # --------------------------------------------------------
    # KDS
    # --------------------------------------------------------

    kds_keywords = [
        "kds",
        "kitchen display",
        "orders not appearing",
        "order not appearing on kds",
        "order not showing in kitchen",
        "kitchen not receiving"
    ]

    if any(keyword in text for keyword in kds_keywords):
        return "kds"

    # --------------------------------------------------------
    # ONLINE ORDERING
    # --------------------------------------------------------

    online_ordering_keywords = [
        "online order",
        "online ordering",
        "cannot place an order",
        "cannot place online order",
        "can't place an order",
        "can't place online order",
        "unable to place an order",
        "unable to place online order",
        "order placement",
        "order placement is not working",
        "customers cannot place",
        "customers can't place",
        "online ordering is not working",
        "online order is not working",
        "sold-out item",
        "sold out item",
        "showing online",
        "available online",
        "menu changes",
        "menu change",
        "not appearing online",
        "not showing online",
        "menu not updated online",
        "menu update not showing",
        "menu sync"
    ]

    if any(keyword in text for keyword in online_ordering_keywords):
        return "online_ordering"

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    menu_keywords = [
        "menu",
        "menu item",
        "item availability",
        "item unavailable",
        "item not available",
        "sold out"
    ]

    if any(keyword in text for keyword in menu_keywords):
        return "menu"

    # --------------------------------------------------------
    # POS
    # --------------------------------------------------------

    pos_keywords = [
        "pos",
        "billing machine",
        "billing system",
        "gst",
        "pos offline",
        "pos not working"
    ]

    if any(keyword in text for keyword in pos_keywords):
        return "pos"

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    account_keywords = [
        "account",
        "login",
        "password",
        "security",
        "forgot password"
    ]

    if any(keyword in text for keyword in account_keywords):
        return "account"

    return "unknown"


# ============================================================
# 2. EXTRACT ORDER ID
# ============================================================

def extract_order_id(message):

    patterns = [
        r"order\s*(?:id|number|no)?\s*[:#-]?\s*(\d+)",
        r"\border\s+(\d+)\b",
        r"\border#\s*(\d+)",
        r"#(\d+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            message.lower()
        )

        if match:
            return match.group(1)

    return None


# ============================================================
# 3. EXTRACT OUTLET ID
# ============================================================

def extract_outlet_id(message):

    patterns = [
        r"outlet\s*(?:id|number|no)?\s*[:#-]?\s*(O\d+)",
        r"\b(O\d{3})\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            message,
            re.IGNORECASE
        )

        if match:
            return match.group(1).upper()

    return None


# ============================================================
# 4. PLANNER
# ============================================================

def create_agent_plan(issue_type):

    plan_result = planner.create_plan(issue_type)

    print("\n[Agent] Creating execution plan...")

    if not plan_result.get("success"):

        print(
            f"[Agent] No plan available for: {issue_type}"
        )

        return {
            "success": False,
            "issue_type": issue_type,
            "plan": [],
            "error": plan_result.get(
                "error",
                "Unable to create agent plan."
            )
        }

    print(
        f"[Agent] Plan created for: {issue_type}"
    )

    for index, step in enumerate(
        plan_result.get("plan", []),
        start=1
    ):
        print(
            f"[Agent] Plan Step {index}: {step}"
        )

    return plan_result


# ============================================================
# 5. ORDER INVESTIGATION
# ============================================================

def investigate_order(order_id):

    print(
        "\n[Agent] Checking order information..."
    )

    order_result = run_tool(
        "get_order",
        order_id=order_id
    )

    if not order_result.get("success"):

        return {
            "success": False,
            "stage": "order_lookup",
            "error": order_result.get(
                "error",
                "Unable to retrieve order information."
            ),
            "escalation_required": False
        }

    order = order_result.get(
        "order",
        {}
    )

    if not order:

        return {
            "success": False,
            "stage": "order_lookup",
            "error": "Order information was empty.",
            "escalation_required": False
        }

    print(
        f"[Agent] Order found: {order_id}"
    )

    print(
        "\n[Agent] Checking order status..."
    )

    status_result = run_tool(
        "get_order_status",
        order_id=order_id
    )

    if status_result.get("success"):

        order_status = status_result.get(
            "status",
            order.get("status")
        )

    else:

        order_status = order.get(
            "status"
        )

    order_status = str(
        order_status or ""
    ).lower()

    print(
        f"[Agent] Order Status: {order_status}"
    )

    # --------------------------------------------------------
    # Pending order
    # --------------------------------------------------------

    if order_status == "pending":

        diagnosis = (
            f"Order {order_id} is currently pending."
        )

        troubleshooting = [
            "Check the current order processing status.",
            "Verify that the outlet is processing the order.",
            "Check whether the order moves from pending to the next status.",
            "If the order remains pending, escalate it for investigation."
        ]

        resolution = (
            f"Order {order_id} is still pending. "
            "The order should be monitored and escalated "
            "if it does not progress."
        )

        escalation_required = True

    # --------------------------------------------------------
    # Successful order
    # --------------------------------------------------------

    elif order_status in [
        "success",
        "successful",
        "completed",
        "complete"
    ]:

        diagnosis = (
            f"Order {order_id} has been completed successfully."
        )

        troubleshooting = [
            "Verify the order details.",
            "Confirm the order completion status."
        ]

        resolution = (
            f"Order {order_id} is currently completed successfully."
        )

        escalation_required = False

    # --------------------------------------------------------
    # Failed order
    # --------------------------------------------------------

    elif order_status == "failed":

        diagnosis = (
            f"Order {order_id} has failed."
        )

        troubleshooting = [
            "Verify the order details.",
            "Check the reason for order failure.",
            "Retry the order if appropriate."
        ]

        resolution = (
            f"Order {order_id} has failed and requires "
            "further investigation if the customer still needs assistance."
        )

        escalation_required = True

    # --------------------------------------------------------
    # Cancelled order
    # --------------------------------------------------------

    elif order_status == "cancelled":

        diagnosis = (
            f"Order {order_id} has been cancelled."
        )

        troubleshooting = [
            "Verify the cancellation reason.",
            "Check whether a new order is required."
        ]

        resolution = (
            f"Order {order_id} is cancelled."
        )

        escalation_required = False

    # --------------------------------------------------------
    # Unknown status
    # --------------------------------------------------------

    else:

        diagnosis = (
            f"Order {order_id} has status '{order_status}'."
        )

        troubleshooting = [
            "Verify the order status.",
            "Check the order processing system.",
            "Retry or escalate if the issue continues."
        ]

        resolution = (
            "The order status requires further investigation."
        )

        escalation_required = True

    return {
        "success": True,
        "order": order,
        "order_status": order_status,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 6. PAYMENT / ORDER PAYMENT INVESTIGATION
# ============================================================

def investigate_payment(order_id):

    print(
        "\n[Agent] Checking order information..."
    )

    order_result = run_tool(
        "get_order",
        order_id=order_id
    )

    if not order_result.get("success"):

        return {
            "success": False,
            "stage": "order_lookup",
            "error": order_result.get(
                "error",
                "Unable to retrieve order information."
            ),
            "escalation_required": True
        }

    order = order_result.get(
        "order",
        {}
    )

    if not order:

        return {
            "success": False,
            "stage": "order_lookup",
            "error": "Order information was empty.",
            "escalation_required": True
        }

    print(
        f"[Agent] Order Status: "
        f"{order.get('status')}"
    )

    # --------------------------------------------------------
    # Get actual order status tool
    # --------------------------------------------------------

    print(
        "\n[Agent] Checking order status..."
    )

    status_result = run_tool(
        "get_order_status",
        order_id=order_id
    )

    if status_result.get("success"):

        actual_order_status = status_result.get(
            "status",
            order.get("status")
        )

    else:

        actual_order_status = order.get(
            "status"
        )

    # --------------------------------------------------------
    # Check payment
    # --------------------------------------------------------

    print(
        "\n[Agent] Checking payment information..."
    )

    payment_result = run_tool(
        "get_payment_status",
        order_id=order_id
    )

    if not payment_result.get("success"):

        return {
            "success": False,
            "stage": "payment_lookup",
            "error": payment_result.get(
                "error",
                "Unable to retrieve payment information."
            ),
            "order": order,
            "order_status": actual_order_status,
            "escalation_required": True
        }

    payment = payment_result.get(
        "payment",
        {}
    )

    if not payment:

        return {
            "success": False,
            "stage": "payment_lookup",
            "error": "Payment information was empty.",
            "order": order,
            "order_status": actual_order_status,
            "escalation_required": True
        }

    print(
        f"[Agent] Payment Status: "
        f"{payment.get('status')}"
    )

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    order_status = str(
        actual_order_status or ""
    ).lower()

    payment_status = str(
        payment.get("status", "")
    ).lower()

    print(
        "\n[Agent] Comparing order and payment status..."
    )

    # --------------------------------------------------------
    # Payment success + order pending
    # --------------------------------------------------------

    if (
        order_status == "pending"
        and payment_status == "success"
    ):

        diagnosis = (
            "Payment was successful, but the order is still pending. "
            "There is a mismatch between the payment and order status."
        )

        action = (
            "Do not issue an automatic refund. "
            "The payment/order mismatch requires manual investigation "
            "or refund approval."
        )

        troubleshooting = [
            "Verify the payment status.",
            "Verify the order status.",
            "Compare the payment amount with the order amount.",
            "Do not issue an automatic refund.",
            "Escalate the payment/order mismatch for manual investigation."
        ]

        resolution = (
            "The payment was successful but the order remains pending. "
            "The mismatch should be manually investigated."
        )

        escalation_required = True

    # --------------------------------------------------------
    # Payment success + order failed
    # --------------------------------------------------------

    elif (
        order_status == "failed"
        and payment_status == "success"
    ):

        diagnosis = (
            "Payment was successful, but the order has failed."
        )

        action = (
            "Do not execute a refund automatically. "
            "Manual investigation or refund approval is required."
        )

        troubleshooting = [
            "Verify the payment status.",
            "Verify the failed order status.",
            "Do not execute an automatic refund.",
            "Escalate for manual investigation or refund approval."
        ]

        resolution = (
            "The payment succeeded while the order failed. "
            "Manual investigation is required."
        )

        escalation_required = True

    # --------------------------------------------------------
    # Payment failed
    # --------------------------------------------------------

    elif payment_status == "failed":

        diagnosis = (
            "The payment was not successful according to "
            "the backend payment status."
        )

        action = (
            "No automatic refund should be performed because "
            "the backend does not show a successful payment."
        )

        troubleshooting = [
            "Verify the payment method.",
            "Retry the payment if required.",
            "Check whether the order is still pending."
        ]

        resolution = (
            "The backend shows that the payment failed. "
            "No automatic refund is required."
        )

        escalation_required = False

    # --------------------------------------------------------
    # Both successful
    # --------------------------------------------------------

    elif (
        order_status in [
            "success",
            "successful",
            "completed",
            "complete"
        ]
        and payment_status == "success"
    ):

        diagnosis = (
            "The order and payment are both successful."
        )

        action = (
            "No payment mismatch was detected."
        )

        troubleshooting = [
            "Verify the order details.",
            "Verify the payment details."
        ]

        resolution = (
            "The order and payment are both successful."
        )

        escalation_required = False

    # --------------------------------------------------------
    # Other
    # --------------------------------------------------------

    else:

        diagnosis = (
            f"Order status is '{order_status}' and "
            f"payment status is '{payment_status}'."
        )

        action = (
            "The backend information does not show a clear "
            "payment mismatch. Further investigation may be required."
        )

        troubleshooting = [
            "Verify the order status.",
            "Verify the payment status.",
            "Compare the order and payment information."
        ]

        resolution = (
            "The order and payment information requires "
            "further investigation."
        )

        escalation_required = True

    return {
        "success": True,
        "order": order,
        "order_status": order_status,
        "payment": payment,
        "diagnosis": diagnosis,
        "action": action,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 7. COMMON OUTLET VALIDATION
# ============================================================

def get_outlet_and_restaurant(outlet_id):

    print(
        "\n[Agent] Checking outlet information..."
    )

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result.get("success"):

        return {
            "success": False,
            "stage": "outlet_lookup",
            "error": outlet_result.get(
                "error",
                f"Outlet {outlet_id} not found."
            )
        }

    outlet = outlet_result.get(
        "outlet",
        {}
    )

    restaurant_id = outlet.get(
        "restaurant_id"
    )

    print(
        f"[Agent] Outlet found: "
        f"{outlet.get('name')}"
    )

    print(
        "\n[Agent] Checking restaurant information..."
    )

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result.get("success"):

        return {
            "success": False,
            "stage": "restaurant_lookup",
            "error": restaurant_result.get(
                "error",
                "Unable to retrieve restaurant information."
            ),
            "outlet": outlet
        }

    restaurant = restaurant_result.get(
        "restaurant",
        {}
    )

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant
    }


# ============================================================
# 8. POS INVESTIGATION
# ============================================================

def investigate_pos(outlet_id):

    common = get_outlet_and_restaurant(
        outlet_id
    )

    if not common.get("success"):

        return {
            **common,
            "escalation_required": False
        }

    outlet = common["outlet"]
    restaurant = common["restaurant"]

    print(
        "\n[Agent] Checking POS status..."
    )

    pos_result = run_tool(
        "get_pos_status",
        outlet_id=outlet_id
    )

    if not pos_result.get("success"):

        return {
            "success": False,
            "stage": "pos_lookup",
            "error": pos_result.get(
                "error",
                "Unable to retrieve POS information."
            ),
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    pos = pos_result.get(
        "pos",
        {}
    )

    pos_status = str(
        pos.get("status", "")
    ).lower()

    print(
        f"[Agent] POS Status: {pos_status}"
    )

    if pos_status == "offline":

        diagnosis = (
            "The POS system is currently offline."
        )

        troubleshooting = [
            "Check the POS network connection.",
            "Check whether the device is powered on.",
            "Restart the POS application.",
            "Verify the network connection.",
            "Retry synchronization."
        ]

        resolution = (
            "The POS is currently offline. Please check the "
            "network connection and restart the POS application."
        )

        escalation_required = True

    elif pos_status == "online":

        diagnosis = (
            "The POS is online according to the backend status."
        )

        troubleshooting = [
            "Refresh the POS application.",
            "Check the latest synchronization.",
            "Retry the affected POS operation."
        ]

        resolution = (
            "The backend shows that the POS is online, but "
            "the customer is still experiencing an issue. "
            "Further investigation may be required."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The POS status could not be clearly determined."
        )

        troubleshooting = [
            "Check whether the POS device is powered on.",
            "Check the network connection.",
            "Restart the POS application.",
            "Retry the POS operation."
        ]

        resolution = (
            "The backend returned an unexpected POS status, "
            "so the issue should be escalated to support."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant,
        "pos": pos,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 9. PRINTER INVESTIGATION
# ============================================================

def investigate_printer(outlet_id):

    common = get_outlet_and_restaurant(
        outlet_id
    )

    if not common.get("success"):

        return {
            **common,
            "escalation_required": False
        }

    outlet = common["outlet"]
    restaurant = common["restaurant"]

    print(
        "\n[Agent] Checking printer status..."
    )

    printer_result = run_tool(
        "get_printer_status",
        outlet_id=outlet_id
    )

    if not printer_result.get("success"):

        return {
            "success": False,
            "stage": "printer_lookup",
            "error": printer_result.get(
                "error",
                "Unable to retrieve printer information."
            ),
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    printers = printer_result.get(
        "printers",
        []
    )

    if not printers:

        return {
            "success": False,
            "stage": "printer_lookup",
            "error": f"No printer information found for outlet {outlet_id}.",
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    offline_printers = []

    for printer in printers:

        if str(
            printer.get("status", "")
        ).lower() == "offline":

            offline_printers.append(
                printer
            )

    if offline_printers:

        diagnosis = (
            "One or more printers at this outlet are offline."
        )

        troubleshooting = [
            "Check the printer power connection.",
            "Check the WiFi or USB connection.",
            "Restart the printer.",
            "Verify the printer connection from the POS.",
            "Try printing a test receipt."
        ]

        resolution = (
            "The printer appears to be offline. "
            "Please check the printer connection and restart it. "
            "If the issue continues, it should be escalated."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The printer is online according to the backend status."
        )

        troubleshooting = [
            "Check printer configuration.",
            "Check printer paper.",
            "Check whether another print job is stuck.",
            "Restart the printer.",
            "Try a test print."
        ]

        resolution = (
            "The backend shows the printer as online, but the "
            "customer is still experiencing a printing issue. "
            "Further investigation may be required."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant,
        "printers": printers,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 10. KDS INVESTIGATION
# ============================================================

def investigate_kds(outlet_id):

    common = get_outlet_and_restaurant(
        outlet_id
    )

    if not common.get("success"):

        return {
            **common,
            "escalation_required": False
        }

    outlet = common["outlet"]
    restaurant = common["restaurant"]

    print(
        "\n[Agent] Checking KDS status..."
    )

    kds_result = run_tool(
        "get_kds_status",
        outlet_id=outlet_id
    )

    if not kds_result.get("success"):

        return {
            "success": False,
            "stage": "kds_lookup",
            "error": kds_result.get(
                "error",
                "Unable to retrieve KDS information."
            ),
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    kds = kds_result.get(
        "kds",
        {}
    )

    kds_status = str(
        kds.get("status", "")
    ).lower()

    orders_sync = str(
        kds.get("orders_sync", "")
    ).lower()

    print(
        f"[Agent] KDS Status: {kds_status}"
    )

    print(
        f"[Agent] Orders Sync: {orders_sync}"
    )

    if (
        kds_status == "offline"
        or orders_sync == "not_working"
    ):

        diagnosis = (
            "The KDS is offline or order synchronization "
            "is not working."
        )

        troubleshooting = [
            "Check the KDS device connection.",
            "Restart the KDS application.",
            "Verify the outlet ID.",
            "Retry order synchronization.",
            "Check whether the KDS comes online."
        ]

        resolution = (
            "The KDS status indicates a connectivity or "
            "synchronization issue. Please restart the KDS "
            "and retry synchronization."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The KDS is online and order synchronization "
            "appears to be working."
        )

        troubleshooting = [
            "Refresh the KDS application.",
            "Check the latest order synchronization.",
            "Verify that the affected order exists.",
            "Retry synchronization."
        ]

        resolution = (
            "The backend shows that the KDS is working. "
            "If the order is still not appearing, "
            "further investigation may be required."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant,
        "kds": kds,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 11. MENU INVESTIGATION
# ============================================================

def investigate_menu(outlet_id):

    common = get_outlet_and_restaurant(
        outlet_id
    )

    if not common.get("success"):

        return {
            **common,
            "escalation_required": False
        }

    outlet = common["outlet"]
    restaurant = common["restaurant"]

    print(
        "\n[Agent] Checking menu status..."
    )

    menu_result = run_tool(
        "get_menu_status",
        outlet_id=outlet_id
    )

    if not menu_result.get("success"):

        return {
            "success": False,
            "stage": "menu_lookup",
            "error": menu_result.get(
                "error",
                "Unable to retrieve menu information."
            ),
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    menu = menu_result.get(
        "menu",
        {}
    )

    sync_status = str(
        menu.get("sync_status", "")
    ).lower()

    items = menu.get(
        "items",
        []
    )

    unavailable_items = []

    for item in items:

        if item.get("available") is False:

            if item.get("name"):
                unavailable_items.append(
                    item.get("name")
                )

    print(
        f"[Agent] Menu Sync Status: {sync_status}"
    )

    print(
        f"[Agent] Last Menu Update: "
        f"{menu.get('last_updated')}"
    )

    if sync_status == "failed":

        diagnosis = (
            "The menu synchronization has failed. "
            "Recent menu changes may not be appearing "
            "on the online ordering platform."
        )

        troubleshooting = [
            "Retry menu synchronization.",
            "Verify the latest menu update time.",
            "Check item availability.",
            "Refresh the online ordering menu.",
            "Verify whether the changes are now visible online."
        ]

        resolution = (
            "The menu sync has failed. Retry synchronization "
            "and refresh the online ordering menu. "
            "If synchronization continues to fail, escalate."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The menu synchronization is currently successful."
        )

        troubleshooting = [
            "Refresh the online ordering menu.",
            "Verify the latest menu update time.",
            "Check the specific item availability.",
            "Confirm that the latest changes are visible online."
        ]

        resolution = (
            "The menu is currently synchronized. "
            "Refresh the online ordering menu and verify "
            "the latest changes."
        )

        escalation_required = True

    if unavailable_items:

        diagnosis += (
            " Unavailable item(s): "
            + ", ".join(unavailable_items)
            + "."
        )

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant,
        "menu": menu,
        "sync_status": sync_status,
        "last_updated": menu.get("last_updated"),
        "unavailable_items": unavailable_items,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 12. ONLINE ORDERING INVESTIGATION
# ============================================================

def investigate_online_ordering(outlet_id):

    common = get_outlet_and_restaurant(
        outlet_id
    )

    if not common.get("success"):

        return {
            **common,
            "escalation_required": False
        }

    outlet = common["outlet"]
    restaurant = common["restaurant"]

    print(
        "\n[Agent] Checking online ordering status..."
    )

    online_result = run_tool(
        "get_online_order_status",
        outlet_id=outlet_id
    )

    if not online_result.get("success"):

        return {
            "success": False,
            "stage": "online_order_lookup",
            "error": online_result.get(
                "error",
                "Unable to retrieve online ordering information."
            ),
            "outlet": outlet,
            "restaurant": restaurant,
            "escalation_required": True
        }

    online_order = online_result.get(
        "online_order",
        {}
    )

    online_status = str(
        online_order.get("status", "")
    ).lower()

    placement_status = str(
        online_order.get("order_placement", "")
    ).lower()

    print(
        f"[Agent] Online Ordering Status: {online_status}"
    )

    print(
        f"[Agent] Order Placement: {placement_status}"
    )

    if (
        online_status == "online"
        and placement_status == "working"
    ):

        diagnosis = (
            "The online ordering service is online and "
            "order placement is working according to the backend."
        )

        troubleshooting = [
            "Refresh the online ordering application.",
            "Verify menu availability.",
            "Retry placing the order.",
            "Check whether the issue continues."
        ]

        resolution = (
            "The backend shows online ordering is working. "
            "If the customer still cannot place an order, "
            "further investigation may be required."
        )

        escalation_required = True

    elif (
        online_status == "online"
        and placement_status == "not_working"
    ):

        diagnosis = (
            "Online ordering is currently not working "
            "for this outlet."
        )

        troubleshooting = [
            "Check whether the outlet is active.",
            "Verify menu availability.",
            "Check the online ordering service status.",
            "Refresh the online ordering application.",
            "Retry placing an online order."
        ]

        resolution = (
            "The outlet's online order placement service is "
            "currently not working. Refresh the online ordering "
            "system and retry. If the issue continues, escalate."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The online ordering status could not be clearly determined."
        )

        troubleshooting = [
            "Check outlet status.",
            "Check online ordering service status.",
            "Refresh the application.",
            "Retry the order."
        ]

        resolution = (
            "The online ordering backend returned an unclear status. "
            "Further investigation is required."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet,
        "restaurant": restaurant,
        "online_order": online_order,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# 13. SUPPORT TICKET
# ============================================================

def create_escalation_ticket(
    customer_message,
    investigation,
    issue_type=None,
    priority="medium"
):

    global active_support_ticket
    global active_ticket_context

    outlet = investigation.get(
        "outlet"
    ) or {}

    restaurant = investigation.get(
        "restaurant"
    ) or {}

    order = investigation.get(
        "order"
    ) or {}

    restaurant_id = (
        restaurant.get("restaurant_id")
        or order.get("restaurant_id")
        or memory.get_context("restaurant_id")
    )

    outlet_id = (
        outlet.get("outlet_id")
        or order.get("outlet_id")
        or memory.get_context("outlet_id")
    )

    order_id = (
        order.get("order_id")
        or investigation.get("order_id")
        or memory.get_context("order_id")
        or extract_order_id(customer_message)
    )

    current_issue_type = (
        issue_type
        or memory.get_context("issue_type")
    )

    # --------------------------------------------------------
    # Duplicate ticket protection
    # --------------------------------------------------------

    if active_support_ticket:

        same_issue = (
            active_ticket_context.get("issue_type")
            == current_issue_type
            and active_ticket_context.get("outlet_id")
            == outlet_id
            and active_ticket_context.get("order_id")
            == order_id
        )

        if same_issue:

            print(
                "\n[Agent] Existing support ticket found: "
                f"{active_support_ticket.get('ticket_id')}"
            )

            print(
                "[Agent] Skipping duplicate ticket creation."
            )

            return active_support_ticket

    print(
        "\n[Agent] Creating support ticket..."
    )

    ticket_result = run_tool(
        "create_support_ticket",
        customer_issue=customer_message,
        priority=priority,
        order_id=order_id,
        restaurant_id=restaurant_id,
        outlet_id=outlet_id
    )

    if ticket_result.get("success"):

        active_support_ticket = ticket_result

        active_ticket_context = {
            "issue_type": current_issue_type,
            "outlet_id": outlet_id,
            "order_id": order_id
        }

    return ticket_result


# ============================================================
# 14. RUN PLANNED INVESTIGATION
# ============================================================

def execute_agent_plan(
    issue_type,
    customer_message
):

    # --------------------------------------------------------
    # Create planner execution plan
    # --------------------------------------------------------

    plan_result = create_agent_plan(
        issue_type
    )

    if not plan_result.get("success"):

        return {
            "success": False,
            "issue_type": issue_type,
            "error": plan_result.get(
                "error",
                "Unable to create execution plan."
            )
        }

    plan = plan_result.get(
        "plan",
        []
    )

    print(
        "\n[Agent] Executing planned workflow..."
    )

    # ========================================================
    # ORDER
    # ========================================================

    if issue_type == "order":

        order_id = extract_order_id(
            customer_message
        )

        if not order_id:

            return {
                "success": True,
                "issue_type": "order",
                "message": (
                    "Please provide your order ID so I can "
                    "check the order status."
                )
            }
            

        print(
            f"\n[Agent] Order ID detected: {order_id}"
        )

        investigation = investigate_order(
            order_id
        )

        if not investigation.get("success"):

            return {
                "success": False,
                "issue_type": "order",
                "order_id": order_id,
                "error": investigation.get(
                    "error",
                    "Order investigation failed."
                ),
                "investigation": investigation
            }

        support_ticket = None

        if investigation.get(
            "escalation_required"
        ):

            support_ticket = create_escalation_ticket(
                customer_message,
                investigation,
                issue_type="order",
                priority="high"
            )

        return {
            "success": True,
            "issue_type": "order",
            "order_id": order_id,
            "execution_plan": plan,
            "knowledge": None,
            "investigation": investigation,
            "support_ticket": support_ticket
        }

    # ========================================================
    # PAYMENT
    # ========================================================

    if issue_type == "payment":

        order_id = extract_order_id(
            customer_message
        )

        if not order_id:

            return {
                "success": True,
                "issue_type": "payment",
                "message": (
                    "Please provide your order ID so I can "
                    "check the payment status."
                )
            }

        print(
            f"\n[Agent] Order ID detected: {order_id}"
        )

        investigation = investigate_payment(
            order_id
        )

        if not investigation.get("success"):

            return {
                "success": False,
                "issue_type": "payment",
                "order_id": order_id,
                "error": investigation.get(
                    "error",
                    "Payment investigation failed."
                ),
                "investigation": investigation
            }

        support_ticket = None

        if investigation.get(
            "escalation_required"
        ):

            support_ticket = create_escalation_ticket(
                customer_message,
                investigation,
                issue_type="payment",
                priority="high"
            )

        return {
            "success": True,
            "issue_type": "payment",
            "order_id": order_id,
            "execution_plan": plan,
            "investigation": investigation,
            "support_ticket": support_ticket
        }

    # ========================================================
    # OUTLET BASED ISSUES
    # ========================================================

    if issue_type in [
        "pos",
        "printer",
        "kds",
        "menu",
        "online_ordering"
    ]:

        outlet_id = extract_outlet_id(
            customer_message
        )

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "execution_plan": plan,
                "message": (
                    "Please provide your outlet ID so I can "
                    "check the issue."
                )
            }

        print(
            f"\n[Agent] Outlet ID detected: {outlet_id}"
        )

        # ----------------------------------------------------
        # Select investigator
        # ----------------------------------------------------

        investigators = {
            "pos": investigate_pos,
            "printer": investigate_printer,
            "kds": investigate_kds,
            "menu": investigate_menu,
            "online_ordering": investigate_online_ordering
        }

        investigator = investigators[
            issue_type
        ]

        investigation = investigator(
            outlet_id
        )

        # ----------------------------------------------------
        # Invalid outlet / lookup error
        # ----------------------------------------------------

        if not investigation.get("success"):

            # Invalid outlet should NOT automatically create
            # a support ticket.
            return {
                "success": False,
                "issue_type": issue_type,
                "outlet_id": outlet_id,
                "execution_plan": plan,
                "error": investigation.get(
                    "error",
                    "Investigation failed."
                ),
                "investigation": investigation,
                "support_ticket": None
            }

        # ----------------------------------------------------
        # Escalation
        # ----------------------------------------------------

        support_ticket = None

        if investigation.get(
            "escalation_required"
        ):

            priority = "high"

            if issue_type in [
                "menu",
                "online_ordering"
            ]:
                priority = "medium"

            support_ticket = create_escalation_ticket(
                customer_message,
                investigation,
                issue_type=issue_type,
                priority=priority
            )

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "execution_plan": plan,
            "investigation": investigation,
            "support_ticket": support_ticket
        }

    # ========================================================
    # UNKNOWN
    # ========================================================

    return {
        "success": True,
        "issue_type": "unknown",
        "execution_plan": plan,
        "message": (
            "I could not confidently identify the issue. "
            "Please provide more details so I can assist you."
        )
    }


# ============================================================
# 15. MAIN AGENT CORE
# ============================================================

def _run_agent_core(customer_message):

    print(
        "\n========================================"
    )

    print(
        "FOODCHOW AI SUPPORT AGENT"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # STEP 1 - CLASSIFICATION
    # --------------------------------------------------------

    issue_type = classify_issue(
        customer_message
    )

    print(
        f"\n[Agent] Issue Type: {issue_type}"
    )

    # --------------------------------------------------------
    # STEP 2 - KNOWLEDGE BASE
    # --------------------------------------------------------

    print(
        "\n[Agent] Searching Knowledge Base..."
    )

    try:

        knowledge_result = get_relevant_knowledge(
            customer_message,
            top_k=2
        )

    except Exception as exc:

        print(
            f"[Agent] Knowledge retrieval error: {exc}"
        )

        knowledge_result = {
            "success": False,
            "error": str(exc),
            "knowledge": []
        }

    # --------------------------------------------------------
    # STEP 3 - EXECUTE PLANNER
    # --------------------------------------------------------

    result = execute_agent_plan(
        issue_type,
        customer_message
    )

    # --------------------------------------------------------
    # Add knowledge result
    # --------------------------------------------------------

    result["knowledge"] = knowledge_result

    return result


# ============================================================
# 16. CONVERSATION MEMORY
# ============================================================

def run_agent(customer_message):

    global active_support_ticket
    global active_ticket_context

    # --------------------------------------------------------
    # Save customer message
    # --------------------------------------------------------

    memory.add_message(
        "customer",
        customer_message
    )

    # --------------------------------------------------------
    # Detect current information
    # --------------------------------------------------------

    current_issue_type = classify_issue(
        customer_message
    )

    current_outlet_id = extract_outlet_id(
        customer_message
    )

    current_order_id = extract_order_id(
        customer_message
    )

    previous_issue_type = memory.get_context(
        "issue_type"
    )

    # --------------------------------------------------------
    # New issue => reset old ticket
    # --------------------------------------------------------

    if (
        current_issue_type != "unknown"
        and previous_issue_type
        and current_issue_type != previous_issue_type
    ):

        active_support_ticket = None

        active_ticket_context = {
            "issue_type": None,
            "outlet_id": None,
            "order_id": None
        }

    # --------------------------------------------------------
    # Save explicit context
    # --------------------------------------------------------

    if current_issue_type != "unknown":

        memory.set_context(
            "issue_type",
            current_issue_type
        )

    if current_outlet_id:

        memory.set_context(
            "outlet_id",
            current_outlet_id
        )

    if current_order_id:

        memory.set_context(
            "order_id",
            current_order_id
        )

    # --------------------------------------------------------
    # Read remembered context
    # --------------------------------------------------------

    remembered_issue_type = memory.get_context(
        "issue_type"
    )

    remembered_outlet_id = memory.get_context(
        "outlet_id"
    )

    remembered_order_id = memory.get_context(
        "order_id"
    )

    # --------------------------------------------------------
    # Build message using memory
    # --------------------------------------------------------

    agent_message = customer_message

    if (
        current_outlet_id is None
        and remembered_outlet_id
    ):

        agent_message += (
            f" outlet {remembered_outlet_id}"
        )

    if (
        current_order_id is None
        and remembered_order_id
    ):

        agent_message += (
            f" order {remembered_order_id}"
        )

    # --------------------------------------------------------
    # For follow-up questions
    # --------------------------------------------------------

    if (
        current_issue_type == "unknown"
        and remembered_issue_type
    ):

        issue_keywords = {
            "payment": " payment",
            "order": " order",
            "printer": " printer",
            "kds": " kds",
            "online_ordering": " online ordering",
            "menu": " menu",
            "pos": " pos",
            "account": " account"
        }

        agent_message += issue_keywords.get(
            remembered_issue_type,
            ""
        )

    # --------------------------------------------------------
    # Run agent
    # --------------------------------------------------------

    result = _run_agent_core(
        agent_message
    )

    # --------------------------------------------------------
    # Final issue type
    # --------------------------------------------------------

    final_issue_type = result.get(
        "issue_type"
    )

    if (
        final_issue_type
        and final_issue_type != "unknown"
    ):

        memory.set_context(
            "issue_type",
            final_issue_type
        )

    # --------------------------------------------------------
    # Save IDs
    # --------------------------------------------------------

    final_outlet_id = result.get(
        "outlet_id"
    )

    if final_outlet_id:

        memory.set_context(
            "outlet_id",
            final_outlet_id
        )

    final_order_id = result.get(
        "order_id"
    )

    if final_order_id:

        memory.set_context(
            "order_id",
            final_order_id
        )

    # --------------------------------------------------------
    # Save restaurant / outlet from investigation
    # --------------------------------------------------------

    investigation = result.get(
        "investigation"
    )

    if investigation:

        restaurant = investigation.get(
            "restaurant"
        )

        if restaurant:

            restaurant_id = restaurant.get(
                "restaurant_id"
            )

            if restaurant_id:

                memory.set_context(
                    "restaurant_id",
                    restaurant_id
                )

        outlet = investigation.get(
            "outlet"
        )

        if outlet:

            outlet_id = outlet.get(
                "outlet_id"
            )

            if outlet_id:

                memory.set_context(
                    "outlet_id",
                    outlet_id
                )

        order = investigation.get(
            "order"
        )

        if order:

            order_id = order.get(
                "order_id"
            )

            restaurant_id = order.get(
                "restaurant_id"
            )

            outlet_id = order.get(
                "outlet_id"
            )

            if order_id:

                memory.set_context(
                    "order_id",
                    order_id
                )

            if restaurant_id:

                memory.set_context(
                    "restaurant_id",
                    restaurant_id
                )

            if outlet_id:

                memory.set_context(
                    "outlet_id",
                    outlet_id
                )

    # --------------------------------------------------------
    # Agent response
    # --------------------------------------------------------

    if result.get("message"):

        agent_response = result.get(
            "message"
        )

    elif investigation:

        agent_response = investigation.get(
            "resolution",
            investigation.get(
                "diagnosis",
                "Investigation completed."
            )
        )

    else:

        agent_response = (
            "Investigation completed."
        )

    memory.add_message(
        "agent",
        agent_response
    )

    return result


# ============================================================
# 17. TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "FOODCHOW AGENT TEST"
    )

    print(
        "========================================"
    )

    customer_message = input(
        "\nCustomer: "
    )

    result = run_agent(
        customer_message
    )

    print(
        "\n========================================"
    )

    print(
        "FINAL AGENT RESULT"
    )

    print(
        "========================================"
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )

# ============================================================
# 15. CONTROLLED ACTIONS & HUMAN HANDOFF
# ============================================================

def is_positive_response(message):
    """
    Detect a clear customer confirmation that the issue is resolved.

    Important:
    Negative responses must be checked BEFORE positive responses.
    This prevents messages such as:
        "No, it is still not working"
    from being detected as positive because they contain "working".
    """

    text = message.lower().strip()

    # Exact / clear positive responses only
    positive_responses = {
        "yes",
        "yes it is fixed",
        "yes it is working",
        "yes it works",
        "yes fixed",
        "yes resolved",
        "resolved",
        "fixed",
        "problem solved",
        "issue solved",
        "solved",
        "it works",
        "it is working",
        "working now",
        "works now",
        "all good",
        "all okay",
        "everything is fine",
        "fine now",
        "okay now",
        "ok now",
        "done"
    }

    return text in positive_responses


def is_negative_response(message):
    """
    Detect a clear customer confirmation that the issue
    is still unresolved.
    """

    text = message.lower().strip()

    negative_phrases = [
        "no",
        "no it is not fixed",
        "no it is still not working",
        "no still not working",
        "still not working",
        "still doesn't work",
        "still does not work",
        "still not fixed",
        "still unresolved",
        "not resolved",
        "not fixed",
        "problem continues",
        "issue continues",
        "same problem",
        "same issue",
        "failed again",
        "still pending",
        "not working",
        "doesn't work",
        "does not work",
        "not working yet",
        "problem is still there",
        "issue is still there"
    ]

    # Exact response
    if text in negative_phrases:
        return True

    # Important compound checks
    if (
        ("no" in text or "not" in text or "still" in text)
        and (
            "working" in text
            or "fixed" in text
            or "resolved" in text
            or "pending" in text
            or "problem" in text
            or "issue" in text
        )
    ):
        return True

    return False


def build_conversation_summary(
    customer_message,
    result
):
    """
    Build useful context for human support escalation.
    """

    investigation = result.get(
        "investigation"
    ) or {}

    summary = {
        "customer_issue": customer_message,
        "issue_type": result.get(
            "issue_type"
        ),
        "order_id": result.get(
            "order_id"
        ),
        "outlet_id": result.get(
            "outlet_id"
        ),
        "investigation_completed": bool(
            investigation
        ),
        "diagnosis": investigation.get(
            "diagnosis"
        ),
        "resolution": investigation.get(
            "resolution"
        ),
        "troubleshooting_steps": investigation.get(
            "troubleshooting_steps",
            []
        ),
        "escalation_required": investigation.get(
            "escalation_required",
            False
        )
    }

    # Get outlet from investigation if not already available
    outlet = investigation.get(
        "outlet"
    )

    if outlet and not summary.get(
        "outlet_id"
    ):
        summary["outlet_id"] = outlet.get(
            "outlet_id"
        )

    # Get order from investigation if not already available
    order = investigation.get(
        "order"
    )

    if order and not summary.get(
        "order_id"
    ):
        summary["order_id"] = order.get(
            "order_id"
        )

    # Add restaurant information
    restaurant = investigation.get(
        "restaurant"
    )

    if restaurant:
        summary["restaurant_id"] = restaurant.get(
            "restaurant_id"
        )
        summary["restaurant_name"] = restaurant.get(
            "name"
        )

    return summary


# ============================================================
# CUSTOMER RESOLUTION HANDLER
# ============================================================

def handle_customer_resolution(
    customer_message,
    previous_result
):
    """
    Handle customer confirmation after troubleshooting.

    YES:
        Close the conversation.

    NO:
        Escalate to human support.

    Anything unclear:
        Ask again.
    """

    global active_support_ticket
    global active_ticket_context

    # --------------------------------------------------------
    # IMPORTANT:
    # Negative must be checked BEFORE positive.
    # --------------------------------------------------------

    if is_negative_response(
        customer_message
    ):

        print(
            "\n[Agent] Customer confirmed "
            "the issue is NOT resolved."
        )

        investigation = (
            previous_result.get(
                "investigation"
            )
            or {}
        )

        issue_type = previous_result.get(
            "issue_type"
        )

        outlet_id = previous_result.get(
            "outlet_id"
        )

        order_id = previous_result.get(
            "order_id"
        )

        # ----------------------------------------------------
        # Build human handoff summary
        # ----------------------------------------------------

        handoff_summary = build_conversation_summary(
            customer_message,
            previous_result
        )

        # Add previous customer conversation if available
        try:

            if hasattr(
                memory,
                "get_last_message"
            ):

                handoff_summary[
                    "previous_customer_message"
                ] = memory.get_last_message(
                    "customer"
                )

        except Exception:

            pass

        # ----------------------------------------------------
        # Create / reuse support ticket
        # ----------------------------------------------------

        ticket_result = create_escalation_ticket(
            customer_message=customer_message,
            investigation=investigation,
            issue_type=issue_type,
            priority="high"
        )

        if ticket_result.get(
            "success"
        ):

            ticket_result[
                "conversation_summary"
            ] = handoff_summary

            ticket_result[
                "handoff_reason"
            ] = (
                "Customer confirmed that the issue "
                "remains unresolved after troubleshooting."
            )

        return {
            "success": True,
            "status": "escalated",
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "order_id": order_id,
            "message": (
                "The issue is still unresolved, so I have "
                "escalated it to FoodChow support for further "
                "investigation."
            ),
            "support_ticket": ticket_result
        }

    # --------------------------------------------------------
    # Positive confirmation
    # --------------------------------------------------------

    if is_positive_response(
        customer_message
    ):

        return {
            "success": True,
            "status": "resolved",
            "message": (
                "Great. The issue has been confirmed as "
                "resolved. No further action is required."
            ),
            "support_ticket": None
        }

    # --------------------------------------------------------
    # Unclear response
    # --------------------------------------------------------

    return {
        "success": True,
        "status": "awaiting_confirmation",
        "message": (
            "Please confirm whether the issue is resolved. "
            "Reply with 'yes' if it is fixed or 'no' if "
            "the problem is still occurring."
        ),
        "support_ticket": None
    }


# ============================================================
# 16. CONTROLLED REFUND HANDLING
# ============================================================

def handle_refund_request(
    customer_message
):
    """
    Refunds are controlled actions.

    The agent NEVER executes a refund automatically.
    """

    order_id = extract_order_id(
        customer_message
    )

    if not order_id:

        return {
            "success": True,
            "issue_type": "payment",
            "action": "refund_request",
            "status": "awaiting_information",
            "message": (
                "Please provide your order ID so I can "
                "check the order and payment details before "
                "processing a refund request."
            ),
            "support_ticket": None
        }

    print(
        f"\n[Agent] Refund request detected for "
        f"order {order_id}."
    )

    # --------------------------------------------------------
    # Check order
    # --------------------------------------------------------

    investigation = investigate_payment(
        order_id
    )

    if not investigation.get(
        "success"
    ):

        ticket = create_escalation_ticket(
            customer_message=customer_message,
            investigation=investigation,
            issue_type="payment",
            priority="high"
        )

        return {
            "success": False,
            "issue_type": "payment",
            "action": "refund_request",
            "order_id": order_id,
            "message": (
                "I could not complete the payment investigation. "
                "The refund request has been escalated to support."
            ),
            "investigation": investigation,
            "support_ticket": ticket
        }

    order = investigation.get(
        "order",
        {}
    )

    payment = investigation.get(
        "payment",
        {}
    )

    order_status = str(
        order.get(
            "status",
            ""
        )
    ).lower()

    payment_status = str(
        payment.get(
            "status",
            ""
        )
    ).lower()

    # --------------------------------------------------------
    # NEVER automatically refund
    # --------------------------------------------------------

    print(
        "\n[Agent] Refund action requires human approval."
    )

    ticket = create_escalation_ticket(
        customer_message=customer_message,
        investigation=investigation,
        issue_type="payment",
        priority="high"
    )

    return {
        "success": True,
        "issue_type": "payment",
        "action": "refund_request",
        "status": "escalated",
        "order_id": order_id,
        "order_status": order_status,
        "payment_status": payment_status,
        "message": (
            "I have checked the order and payment information. "
            "A refund is a controlled action and cannot be "
            "processed automatically. Your refund request has "
            "been escalated to support for approval."
        ),
        "investigation": investigation,
        "support_ticket": ticket
    }


# ============================================================
# 17. SENSITIVE ISSUE GUARDRAIL
# ============================================================

def is_sensitive_issue(
    customer_message
):
    """
    Identify issues that require human handling.
    """

    text = customer_message.lower()

    sensitive_words = [
        "refund",
        "chargeback",
        "fraud",
        "stolen",
        "hacked",
        "security",
        "delete account",
        "delete restaurant",
        "remove restaurant",
        "account hacked",
        "unauthorized payment",
        "unauthorised payment"
    ]

    return any(
        word in text
        for word in sensitive_words
    )


# ============================================================
# 18. AGENTIC CONVERSATION LOOP
# ============================================================

def run_agent_conversation():
    """
    Multi-turn FoodChow support conversation.

    Flow:

        Customer
            ↓
        Classification
            ↓
        RAG
            ↓
        Planner
            ↓
        Tool Calling
            ↓
        Investigation
            ↓
        Resolution / Troubleshooting
            ↓
        Ask confirmation
            ↓
        YES → Close
        NO  → Human Escalation
    """

    global active_support_ticket
    global active_ticket_context

    print(
        "\n========================================"
    )

    print(
        "FOODCHOW AI SUPPORT AGENT"
    )

    print(
        "MULTI-TURN CONVERSATION MODE"
    )

    print(
        "========================================"
    )

    print(
        "\nType 'exit' to end the conversation."
    )

    previous_result = None

    while True:

        customer_message = input(
            "\nCustomer: "
        ).strip()

        if not customer_message:

            print(
                "Please enter a message."
            )

            continue

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if customer_message.lower() in [
            "exit",
            "quit",
            "close"
        ]:

            print(
                "\n[Agent] Conversation closed."
            )

            break

        # ----------------------------------------------------
        # Sensitive refund request
        # ----------------------------------------------------

        if (
            is_sensitive_issue(
                customer_message
            )
            and "refund" in customer_message.lower()
        ):

            result = handle_refund_request(
                customer_message
            )

            print(
                "\n========================================"
            )

            print(
                "AGENT RESPONSE"
            )

            print(
                "========================================"
            )

            print(
                result.get(
                    "message",
                    "Refund request processed."
                )
            )

            ticket = result.get(
                "support_ticket"
            )

            if (
                ticket
                and ticket.get("success")
            ):

                print(
                    "\nSupport Ticket:",
                    ticket.get(
                        "ticket_id"
                    )
                )

                print(
                    "Refund request has been escalated "
                    "for human approval."
                )

            previous_result = result

            continue

        # ----------------------------------------------------
        # Resolution confirmation
        # ----------------------------------------------------

        if previous_result:

            negative = is_negative_response(
                customer_message
            )

            positive = is_positive_response(
                customer_message
            )

            # Negative has priority over positive
            if negative or positive:

                result = handle_customer_resolution(
                    customer_message,
                    previous_result
                )

                print(
                    "\n========================================"
                )

                print(
                    "AGENT RESPONSE"
                )

                print(
                    "========================================"
                )

                print(
                    result.get(
                        "message",
                        "Request processed."
                    )
                )

                # ------------------------------------------------
                # Resolved
                # ------------------------------------------------

                if result.get(
                    "status"
                ) == "resolved":

                    print(
                        "\n[Agent] Conversation completed."
                    )

                    print(
                        "[Agent] Issue marked as resolved."
                    )

                    break

                # ------------------------------------------------
                # Escalated
                # ------------------------------------------------

                if result.get(
                    "status"
                ) == "escalated":

                    ticket = result.get(
                        "support_ticket"
                    )

                    if (
                        ticket
                        and ticket.get("success")
                    ):

                        print(
                            "\nSupport Ticket:",
                            ticket.get(
                                "ticket_id"
                            )
                        )

                    print(
                        "[Agent] Human support handoff completed."
                    )

                    break

                # ------------------------------------------------
                # Awaiting clarification
                # ------------------------------------------------

                previous_result = result

                continue

        # ----------------------------------------------------
        # Normal agent processing
        # ----------------------------------------------------

        result = run_agent(
            customer_message
        )

        print(
            "\n========================================"
        )

        print(
            "FINAL AGENT RESULT"
        )

        print(
            "========================================"
        )

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        # ----------------------------------------------------
        # Human-friendly response
        # ----------------------------------------------------

        if result.get(
            "message"
        ):

            agent_response = result.get(
                "message"
            )

        else:

            investigation = result.get(
                "investigation"
            )

            if investigation:

                agent_response = investigation.get(
                    "resolution",
                    investigation.get(
                        "diagnosis",
                        "Investigation completed."
                    )
                )

            else:

                agent_response = (
                    "I have completed the investigation."
                )

        print(
            "\n========================================"
        )

        print(
            "AGENT RESPONSE"
        )

        print(
            "========================================"
        )

        print(
            agent_response
        )

        # ----------------------------------------------------
        # If support ticket already created
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # Do NOT ask "Is the issue resolved?" immediately
        # after escalation.
        #
        # The assignment says unresolved cases should be
        # handed to human support.
        # ----------------------------------------------------

        ticket = result.get(
            "support_ticket"
        )

        if (
            ticket
            and ticket.get("success")
        ):

            print(
                "\nSupport Ticket:",
                ticket.get(
                    "ticket_id"
                )
            )

            print(
                "The issue has been escalated to FoodChow support."
            )

            previous_result = result

            # Keep conversation open only if customer wants
            # to provide additional information.
            continue

        # ----------------------------------------------------
        # Investigation completed
        # ----------------------------------------------------

        investigation = result.get(
            "investigation"
        )

        if investigation:

            escalation_required = investigation.get(
                "escalation_required",
                False
            )

            # ------------------------------------------------
            # If escalation is required but ticket was not
            # created, tell customer support is required.
            # ------------------------------------------------

            if escalation_required:

                print(
                    "\n[Agent] Further human support may be "
                    "required."
                )

            # ------------------------------------------------
            # Ask confirmation only when there is no existing
            # support ticket.
            # ------------------------------------------------

            print(
                "\nIs the issue resolved?"
            )

            print(
                "Reply with 'yes' if fixed or "
                "'no' if the issue is still occurring."
            )

        else:

            # Unknown / clarification case
            print(
                "\n[Agent] Please provide more details "
                "if further assistance is required."
            )

        previous_result = result


# ============================================================
# 19. FINAL PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_agent_conversation()