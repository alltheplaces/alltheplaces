from enum import Enum


class Categories(Enum):
    BUS_STOP = {"highway": "bus_stop", "public_transport": "platform"}
    BUS_STATION = {"amenity": "bus_station", "public_transport": "station"}

    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}

    CAFE = {"amenity": "cafe"}
    COFFEE_SHOP = {"amenity": "cafe", "cuisine": "coffee_shop"}
    PHARMACY = {"amenity": "pharmacy"}
    FUEL_STATION = {"amenity": "fuel"}
    BANK = {"amenity": "bank"}
    ATM = {"amenity": "atm"}


def apply_category(category, item):
    if not item.get("extras"):
        item["extras"] = {}
    item["extras"].update(category.value)
