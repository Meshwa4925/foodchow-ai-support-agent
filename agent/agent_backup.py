import re
import json

from agent.rag_connector import get_relevant_knowledge
from agent.tool_registry import run_tool
from agent.memory import ConversationMemory

memory = ConversationMemory()


# ============================================================
# ISSUE CLASSIFICATION
# ============================================================

def classify_issue(message):
    text = message.lower()

    # Payment issues
    if any(word in text for word in [
        "payment",
        "paid",
        "deducted",
        "payment pending",
        "payment failed",
        "transaction"
    ]):
        return "payment"

    # Printer issues
    if any(word in text for word in [
        "printer",
        "printing",
        "print",
        "receipt"
    ]):
        return "printer"

    # KDS issues
    if any(word in text for word in [
        "kds",
        "kitchen display",
        "orders not appearing",
        "order not showing in kitchen"
    ]):
        return "kds"

    # Online Ordering issues
    if any(word in text for word in [
        "online order",
        "online ordering",
        "cannot place an order",
        "can't place an order",
        "unable to place an order",
        "order placement",
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
    ]):
        return "online_ordering"

    # Menu issues
    if any(word in text for word in [
        "menu",
        "menu item",
        "item availability"
    ]):
        return "menu"

    # POS issues
    if any(word in text for word in [
        "pos",
        "billing machine",
        "billing system",
        "gst",
        "offline"
    ]):
        return "pos"

    return "unknown"


# ============================================================
# EXTRACT ORDER ID
# ============================================================

def extract_order_id(message):
    patterns = [
        r"order\s*(?:id|number|no)?\s*[:#-]?\s*(\d+)",
        r"\border\s+(\d+)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, message.lower())

        if match:
            return match.group(1)

    return None


# ============================================================
# EXTRACT OUTLET ID
# ============================================================

def extract_outlet_id(message):
    patterns = [
        r"outlet\s*(?:id|number|no)?\s*[:#-]?\s*(O\d+)",
        r"\b(O\d{3})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)

        if match:
            return match.group(1).upper()

    return None


# ============================================================
# PAYMENT INVESTIGATION
# ============================================================

def investigate_payment(order_id):

    order_result = run_tool(
        "get_order",
        order_id=order_id
    )

    if not order_result["success"]:
        return {
            "success": False,
            "error": order_result["error"]
        }

    payment_result = run_tool(
        "get_payment_status",
        order_id=order_id
    )

    if not payment_result["success"]:
        return {
            "success": False,
            "error": payment_result["error"]
        }

    order = order_result["order"]
    payment = payment_result["payment"]

    order_status = order["status"]
    payment_status = payment["status"]

    if payment_status == "success" and order_status == "pending":

        diagnosis = (
            "Payment was successful, but the order is still pending."
        )

        escalation_required = True

    elif payment_status == "failed":

        diagnosis = (
            "The payment transaction failed."
        )

        escalation_required = False

    elif payment_status == "success" and order_status == "confirmed":

        diagnosis = (
            "Payment was successful and the order is confirmed."
        )

        escalation_required = False

    else:

        diagnosis = (
            "The payment and order status combination requires further investigation."
        )

        escalation_required = True

    return {
        "success": True,
        "order": order,
        "payment": payment,
        "diagnosis": diagnosis,
        "escalation_required": escalation_required
    }


# ============================================================
# PRINTER INVESTIGATION
# ============================================================

def investigate_printer(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    printer_result = run_tool(
        "get_printer_status",
        outlet_id=outlet_id
    )

    if not printer_result["success"]:
        return {
            "success": False,
            "error": printer_result["error"]
        }

    printers = printer_result["printers"]

    offline_printers = [
        printer
        for printer in printers
        if printer["status"].lower() == "offline"
    ]

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
            "All configured printers at this outlet are online."
        )

        troubleshooting = [
            "Check printer paper.",
            "Check printer configuration.",
            "Try a test print."
        ]

        resolution = (
            "The printer status appears normal. "
            "Please try a test print and verify the printer configuration."
        )

        escalation_required = False

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "printers": printers,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# KDS INVESTIGATION
# ============================================================

def investigate_kds(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    kds_result = run_tool(
        "get_kds_status",
        outlet_id=outlet_id
    )

    if not kds_result["success"]:
        return {
            "success": False,
            "error": kds_result["error"]
        }

    kds = kds_result["kds"]

    if (
        kds["status"].lower() == "offline"
        or kds["orders_sync"].lower() != "working"
    ):

        diagnosis = (
            "The KDS is offline or order synchronization is not working."
        )

        troubleshooting = [
            "Check the KDS device connection.",
            "Restart the KDS application.",
            "Verify the outlet ID.",
            "Retry order synchronization.",
            "Check whether the KDS comes online."
        ]

        resolution = (
            "The KDS status indicates a connectivity or synchronization issue. "
            "Please restart the KDS and retry synchronization."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The KDS is online and order synchronization is working."
        )

        troubleshooting = [
            "Refresh the KDS application.",
            "Check the latest order synchronization.",
            "Verify that the order exists."
        ]

        resolution = (
            "The KDS appears to be working normally."
        )

        escalation_required = False

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "kds": kds,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# MENU INVESTIGATION
# ============================================================

def investigate_menu(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    menu_result = run_tool(
        "get_menu_status",
        outlet_id=outlet_id
    )

    if not menu_result["success"]:
        return {
            "success": False,
            "error": menu_result["error"]
        }

    menu = menu_result["menu"]

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "menu": menu
    }


# ============================================================
# ONLINE ORDERING - SCENARIO 1
# CANNOT PLACE ONLINE ORDER
# ============================================================

def investigate_online_ordering(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    online_result = run_tool(
        "get_online_order_status",
        outlet_id=outlet_id
    )

    if not online_result["success"]:
        return {
            "success": False,
            "error": online_result["error"]
        }

    online_order = online_result["online_order"]

    if online_order["order_placement"] == "not_working":

        diagnosis = (
            "Online ordering is currently not working for this outlet."
        )

        troubleshooting = [
            "Check whether the outlet is active.",
            "Verify menu availability.",
            "Check the online ordering service status.",
            "Refresh the online ordering application.",
            "Retry placing an online order."
        ]

        resolution = (
            "The outlet's online order placement service is currently not working. "
            "Please refresh the online ordering system and retry. "
            "If the issue continues, it should be escalated."
        )

        escalation_required = True

    elif online_order["order_placement"] == "working":

        diagnosis = (
            "Online order placement is currently working for this outlet."
        )

        troubleshooting = [
            "Refresh the online ordering page.",
            "Verify the menu item availability.",
            "Try placing the order again."
        ]

        resolution = (
            "The online ordering service appears to be working normally."
        )

        escalation_required = False

    else:

        diagnosis = (
            "The online ordering status could not be determined."
        )

        troubleshooting = [
            "Refresh the online ordering system.",
            "Check the outlet configuration.",
            "Retry the order."
        ]

        resolution = (
            "The online ordering status requires further investigation."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "online_order": online_order,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# ONLINE ORDERING - SCENARIO 2
# SOLD-OUT ITEM STILL SHOWING ONLINE
# ============================================================

def investigate_sold_out_item(outlet_id, customer_message):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    menu_result = run_tool(
        "get_menu_status",
        outlet_id=outlet_id
    )

    if not menu_result["success"]:
        return {
            "success": False,
            "error": menu_result["error"]
        }

    menu = menu_result["menu"]

    item_name = None
    item_available = None

    for item in menu["items"]:

        if item["name"].lower() in customer_message.lower():

            item_name = item["name"]
            item_available = item["available"]
            break

    if item_name is None:

        return {
            "success": False,
            "error": (
                "Could not identify the menu item from the customer message."
            ),
            "escalation_required": True
        }

    if item_available is False:

        if menu["sync_status"].lower() == "failed":

            diagnosis = (
                f"The item '{item_name}' is marked as unavailable in the "
                "backend, but menu synchronization has failed. "
                "Therefore, the sold-out status may not be reflected correctly "
                "on the online ordering menu."
            )

            troubleshooting = [
                "Retry menu synchronization.",
                "Verify the item availability in the backend.",
                "Refresh the online ordering menu.",
                "Confirm that the sold-out item is no longer visible online."
            ]

            resolution = (
                f"'{item_name}' is marked as unavailable, but the menu sync "
                "has failed. Retry synchronization and refresh the online menu. "
                "If the item still appears online, escalate to support."
            )

            escalation_required = True

        else:

            diagnosis = (
                f"The item '{item_name}' is marked as sold out in the backend, "
                "but it may still be visible on the online ordering menu."
            )

            troubleshooting = [
                "Refresh the online ordering menu.",
                "Check the latest menu synchronization.",
                "Retry menu synchronization if required.",
                "Verify that the item is no longer available online."
            ]

            resolution = (
                f"'{item_name}' is marked as unavailable in the backend. "
                "Please refresh the online menu and verify the item availability. "
                "If it still appears online, the issue should be escalated."
            )

            escalation_required = True

    else:

        diagnosis = (
            f"The backend currently shows '{item_name}' as available. "
            "The reported sold-out condition could not be confirmed."
        )

        troubleshooting = [
            "Verify the item's current availability.",
            "Check the latest menu update.",
            "Refresh the online ordering menu.",
            "Ask restaurant staff to confirm the item status."
        ]

        resolution = (
            f"The backend currently shows '{item_name}' as available. "
            "Please verify the item's availability and refresh the online menu."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "menu": menu,
        "item_name": item_name,
        "item_available": item_available,
        "sync_status": menu["sync_status"],
        "last_updated": menu["last_updated"],
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# ONLINE ORDERING - SCENARIO 3
# MENU CHANGES NOT APPEARING ONLINE
# ============================================================

def investigate_menu_changes_not_online(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    menu_result = run_tool(
        "get_menu_status",
        outlet_id=outlet_id
    )

    if not menu_result["success"]:
        return {
            "success": False,
            "error": menu_result["error"]
        }

    menu = menu_result["menu"]

    sync_status = menu["sync_status"].lower()

    if sync_status == "failed":

        diagnosis = (
            "The menu synchronization has failed. "
            "Therefore, recent menu changes may not be appearing "
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
            "The menu sync has failed, which can prevent recent changes "
            "from appearing online. Retry the menu synchronization and "
            "refresh the online ordering menu. If synchronization continues "
            "to fail, escalate to support."
        )

        escalation_required = True

    elif sync_status == "synced":

        diagnosis = (
            "The menu synchronization is currently successful. "
            "The online menu should contain the latest synchronized changes."
        )

        troubleshooting = [
            "Refresh the online ordering menu.",
            "Verify the latest menu update time.",
            "Check the specific item availability.",
            "Confirm that the latest changes are visible online."
        ]

        resolution = (
            "The menu is currently synchronized. Please refresh the online "
            "ordering menu and verify the latest changes. If the changes "
            "still do not appear, escalate the issue for further investigation."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The menu synchronization status could not be determined."
        )

        troubleshooting = [
            "Check the menu synchronization status.",
            "Retry menu synchronization.",
            "Refresh the online ordering menu.",
            "Verify the latest menu update."
        ]

        resolution = (
            "The menu synchronization status requires further investigation."
        )

        escalation_required = True

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "menu": menu,
        "sync_status": menu["sync_status"],
        "last_updated": menu["last_updated"],
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# POS INVESTIGATION
# ============================================================

def investigate_pos(outlet_id):

    outlet_result = run_tool(
        "get_outlet",
        outlet_id=outlet_id
    )

    if not outlet_result["success"]:
        return {
            "success": False,
            "error": outlet_result["error"]
        }

    restaurant_id = outlet_result["outlet"]["restaurant_id"]

    restaurant_result = run_tool(
        "get_restaurant",
        restaurant_id=restaurant_id
    )

    if not restaurant_result["success"]:
        return {
            "success": False,
            "error": restaurant_result["error"]
        }

    pos_result = run_tool(
        "get_pos_status",
        outlet_id=outlet_id
    )

    if not pos_result["success"]:
        return {
            "success": False,
            "error": pos_result["error"]
        }

    pos = pos_result["pos"]

    if pos["status"].lower() == "offline":

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
            "The POS is currently offline. Please check the network connection "
            "and restart the POS application."
        )

        escalation_required = True

    else:

        diagnosis = (
            "The POS system is currently online."
        )

        troubleshooting = [
            "Refresh the POS application.",
            "Check the latest synchronization.",
            "Retry the operation."
        ]

        resolution = (
            "The POS appears to be online and operational."
        )

        escalation_required = False

    return {
        "success": True,
        "outlet": outlet_result["outlet"],
        "restaurant": restaurant_result["restaurant"],
        "pos": pos,
        "diagnosis": diagnosis,
        "troubleshooting_steps": troubleshooting,
        "resolution": resolution,
        "escalation_required": escalation_required
    }


# ============================================================
# CREATE ESCALATION TICKET
# ============================================================

def create_escalation_ticket(
    customer_message,
    investigation,
    priority="medium"
):

    outlet = investigation.get("outlet")
    restaurant = investigation.get("restaurant")

    restaurant_id = None
    outlet_id = None

    if restaurant:
        restaurant_id = restaurant.get("restaurant_id")

    if outlet:
        outlet_id = outlet.get("outlet_id")

    return run_tool(
        "create_support_ticket",
        customer_issue=customer_message,
        priority=priority,
        restaurant_id=restaurant_id,
        outlet_id=outlet_id
    )


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(customer_message):

    print("\n========================================")
    print("FOODCHOW AI SUPPORT AGENT")
    print("========================================")

    # --------------------------------------------------------
    # STEP 1 - CLASSIFICATION
    # --------------------------------------------------------

    issue_type = classify_issue(customer_message)

    print(f"\n[Agent] Issue Type: {issue_type}")

    # --------------------------------------------------------
    # STEP 2 - RAG
    # --------------------------------------------------------

    print("\n[Agent] Searching Knowledge Base...")

    knowledge_result = get_relevant_knowledge(
        customer_message,
        top_k=2
    )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    if issue_type == "payment":

        order_id = extract_order_id(customer_message)

        if not order_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your order ID so I can check "
                    "the payment and order status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Order ID detected: {order_id}")

        print("\n[Agent] Checking order information...")

        investigation = investigate_payment(order_id)

        if not investigation["success"]:

            return {
                "success": False,
                "issue_type": issue_type,
                "error": investigation["error"],
                "knowledge": knowledge_result
            }

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="high"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "order_id": order_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # ONLINE ORDERING - SCENARIO 2
    # SOLD OUT ITEM
    # --------------------------------------------------------

    if (
        issue_type == "online_ordering"
        and (
            "sold out" in customer_message.lower()
            or "sold-out" in customer_message.lower()
            or "showing online" in customer_message.lower()
            or "available online" in customer_message.lower()
        )
    ):

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "the menu and item availability."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking outlet information...")

        print("\n[Agent] Checking menu status...")

        investigation = investigate_sold_out_item(
            outlet_id,
            customer_message
        )

        if not investigation["success"]:

            print("\n[Agent] Investigation failed.")

            ticket = run_tool(
                "create_support_ticket",
                customer_issue=customer_message,
                priority="medium",
                outlet_id=outlet_id
            )

            return {
                "success": False,
                "issue_type": issue_type,
                "outlet_id": outlet_id,
                "knowledge": knowledge_result,
                "investigation": investigation,
                "support_ticket": ticket
            }

        print(
            f"[Agent] Menu Sync Status: "
            f"{investigation['sync_status']}"
        )

        print(
            f"[Agent] Last Menu Update: "
            f"{investigation['last_updated']}"
        )

        print(
            f"[Agent] Item detected: "
            f"{investigation['item_name']}"
        )

        print(
            f"[Agent] Item Availability: "
            f"{investigation['item_available']}"
        )

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="medium"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # ONLINE ORDERING - SCENARIO 3
    # MENU CHANGES NOT APPEARING ONLINE
    # --------------------------------------------------------

    if (
        issue_type == "online_ordering"
        and (
            "menu changes" in customer_message.lower()
            or "menu change" in customer_message.lower()
            or "not appearing online" in customer_message.lower()
            or "not showing online" in customer_message.lower()
            or "menu not updated online" in customer_message.lower()
            or "menu update not showing" in customer_message.lower()
            or "menu sync" in customer_message.lower()
        )
    ):

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "your menu synchronization status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking outlet information...")

        print("\n[Agent] Checking restaurant information...")

        print("\n[Agent] Checking menu status...")

        investigation = investigate_menu_changes_not_online(
            outlet_id
        )

        if not investigation["success"]:

            print("\n[Agent] Investigation failed.")

            ticket = run_tool(
                "create_support_ticket",
                customer_issue=customer_message,
                priority="medium",
                outlet_id=outlet_id
            )

            return {
                "success": False,
                "issue_type": issue_type,
                "outlet_id": outlet_id,
                "knowledge": knowledge_result,
                "investigation": investigation,
                "support_ticket": ticket
            }

        print(
            f"[Agent] Menu Sync Status: "
            f"{investigation['sync_status']}"
        )

        print(
            f"[Agent] Last Menu Update: "
            f"{investigation['last_updated']}"
        )

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="medium"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # ONLINE ORDERING - SCENARIO 1
    # CANNOT PLACE ORDER
    # --------------------------------------------------------

    if issue_type == "online_ordering":

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "the online ordering status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking outlet information...")

        print("\n[Agent] Checking restaurant information...")

        print("\n[Agent] Checking online ordering status...")

        investigation = investigate_online_ordering(
            outlet_id
        )

        if not investigation["success"]:

            print("\n[Agent] Investigation failed.")

            ticket = run_tool(
                "create_support_ticket",
                customer_issue=customer_message,
                priority="high",
                outlet_id=outlet_id
            )

            return {
                "success": False,
                "issue_type": issue_type,
                "outlet_id": outlet_id,
                "knowledge": knowledge_result,
                "investigation": investigation,
                "support_ticket": ticket
            }

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="high"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # PRINTER
    # --------------------------------------------------------

    if issue_type == "printer":

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "the printer status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking printer status...")

        investigation = investigate_printer(
            outlet_id
        )

        if not investigation["success"]:

            return {
                "success": False,
                "issue_type": issue_type,
                "error": investigation["error"],
                "knowledge": knowledge_result
            }

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="high"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # KDS
    # --------------------------------------------------------

    if issue_type == "kds":

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "the KDS status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking KDS status...")

        investigation = investigate_kds(
            outlet_id
        )

        if not investigation["success"]:

            return {
                "success": False,
                "issue_type": issue_type,
                "error": investigation["error"],
                "knowledge": knowledge_result
            }

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="high"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # POS
    # --------------------------------------------------------

    if issue_type == "pos":

        outlet_id = extract_outlet_id(customer_message)

        if not outlet_id:

            return {
                "success": True,
                "issue_type": issue_type,
                "message": (
                    "Please provide your outlet ID so I can check "
                    "the POS status."
                ),
                "knowledge": knowledge_result
            }

        print(f"[Agent] Outlet ID detected: {outlet_id}")

        print("\n[Agent] Checking POS status...")

        investigation = investigate_pos(
            outlet_id
        )

        if not investigation["success"]:

            return {
                "success": False,
                "issue_type": issue_type,
                "error": investigation["error"],
                "knowledge": knowledge_result
            }

        if investigation["escalation_required"]:

            print("\n[Agent] Creating support ticket...")

            ticket = create_escalation_ticket(
                customer_message,
                investigation,
                priority="high"
            )

        else:

            ticket = None

        return {
            "success": True,
            "issue_type": issue_type,
            "outlet_id": outlet_id,
            "knowledge": knowledge_result,
            "investigation": investigation,
            "support_ticket": ticket
        }

    # --------------------------------------------------------
    # UNKNOWN ISSUE
    # --------------------------------------------------------

    print("\n[Agent] Issue could not be confidently classified.")

    ticket = run_tool(
        "create_support_ticket",
        customer_issue=customer_message,
        priority="medium"
    )

    return {
        "success": True,
        "issue_type": "unknown",
        "knowledge": knowledge_result,
        "message": (
            "I could not confidently identify the issue. "
            "I have created a support ticket for further assistance."
        ),
        "support_ticket": ticket
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("FOODCHOW AGENT TEST")
    print("========================================")

    customer_message = (
        "Menu changes are not appearing online at outlet O002"
    )

    result = run_agent(customer_message)

    print("\n========================================")
    print("FINAL AGENT RESULT")
    print("========================================")

    print(result)