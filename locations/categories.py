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
    CAR_RENTAL = {"amenity": "car_rental"}
    CAR_WASH = {"amenity": "car_wash"}
    PARKING = {"amenity": "parking"}

    BUS_STOP = {"highway": "bus_stop", "public_transport": "platform"}
    BUS_STATION = {"amenity": "bus_station", "public_transport": "station"}
    TRAIN_STATION = {"railway": "station"}

    BOWLING = {"leisure": "bowling_alley"}
    GYM = {"leisure": "fitness_centre"}
    SAUNA = {"leisure": "sauna"}

    HIGHWAY_RESIDENTIAL = {"highway": "residential"}

    CRAFT_CARPENTER = {"craft": "carpenter"}
    CRAFT_CLOCKMAKER = {"craft": "clockmaker"}
    CRAFT_ELECTRONICS_REPAIR = {"craft": "electronics_repair"}
    CRAFT_JEWELLER = {"craft": "jeweller"}
    CRAFT_KEY_CUTTER = {"craft": "key_cutter"}
    CRAFT_LOCKSMITH = {"craft": "locksmith"}
    CRAFT_TAILOR = {"craft": "tailor"}
    CRAFT_SHOEMAKER = {"craft": "shoemaker"}

    LEISURE_PLAYGROUND = {"leisure": "playground"}

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
    SHOP_COMPUTER = {"shop": "computer"}
    SHOP_CONFECTIONERY = {"shop": "confectionery"}
    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_COPYSHOP = {"shop": "copyshop"}
    SHOP_COSMETICS = {"shop": "cosmetics"}
    SHOP_DEPARTMENT_STORE = {"shop": "department_store"}
    SHOP_DOITYOURSELF = {"shop": "doityourself"}
    SHOP_DRY_CLEANING = {"shop": "dry_cleaning"}
    SHOP_ELECTRONICS = {"shop": "electronics"}
    SHOP_FASHION_ACCESSORIES = {"shop": "fashion_accessories"}
    SHOP_FLORIST = {"shop": "florist"}
    SHOP_FUNERAL_DIRECTORS = {"shop": "funeral_directors"}
    SHOP_FURNITURE = {"shop": "furniture"}
    SHOP_FRAME = {"shop": "frame"}
    SHOP_GARDEN_CENTRE = {"shop": "garden_centre"}
    SHOP_GIFT = {"shop": "gift"}
    SHOP_HAIRDRESSER = {"shop": "hairdresser"}
    SHOP_HARDWARE = {"shop": "hardware"}
    SHOP_HEARING_AIDS = {"shop": "hearing_aids"}
    SHOP_JEWELRY = {"shop": "jewelry"}
    SHOP_LAUNDRY = {"shop": "laundry"}
    SHOP_MOBILE_PHONE = {"shop": "mobile_phone"}
    SHOP_MONEY_LENDER = {"shop": "money_lender"}
    SHOP_MOTORCYCLE = {"shop": "motorcycle"}
    SHOP_MOTORCYCLE_REPAIR = {"shop": "motorcycle_repair"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}
    SHOP_OPTICIAN = {"shop": "optician"}
    SHOP_OUTDOOR = {"shop": "outdoor"}
    SHOP_OUTPOST = {"shop": "outpost"}
    SHOP_PAINT = {"shop": "paint"}
    SHOP_PASTRY = {"shop": "pastry"}
    SHOP_PAWNBROKER = {"shop": "pawnbroker"}
    SHOP_PERFUMERY = {"shop": "perfumery"}
    SHOP_PET = {"shop": "pet"}
    SHOP_PHOTO = {"shop": "photo"}
    SHOP_SECOND_HAND = {"shop": "second_hand"}
    SHOP_SHOES = {"shop": "shoes"}
    SHOP_SHOE_REPAIR = {"shop": "shoe_repair"}
    SHOP_SPORTS = {"shop": "sports"}
    SHOP_STATIONERY = {"shop": "stationery"}
    SHOP_STORAGE_RENTAL = {"shop": "storage_rental"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_TEA = {"shop": "tea"}
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
    BAR = {"amenity": "bar"}
    BOAT_FUEL_STATION = {"waterway": "fuel"}
    BUREAU_DE_CHANGE = {"amenity": "bureau_de_change"}
    CAFE = {"amenity": "cafe"}
    CANTEEN = {"amenity": "canteen"}
    CARAVAN_SITE = {"tourism": "caravan_site"}
    CHARGING_STATION = {"amenity": "charging_station"}
    CHILD_CARE = {"amenity": "childcare"}
    CINEMA = {"amenity": "cinema"}
    CLINIC = {"amenity": "clinic", "healthcare": "clinic"}
    CLINIC_URGENT = {"amenity": "clinic", "healthcare": "clinic", "urgent_care": "yes"}
    COFFEE_SHOP = {"amenity": "cafe", "cuisine": "coffee_shop"}
    COMMUNITY_CENTRE = {"amenity": "community_centre"}
    COMPRESSED_AIR = {"amenity": "compressed_air"}
    DENTIST = {"amenity": "dentist", "healthcare": "dentist"}
    DOCTOR_GP = {"amenity": "doctors", "healthcare": "doctor", "healthcare:speciality": "community"}
    FAST_FOOD = {"amenity": "fast_food"}
    FUEL_STATION = {"amenity": "fuel"}
    HOSPITAL = {"amenity": "hospital", "healthcare": "hospital"}
    HOTEL = {"tourism": "hotel"}
    KINDERGARTEN = {"amenity": "kindergarten"}
    LIBRARY = {"amenity": "library"}
    MONEY_TRANSFER = {"amenity": "money_transfer"}
    MUSEUM = {"tourism": "museum"}
    PHARMACY = {"amenity": "pharmacy", "healthcare": "pharmacy"}
    PARCEL_LOCKER = {"amenity": "parcel_locker"}
    POST_BOX = {"amenity": "post_box"}
    POST_DEPOT = {"amenity": "post_depot"}
    POST_OFFICE = {"amenity": "post_office"}
    PRODUCT_PICKUP = {"amenity": "product_pickup"}
    PUB = {"amenity": "pub"}
    TELEPHONE = {"amenity": "telephone"}
    RESTAURANT = {"amenity": "restaurant"}
    VETERINARY = {"amenity": "veterinary"}

    VENDING_MACHINE_BICYCLE_TUBE = {"amenity": "vending_machine", "vending": "bicycle_tube"}
    VENDING_MACHINE_COFFEE = {"amenity": "vending_machine", "vending": "coffee"}

    TRADE_AGRICULTURAL_SUPPLIES = {"trade": "agricultural_supplies"}
    TRADE_BATHROOM = {"trade": "bathroom"}
    TRADE_BUILDING_SUPPLIES = {"trade": "building_supplies"}
    TRADE_ELECTRICAL = {"trade": "electrical"}
    TRADE_FIRE_PROTECTION = {"trade": "fire_protection"}
    TRADE_HVAC = {"trade": "hvac"}
    TRADE_IRRIGATION = {"trade": "irrigation"}
    TRADE_KITCHEN = {"trade": "kitchen"}
    TRADE_LANDSCAPING_SUPPLIES = {"trade": "landscaping_supplies"}
    TRADE_PLUMBING = {"trade": "plumbing"}
    TRADE_SWIMMING_POOL_SUPPLIES = {"trade": "swimming_pool_supplies"}


def apply_category(category, item):
    if isinstance(category, Enum):
        tags = category.value
    elif isinstance(category, dict):
        tags = category
    else:
        raise TypeError("dict or Enum required")

    if not item.get("extras"):
        item["extras"] = {}

    for key, value in tags.items():
        if key in item["extras"].keys():
            existing_values = item["extras"][key].split(";")
            if value in existing_values:
                continue
            existing_values.append(value)
            existing_values.sort()
            item["extras"][key] = ";".join(existing_values)
        else:
            item["extras"][key] = value


top_level_tags = [
    "amenity",
    "club",
    "craft",
    "emergency",
    "healthcare",
    "highway",
    "landuse",
    "leisure",
    "man_made",
    "office",
    "public_transport",
    "shop",
    "tourism",
    "aeroway",
    "railway",
    "waterway",
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
    if len(categories.keys()) > 1 and categories.get("shop") == "yes":
        categories.pop("shop")
    return categories or None


# See: https://wiki.openstreetmap.org/wiki/Key:fuel#Examples
class Fuel(Enum):
    # Diesel
    DIESEL = "fuel:diesel"
    GTL_DIESEL = "fuel:GTL_diesel"
    HGV_DIESEL = "fuel:HGV_diesel"
    BIODIESEL = "fuel:biodiesel"
    UNTAXED_DIESEL = "fuel:taxfree_diesel"
    COLD_WEATHER_DIESEL = "fuel:diesel:class2"
    # Octane levels
    OCTANE_80 = "fuel:octane_80"
    OCTANE_87 = "fuel:octane_87"
    OCTANE_89 = "fuel:octane_89"
    OCTANE_90 = "fuel:octane_90"
    OCTANE_91 = "fuel:octane_91"
    OCTANE_92 = "fuel:octane_92"
    OCTANE_93 = "fuel:octane_93"
    OCTANE_94 = "fuel:octane_94"
    OCTANE_95 = "fuel:octane_95"
    OCTANE_97 = "fuel:octane_97"
    OCTANE_98 = "fuel:octane_98"
    OCTANE_99 = "fuel:octane_99"
    OCTANE_100 = "fuel:octane_100"
    # Formulas
    E5 = "fuel:e5"
    E10 = "fuel:e10"
    E15 = "fuel:e15"
    E20 = "fuel:e20"
    E30 = "fuel:e30"
    E85 = "fuel:e85"
    ETHANOL_FREE = "fuel:ethanol_free"
    BIOGAS = "fuel:biogas"
    LPG = "fuel:lpg"
    CNG = "fuel:cng"
    LNG = "fuel:lng"
    PROPANE = "fuel:propane"
    BUTANE = "fuel:butane"
    LH2 = "fuel:LH2"
    # Additives
    ADBLUE = "fuel:adblue"
    ENGINE_OIL = "fuel:engineoil"
    # Planes
    AV91UL = "fuel:91UL"
    AV100LL = "fuel:100LL"
    AVAUTO_GAS = "fuel:autogas"
    AVJetA1 = "fuel:JetA1"

    HEATING_OIL = "fuel:heating_oil"
    KEROSENE = "fuel:kerosene"


class Extras(Enum):
    AIR_CONDITIONING = "air_conditioning"
    ATM = "atm"
    BABY_CHANGING_TABLE = "changing_table"
    CALLING = "service:phone"
    CAR_WASH = "car_wash"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    COMPRESSED_AIR = "compressed_air"
    COMPUTING = "service:computer"
    COPYING = "service:copy"
    DELIVERY = "delivery"
    DRIVE_THROUGH = "drive_through"
    FAST_FOOD = "fast_food"
    FAXING = "service:fax"
    FEE = "fee"
    INDOOR_SEATING = "indoor_seating"
    OIL_CHANGE = "service:vehicle:oil_change"
    OUTDOOR_SEATING = "outdoor_seating"
    PARCEL_PICKUP = "parcel_pickup"
    PARKING_PARENT = "capacity:parent"
    PARKING_WHEELCHAIR = "capacity:disabled"
    PRINTING = "service:print"
    SELF_CHECKOUT = "self_checkout"
    SCANING = "service:scan"
    SHOWERS = "shower"
    SMOKING_AREA = "smoking=isolated"
    TAKEAWAY = "takeaway"
    TOILETS = "toilets"
    TOILETS_WHEELCHAIR = "toilets:wheelchair"
    TRUCK_WASH = "truck_wash"
    VACUUM_CLEANER = "vacuum_cleaner"
    WHEELCHAIR = "wheelchair"
    WIFI = "internet_access=wlan"


class PaymentMethods(Enum):
    ALIPAY = "payment:alipay"
    AMERICAN_EXPRESS = "payment:american_express"
    AMERICAN_EXPRESS_CONTACTLESS = "payment:american_express_contactless"
    APP = "payment:app"
    APPLE_PAY = "payment:apple_pay"
    BCA_CARD = "payment:bca_card"
    BLIK = "payment:blik"
    CARDS = "payment:cards"
    CASH = "payment:cash"
    CHEQUE = "payment:cheque"
    COINS = "payment:coins"
    CONTACTLESS = "payment:contactless"
    CREDIT_CARDS = "payment:credit_cards"
    D_BARAI = "payment:d_barai"
    DEBIT_CARDS = "payment:debit_cards"
    DINACARD = "payment:dinacard"
    DINERS_CLUB = "payment:diners_club"
    DISCOVER_CARD = "payment:discover_card"
    EDY = "payment:edy"
    GCASH = "payment:gcash"
    GOOGLE_PAY = "payment:google_pay"
    GIROCARD = "payment:girocard"
    HUAWEI_PAY = "payment:huawei_pay"
    ID = "payment:id"
    JCB = "payment:jcb"
    LINE_PAY = "payment:line_pay"
    MAESTRO = "payment:maestro"
    MASTER_CARD = "payment:mastercard"
    MASTER_CARD_CONTACTLESS = "payment:mastercard_contactless"
    MASTER_CARD_DEBIT = "payment:mastercard_debit"
    MERPAY = "payment:merpay"
    MIPAY = "payment:mipay"
    NANACO = "payment:nanaco"
    NOTES = "payment:notes"
    PAYPAY = "payment:paypay"
    QUICPAY = "payment:quicpay"
    RAKUTEN_PAY = "payment:rakuten_pay"
    SAMSUNG_PAY = "payment:samsung_pay"
    SATISPAY = "payment:satispay"
    SBP = "payment:sbp"  # https://www.cbr.ru/eng/psystem/sfp/
    TWINT = "payment:twint"
    UNIONPAY = "payment:unionpay"
    VISA = "payment:visa"
    VISA_CONTACTLESS = "payment:visa_contactless"
    VISA_DEBIT = "payment:visa_debit"
    VISA_ELECTRON = "payment:visa_electron"
    V_PAY = "payment:v_pay"
    WAON = "payment:waon"
    WECHAT = "payment:wechat"


class FuelCards(Enum):
    ALLSTAR = "payment:allstar"  # https://allstarcard.co.uk/
    AVIA = "payment:avia_card"  # https://www.aviaitalia.com/en/avia-card/
    ARIS = "payment:aris"
    AS24 = "payment:as24"  # https://www.as24.com/en/offers/cards
    BP = "payment:bp_card"  # https://www.bp.com/en/global/corporate/products-and-services.html
    DEUTSCHLAND = "fuel:discount:deutschland_card"
    DKV = "payment:dkv"
    E100 = "payment:e100"  # https://e100.eu/en
    EUROWAG = "payment:eurowag"  # https://www.eurowag.com/
    ESSO_NATIONAL = "payment:esso_card"
    EXXONMOBIL_FLEET = "payment:exxonmobil_fleet"
    INA = "payment:ina"  # https://www.ina.hr/en/customers/ina-card/
    LOGPAY = "payment:logpay"  # https://www.logpay.de/
    LUKOIL = "payment:lukoil"  # https://lukoil.ru/Products/business/fuelcards
    LUKOIL_LOYALTY_PROGRAM = "fuel:discount:lukoil"
    MOBIL = "payment:mobilcard"  # https://www.mobil.co.nz/en-nz/mobilcard
    MOLGROUP_CARDS = "payment:molgroup_cards"  # https://www.molgroupcards.com/
    MORGAN_FUELS = "payment:morgan_fuels"
    OMV = "payment:omv"  # https://www.omv.com/en/customers/services/fuel-cards
    PETROL_PLUS_REGION = "payment:petrol_plus_region"  # https://www.petrolplus.ru/
    SHELL = "payment:shell"
    SLOVNAFT = "payment:slovnaft"  # https://slovnaft.sk/en/
    TIFON = "payment:tifon"  # https://tifon.hr/hr/
    TOTAL_CARD = "payment:total_card"  # https://totalcard.patotal.com/
    UTA = "payment:uta"
    ROSNEFT = "payment:rosneft"  # https://www.rn-card.ru/
    ROUTEX = "payment:routex"  # https://routex.com/


class Access(Enum):
    HGV = "hgv"


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
        raise TypeError("string or Enum required")
    if not state and "=" in tag_key:
        return

    if "=" in tag_key:
        tag_key, tag_value = tag_key.split("=")
    else:
        tag_value = "yes" if state else "no"
    apply_category({tag_key: tag_value}, item)


class Clothes(Enum):
    BABY = "babies"
    CHILDREN = "children"
    MATERNITY = "maternity"
    MEN = "men"
    UNDERWEAR = "underwear"
    WOMEN = "women"


def apply_clothes(clothes: [str], item: Feature):
    for c in clothes:
        apply_yes_no(f"clothes:{c}", item, True)
    item["extras"]["clothes"] = ";".join(clothes)
