from tools.order_tools import get_order, get_order_status
from tools.payment_tools import get_payment_status
from tools.printer_tools import get_printer_status
from tools.kds_tools import get_kds_status
from tools.menu_tools import get_menu_status
from tools.restaurant_tools import get_restaurant, get_outlet
from tools.pos_tools import get_pos_status
from tools.support_tools import create_support_ticket
from tools.online_order_tools import get_online_order_status

TOOLS = {
    "get_order": get_order,
    "get_order_status": get_order_status,
    "get_payment_status": get_payment_status,
    "get_printer_status": get_printer_status,
    "get_kds_status": get_kds_status,
    "get_menu_status": get_menu_status,
    "get_restaurant": get_restaurant,
    "get_outlet": get_outlet,
    "get_pos_status": get_pos_status,
    "get_online_order_status": get_online_order_status,
    "create_support_ticket": create_support_ticket
}


def run_tool(tool_name, **kwargs):
    if tool_name not in TOOLS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

    try:
        tool_function = TOOLS[tool_name]
        result = tool_function(**kwargs)

        return result

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


def get_available_tools():
    return list(TOOLS.keys())


if __name__ == "__main__":

    print("--------------------------------")
    print("FoodChow Tool Registry Test")
    print("--------------------------------")

    print("\nAvailable Tools:")

    for tool in get_available_tools():
        print("-", tool)

    print("\nTesting get_order...")

    result = run_tool(
        "get_order",
        order_id="1024"
    )

    print("\nResult:")
    print(result)

    print("\nTesting get_menu_status...")

    result = run_tool(
        "get_menu_status",
        outlet_id="O001"
    )

    print("\nResult:")
    print(result)

    print("\nTesting get_restaurant...")

    result = run_tool(
        "get_restaurant",
        restaurant_id="R001"
    )

    print("\nResult:")
    print(result)

    print("\nTesting get_outlet...")

    result = run_tool(
        "get_outlet",
        outlet_id="O001"
    )

    print("\nResult:")
    print(result)

    print("\nTesting get_pos_status...")

    result = run_tool(
        "get_pos_status",
        outlet_id="O001"
    )

    print("\nResult:")
    print(result)