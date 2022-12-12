import logging
from enum import Enum

from locations.items import GeojsonPointItem


class Categories(Enum):
    BUS_STOP = {"highway": "bus_stop", "public_transport": "platform"}
    BUS_STATION = {"amenity": "bus_station", "public_transport": "station"}

    SHOP_CLOTHES = {"shop": "clothes"}
    SHOP_BOOKS = {"shop": "books"}
    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}
    SHOP_OPTICIAN = {"shop": "optician"}
    SHOP_TRAVEL = {"shop": "travel_agency"}
    SHOP_CAR = {"shop": "car"}
    SHOP_WHOLESALE = {"shop": "wholesale"}
    SHOP_CHARITY = {"shop": "charity"}

    CAR_REPAIR = {"shop": "car_repair"}
    FUNERAL_DIRECTORS = {"shop": "funeral_directors"}
    DEPARTMENT_STORE = {"shop": "department_store"}

    CAFE = {"amenity": "cafe"}
    COFFEE_SHOP = {"amenity": "cafe", "cuisine": "coffee_shop"}
    DENTIST = {"amenity": "dentist"}
    CLINIC_URGENT = {"amenity": "clinic", "healthcare": "clinic", "urgent_care": "yes"}
    DOCTOR_GP = {
        "amenity": "doctors",
        "healthcare": "doctor",
        "healthcare:speciality": "community",
    }
    HOSPITAL = {"amenity": "hospital"}
    PUB = {"amenity": "pub"}
    PHARMACY = {"amenity": "pharmacy"}
    FUEL_STATION = {"amenity": "fuel"}
    BANK = {"amenity": "bank"}
    ATM = {"amenity": "atm"}
    POST_OFFICE = {"amenity": "post_office"}
    POST_BOX = {"amenity": "post_box"}


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


top_level_tags = [
    "amenity",
    "emergency",
    "healthcare",
    "highway",
    "leisure",
    "office",
    "public_transport",
    "shop",
    "tourism",
]


def get_category_tags(source) -> {}:
    if isinstance(source, GeojsonPointItem):
        tags = source.get("extras", {})
    elif isinstance(source, Enum):
        tags = source.value
    elif isinstance(source, dict):
        tags = source

    categories = {}
    for top_level_tag in top_level_tags:
        if v := tags.get(top_level_tag):
            categories[top_level_tag] = v
    return categories or None
