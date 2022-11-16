import logging
from enum import Enum


class Categories(Enum):
    BUS_STOP = {"highway": "bus_stop", "public_transport": "platform"}
    BUS_STATION = {"amenity": "bus_station", "public_transport": "station"}

    SHOP_BOOKS = {"shop": "books"}
    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}
    SHOP_TRAVEL = {"shop": "travel_agency"}
    SHOP_CAR = {"shop": "car"}

    CAR_REPAIR = {"shop": "car_repair"}
    FUNERAL_DIRECTORS = {"shop": "funeral_directors"}
    DEPARTMENT_STORE = {"shop": "department_store"}

    CAFE = {"amenity": "cafe"}
    COFFEE_SHOP = {"amenity": "cafe", "cuisine": "coffee_shop"}
    PUB = {"amenity": "pub"}
    PHARMACY = {"amenity": "pharmacy"}
    FUEL_STATION = {"amenity": "fuel"}
    BANK = {"amenity": "bank"}
    ATM = {"amenity": "atm"}


def apply_category(category, item):
    if isinstance(category, Enum):
        tags = category.value
    elif isinstance(category, dict):
        tags = category
    else:
        logging.error("Invalid category format")
        return

    if not item.get("extras"):
        item["extras"] = {}
    item["extras"].update(tags)
