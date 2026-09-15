import json
import os


# =========================================================
# DATA FILE PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

RESTAURANTS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "restaurants.json"
)

OUTLETS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "outlets.json"
)


# =========================================================
# LOAD RESTAURANTS
# =========================================================

def load_restaurants():

    with open(
        RESTAURANTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# LOAD OUTLETS
# =========================================================

def load_outlets():

    with open(
        OUTLETS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# GET RESTAURANT
# =========================================================

def get_restaurant(restaurant_id):

    restaurants = load_restaurants()

    for restaurant in restaurants:

        if restaurant["restaurant_id"] == str(restaurant_id):

            return {
                "success": True,
                "restaurant": restaurant
            }

    return {
        "success": False,
        "error": (
            f"Restaurant {restaurant_id} not found"
        )
    }


# =========================================================
# GET OUTLET
# =========================================================

def get_outlet(outlet_id):

    outlets = load_outlets()

    for outlet in outlets:

        if outlet["outlet_id"] == str(outlet_id):

            return {
                "success": True,
                "outlet": outlet
            }

    return {
        "success": False,
        "error": (
            f"Outlet {outlet_id} not found"
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("--------------------------------")
    print("Restaurant Tools Test")
    print("--------------------------------")

    print("\nRESTAURANT")

    result = get_restaurant("R001")

    print(result)


    print("\nOUTLET")

    result = get_outlet("O001")

    print(result)