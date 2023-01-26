import logging
from enum import Enum

from locations.items import Feature


# Where possible the project tries to apply POI categories and attributes according
# to OSM specifications which is in itself something of an art form. Where the attribution
# cannot be done through NSI related pipeline magic then a spider is free to apply any
# categories and attributes itself. This file provides some help in that area. It certainly
# reduces the number of finger fumble mistypes which are the inevitable by-product
# of lots of string bashing. If ever NSI / ATP where to change / augment the category scheme
# then the level of indirection provided here may also be of help!
class Categories(Enum):
    BICYCLE_PARKING = {"amenity": "bicycle_parking"}
    BICYCLE_RENTAL = {"amenity": "bicycle_rental"}

    BUS_STOP = {"highway": "bus_stop", "public_transport": "platform"}
    BUS_STATION = {"amenity": "bus_station", "public_transport": "station"}

    GYM = {"leisure": "fitness_centre"}

    HIGHWAY_RESIDENTIAL = {"highway": "residential"}

    SHOP_ALCOHOL = {"shop": "alcohol"}
    SHOP_BAKERY = {"shop": "bakery"}
    SHOP_BEAUTY = {"shop": "beauty"}
    SHOP_BEVERAGES = {"shop": "beverages"}
    SHOP_BICYCLE = {"shop": "bicycle"}
    SHOP_BOOKMAKER = {"shop": "bookmaker"}
    SHOP_BOOKS = {"shop": "books"}
    SHOP_BUTCHER = {"shop": "butcher"}
    SHOP_CAR = {"shop": "car"}
    SHOP_CAR_PARTS = {"shop": "car_parts"}
    SHOP_CAR_REPAIR = {"shop": "car_repair"}
    SHOP_CHARITY = {"shop": "charity"}
    SHOP_CHEMIST = {"shop": "chemist"}
    SHOP_CLOTHES = {"shop": "clothes"}
    SHOP_CONFECTIONERY = {"shop": "confectionery"}
    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_COSMETICS = {"shop": "cosmetics"}
    SHOP_DEPARTMENT_STORE = {"shop": "department_store"}
    SHOP_DOITYOURSELF = {"shop": "doityourself"}
    SHOP_DRY_CLEANING = {"shop": "dry_cleaning"}
    SHOP_ELECTRONICS = {"shop": "electronics"}
    SHOP_FLORIST = {"shop": "florist"}
    SHOP_FUNERAL_DIRECTORS = {"shop": "funeral_directors"}
    SHOP_FURNITURE = {"shop": "furniture"}
    SHOP_GARDEN_CENTRE = {"shop": "garden_centre"}
    SHOP_GIFT = {"shop": "gift"}
    SHOP_HAIRDRESSER = {"shop": "hairdresser"}
    SHOP_HARDWARE = {"shop": "hardware"}
    SHOP_JEWELRY = {"shop": "jewelry"}
    SHOP_MOBILE_PHONE = {"shop": "mobile_phone"}
    SHOP_MONEY_LENDER = {"shop": "money_lender"}
    SHOP_MOTORCYCLE = {"shop": "motorcycle"}
    SHOP_MOTORCYCLE_REPAIR = {"shop": "motorcycle_repair"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}
    SHOP_OPTICIAN = {"shop": "optician"}
    SHOP_OUTDOOR = {"shop": "outdoor"}
    SHOP_PAINT = {"shop": "paint"}
    SHOP_PASTRY = {"shop": "pastry"}
    SHOP_PAWNBROKER = {"shop": "pawnbroker"}
    SHOP_PERFUMERY = {"shop": "perfumery"}
    SHOP_PET = {"shop": "pet"}
    SHOP_SHOES = {"shop": "shoes"}
    SHOP_SPORTS = {"shop": "sports"}
    SHOP_STATIONERY = {"shop": "stationery"}
    SHOP_STORAGE_RENTAL = {"shop": "storage_rental"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_TELECOMMUNICATION = {"shop": "telecommunication"}
    SHOP_TOYS = {"shop": "toys"}
    SHOP_TRADE = {"shop": "trade"}
    SHOP_TRAVEL_AGENCY = {"shop": "travel_agency"}
    SHOP_VARIETY_STORE = {"shop": "variety_store"}
    SHOP_WATCHES = {"shop": "watches"}
    SHOP_WHOLESALE = {"shop": "wholesale"}

    OFFICE_FINANCIAL = {"office": "financial"}

    ATM = {"amenity": "atm"}
    BANK = {"amenity": "bank"}
    BUREAU_DE_CHANGE = {"amenity": "bureau_de_change"}
    CAFE = {"amenity": "cafe"}
    CHARGING_STATION = {"amenity": "charging_station"}
    CHILD_CARE = {"amenity": "childcare"}
    CLINIC_URGENT = {"amenity": "clinic", "healthcare": "clinic", "urgent_care": "yes"}
    COFFEE_SHOP = {"amenity": "cafe", "cuisine": "coffee_shop"}
    COMPRESSED_AIR = {"amenity": "compressed_air"}
    DENTIST = {"amenity": "dentist", "healthcare": "dentist"}
    DOCTOR_GP = {"amenity": "doctors", "healthcare": "doctor", "healthcare:speciality": "community"}
    FAST_FOOD = {"amenity": "fast_food"}
    FUEL_STATION = {"amenity": "fuel"}
    HOSPITAL = {"amenity": "hospital", "healthcare": "hospital"}
    HOTEL = {"tourism": "hotel"}
    MONEY_TRANSFER = {"amenity": "money_transfer"}
    PHARMACY = {"amenity": "pharmacy", "healthcare": "pharmacy"}
    POST_BOX = {"amenity": "post_box"}
    POST_OFFICE = {"amenity": "post_office"}
    PRODUCT_PICKUP = {"amenity": "product_pickup"}
    PUB = {"amenity": "pub"}
    RESTAURANT = {"amenity": "restaurant"}

    VENDING_MACHINE_BICYCLE_TUBE = {"amenity": "vending_machine", "vending": "bicycle_tube"}


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
    if isinstance(source, Feature):
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


# See: https://wiki.openstreetmap.org/wiki/Key:fuel#Examples
class Fuel(Enum):
    # Diesel
    DIESEL = "fuel:diesel"
    GTL_DIESEL = "fuel:GTL_diesel"
    HGV_DIESEL = "fuel:HGV_diesel"
    BIODIESEL = "fuel:biodiesel"
    UNTAXED_DIESEL = "fuel:untaxed_diesel"
    COLD_WEATHER_DIESEL = "fuel:diesel:class2"
    # Octane levels
    OCTANE_80 = "fuel:octane_80"
    OCTANE_87 = "fuel:octane_87"
    OCTANE_90 = "fuel:octane_90"
    OCTANE_91 = "fuel:octane_91"
    OCTANE_92 = "fuel:octane_92"
    OCTANE_93 = "fuel:octane_93"
    OCTANE_95 = "fuel:octane_95"
    OCTANE_98 = "fuel:octane_98"
    OCTANE_100 = "fuel:octane_100"
    # Formulas
    E5 = "fuel:e5"
    E10 = "fuel:e10"
    E85 = "fuel:e85"
    BIOGAS = "fuel:biogas"
    LPG = "fuel:lpg"
    CNG = "fuel:cng"
    LNG = "fuel:lng"
    PROPANE = "fuel:propane"
    LH2 = "fuel:LH2"
    # Additives
    ADBLUE = "fuel:adblue"
    ENGINE_OIL = "fuel:engineoil"
    # Planes
    AV91UL = "fuel:91UL"
    AV100LL = "fuel:100LL"
    AVAUTO_GAS = "fuel:autogas"
    AVJetA1 = "fuel:JetA1"

    KEROSENE = "fuel:kerosene"


class Extras(Enum):
    ATM = "atm"
    CAR_WASH = "car_wash"
    OIL_CHANGE = "service:vehicle:oil_change"
    TOILETS = "toilets"
    WHEELCHAIR = "wheelchair"
    WIFI = "internet_access=wlan"


class PaymentMethods(Enum):
    AMERICAN_EXPRESS = "payment:american_express"
    APPLE_PAY = "payment:apple_pay"
    CASH = "payment:cash"
    CONTACTLESS = "payment:contactless"
    CREDIT_CARDS = "payment:credit_cards"
    DEBIT_CARDS = "payment:debit_cards"
    GOOGLE_PAY = "payment:google_pay"
    GIROCARD = "payment:girocard"
    MAESTRO = "payment:maestro"
    MASTER_CARD = "payment:mastercard"
    VISA = "payment:visa"
    V_PAY = "payment:v_pay"


def apply_yes_no(attribute, item: Feature, state: bool, apply_positive_only: bool = True):
    """
    Many OSM POI attribute tags values are "yes"/"no". Provide support for setting these from spider code.
    :param attribute: the tag to use for the attribute (str or Enum accepted)
    :param item: the POI instance to update
    :param state: if the attribute to set True or False
    :param apply_positive_only: only add the tag if state is True
    """
    if not state and apply_positive_only:
        return
    if isinstance(attribute, str):
        tag_key = attribute
    elif isinstance(attribute, Enum):
        tag_key = attribute.value
    else:
        raise AttributeError("string or Enum required")
    if "=" in tag_key:
        tag_key, tag_value = tag_key.split("=")
    else:
        tag_value = "yes" if state else "no"
    apply_category({tag_key: tag_value}, item)
