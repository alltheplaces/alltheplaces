from enum import Enum

from locations.dict_parser import DictParser
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

    ENFORCEMENT_AVERAGE_SPEED = {"enforcement": "average_speed"}
    ENFORCEMENT_MAXIMUM_SPEED = {"enforcement": "maxspeed"}
    ENFORCEMENT_TRAFFIC_SIGNALS = {"enforcement": "traffic_signals"}

    CRAFT_CARPENTER = {"craft": "carpenter"}
    CRAFT_CLOCKMAKER = {"craft": "clockmaker"}
    CRAFT_ELECTRONICS_REPAIR = {"craft": "electronics_repair"}
    CRAFT_JEWELLER = {"craft": "jeweller"}
    CRAFT_KEY_CUTTER = {"craft": "key_cutter"}
    CRAFT_LOCKSMITH = {"craft": "locksmith"}
    CRAFT_TAILOR = {"craft": "tailor"}
    CRAFT_SHOEMAKER = {"craft": "shoemaker"}

    DARK_STORE_GROCERY = {"dark_store": "grocery"}

    INDUSTRIAL_WAREHOUSE = {"industrial": "warehouse"}

    LEISURE_PLAYGROUND = {"leisure": "playground"}
    LEISURE_RESORT = {"leisure": "resort"}

    SHOP_AGRARIAN = {"shop": "agrarian"}
    SHOP_ALCOHOL = {"shop": "alcohol"}
    SHOP_ANIME = {"shop": "anime"}
    SHOP_APPLIANCE = {"shop": "appliance"}
    SHOP_ART = {"shop": "art"}
    SHOP_BABY_GOODS = {"shop": "baby_goods"}
    SHOP_BAG = {"shop": "bag"}
    SHOP_BAKERY = {"shop": "bakery"}
    SHOP_BATHROOM_FURNISHING = {"shop": "bathroom_furnishing"}
    SHOP_BEAUTY = {"shop": "beauty"}
    SHOP_BED = {"shop": "bed"}
    SHOP_BEVERAGES = {"shop": "beverages"}
    SHOP_BICYCLE = {"shop": "bicycle"}
    SHOP_BOOKMAKER = {"shop": "bookmaker"}
    SHOP_BOOKS = {"shop": "books"}
    SHOP_BOAT = {"shop": "boat"}
    SHOP_BUTCHER = {"shop": "butcher"}
    SHOP_CAMERA = {"shop": "camera"}
    SHOP_CANDLES = {"shop": "candles"}
    SHOP_CANNABIS = {"shop": "cannabis"}
    SHOP_CAR = {"shop": "car"}
    SHOP_CAR_PARTS = {"shop": "car_parts"}
    SHOP_CAR_REPAIR = {"shop": "car_repair"}
    SHOP_CARAVAN = {"shop": "caravan"}
    SHOP_CARPET = {"shop": "carpet"}
    SHOP_CATALOGUE = {"shop": "catalogue"}
    SHOP_CHARITY = {"shop": "charity"}
    SHOP_CHEESE = {"shop": "cheese"}
    SHOP_CHEMIST = {"shop": "chemist"}
    SHOP_CHOCOLATE = {"shop": "chocolate"}
    SHOP_CLOTHES = {"shop": "clothes"}
    SHOP_COFFEE = {"shop": "coffee"}
    SHOP_COMPUTER = {"shop": "computer"}
    SHOP_CONFECTIONERY = {"shop": "confectionery"}
    SHOP_CONVENIENCE = {"shop": "convenience"}
    SHOP_COPYSHOP = {"shop": "copyshop"}
    SHOP_COSMETICS = {"shop": "cosmetics"}
    SHOP_COUNTRY_STORE = {"shop": "country_store"}
    SHOP_CRAFT = {"shop": "craft"}
    SHOP_CURTAIN = {"shop": "curtain"}
    SHOP_DAIRY = {"shop": "dairy"}
    SHOP_DELI = {"shop": "deli"}
    SHOP_DEPARTMENT_STORE = {"shop": "department_store"}
    SHOP_DOITYOURSELF = {"shop": "doityourself"}
    SHOP_DOORS = {"shop": "doors"}
    SHOP_DRY_CLEANING = {"shop": "dry_cleaning"}
    SHOP_ELECTRICAL = {"shop": "electrical"}
    SHOP_ELECTRONICS = {"shop": "electronics"}
    SHOP_EROTIC = {"shop": "erotic"}
    SHOP_FASHION_ACCESSORIES = {"shop": "fashion_accessories"}
    SHOP_FISHING = {"shop": "fishing"}
    SHOP_FLOORING = {"shop": "flooring"}
    SHOP_FLORIST = {"shop": "florist"}
    SHOP_FRAME = {"shop": "frame"}
    SHOP_FROZEN_FOOD = {"shop": "frozen_food"}
    SHOP_FUNERAL_DIRECTORS = {"shop": "funeral_directors"}
    SHOP_FURNITURE = {"shop": "furniture"}
    SHOP_GAMES = {"shop": "games"}
    SHOP_GARDEN_CENTRE = {"shop": "garden_centre"}
    SHOP_GAS = {"shop": "gas"}
    SHOP_GENERAL = {"shop": "general"}
    SHOP_GIFT = {"shop": "gift"}
    SHOP_GOLD_BUYER = {"shop": "gold_buyer"}
    SHOP_GREENGROCER = {"shop": "greengrocer"}
    SHOP_HAIRDRESSER = {"shop": "hairdresser"}
    SHOP_HAIRDRESSER_SUPPLY = {"shop": "hairdresser_supply"}
    SHOP_HARDWARE = {"shop": "hardware"}
    SHOP_HEALTH_FOOD = {"shop": "health_food"}
    SHOP_HEARING_AIDS = {"shop": "hearing_aids"}
    SHOP_HERBALIST = {"shop": "herbalist"}
    SHOP_HIFI = {"shop": "hifi"}
    SHOP_HOUSEHOLD_LINEN = {"shop": "household_linen"}
    SHOP_HOUSEWARE = {"shop": "houseware"}
    SHOP_INTERIOR_DECORATION = {"shop": "interior_decoration"}
    SHOP_JEWELRY = {"shop": "jewelry"}
    SHOP_KIOSK = {"shop": "kiosk"}
    SHOP_KITCHEN = {"shop": "kitchen"}
    SHOP_LAUNDRY = {"shop": "laundry"}
    SHOP_LEATHER = {"shop": "leather"}
    SHOP_LIGHTING = {"shop": "lighting"}
    SHOP_LOCKSMITH = {"shop": "locksmith"}
    SHOP_LOTTERY = {"shop": "lottery"}
    SHOP_MALL = {"shop": "mall"}
    SHOP_MASSAGE = {"shop": "massage"}
    SHOP_MEDICAL_SUPPLY = {"shop": "medical_supply"}
    SHOP_MOBILE_PHONE = {"shop": "mobile_phone"}
    SHOP_MODEL = {"shop": "model"}
    SHOP_MONEY_LENDER = {"shop": "money_lender"}
    SHOP_MOTORCYCLE = {"shop": "motorcycle"}
    SHOP_MOTORCYCLE_REPAIR = {"shop": "motorcycle_repair"}
    SHOP_MUSIC = {"shop": "music"}
    SHOP_MUSICAL_INSTRUMENT = {"shop": "musical_instrument"}
    SHOP_NEWSAGENT = {"shop": "newsagent"}
    SHOP_NUTRITION_SUPPLEMENTS = {"shop": "nutrition_supplements"}
    SHOP_NUTS = {"shop": "nuts"}
    SHOP_OPTICIAN = {"shop": "optician"}
    SHOP_ORTHOPEDICS = {"shop": "orthopedics"}
    SHOP_OUTDOOR = {"shop": "outdoor"}
    SHOP_OUTPOST = {"shop": "outpost"}
    SHOP_PAINT = {"shop": "paint"}
    SHOP_PARTY = {"shop": "party"}
    SHOP_PASTRY = {"shop": "pastry"}
    SHOP_PAWNBROKER = {"shop": "pawnbroker"}
    SHOP_PERFUMERY = {"shop": "perfumery"}
    SHOP_PEST_CONTROL = {"shop": "pest_control"}
    SHOP_PET = {"shop": "pet"}
    SHOP_PHOTO = {"shop": "photo"}
    SHOP_PLANT_HIRE = {"shop": "plant_hire"}
    SHOP_POTTERY = {"shop": "pottery"}
    SHOP_PRINTER_INK = {"shop": "printer_ink"}
    SHOP_PYROTECHNICS = {"shop": "pyrotechnics"}
    SHOP_RENTAL = {"shop": "rental"}
    SHOP_SEAFOOD = {"shop": "seafood"}
    SHOP_SECOND_HAND = {"shop": "second_hand"}
    SHOP_SHOES = {"shop": "shoes"}
    SHOP_SHOE_REPAIR = {"shop": "shoe_repair"}
    SHOP_SPICES = {"shop": "spices"}
    SHOP_SPORTS = {"shop": "sports"}
    SHOP_STATIONERY = {"shop": "stationery"}
    SHOP_STORAGE_RENTAL = {"shop": "storage_rental"}
    SHOP_SUPERMARKET = {"shop": "supermarket"}
    SHOP_SWIMMING_POOL = {"shop": "swimming_pool"}
    SHOP_TAILOR = {"shop": "tailor"}
    SHOP_TATTOO = {"shop": "tattoo"}
    SHOP_TEA = {"shop": "tea"}
    SHOP_TELECOMMUNICATION = {"shop": "telecommunication"}
    SHOP_TICKET = {"shop": "ticket"}
    SHOP_TILES = {"shop": "tiles"}
    SHOP_TOBACCO = {"shop": "tobacco"}
    SHOP_TOOL_HIRE = {"shop": "tool_hire"}
    SHOP_TOYS = {"shop": "toys"}
    SHOP_TRADE = {"shop": "trade"}
    SHOP_TRAVEL_AGENCY = {"shop": "travel_agency"}
    SHOP_TRUCK = {"shop": "truck"}
    SHOP_TRUCK_REPAIR = {"shop": "truck_repair"}
    SHOP_TYRES = {"shop": "tyres"}
    SHOP_VACUUM_CLEANER = {"shop": "vacuum_cleaner"}
    SHOP_VARIETY_STORE = {"shop": "variety_store"}
    SHOP_VIDEO_GAMES = {"shop": "video_games"}
    SHOP_VIDEO = {"shop": "video"}
    SHOP_WATCHES = {"shop": "watches"}
    SHOP_WHOLESALE = {"shop": "wholesale"}
    SHOP_WINDOW_BLIND = {"shop": "window_blind"}
    SHOP_WINE = {"shop": "wine"}

    OFFICE_COMPANY = {"office": "company"}
    OFFICE_COURIER = {"office": "courier"}
    OFFICE_ENGINEER = {"office": "engineer"}
    OFFICE_ESTATE_AGENT = {"office": "estate_agent"}
    OFFICE_FINANCIAL = {"office": "financial"}
    OFFICE_IT = {"office": "it"}

    TOURISM_APARTMENT = {"tourism": "apartment"}
    TOURISM_CAMP_SITE = {"tourism": "camp_site"}
    TOURISM_CHALET = {"tourism": "chalet"}
    TOURISM_HOSTEL = {"tourism": "hostel"}
    TOURISM_WILDERNESS_HUT = {"tourism": "wilderness_hut"}

    ALTERNATIVE_MEDICINE = {"healthcare": "alternative"}
    AMBULANCE_STATION = {"emergency": "ambulance_station"}
    ATM = {"amenity": "atm"}
    AUDIOLOGIST = {"healthcare": "audiologist"}
    BANK = {"amenity": "bank"}
    BAR = {"amenity": "bar"}
    BENCH = {"amenity": "bench"}
    BIRTHING_CENTRE = {"healthcare": "birthing_centre"}
    BLOOD_BANK = {"healthcare": "blood_bank"}
    BLOOD_DONATION = {"healthcare": "blood_donation"}
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
    DEFIBRILLATOR = {"emergency": "defibrillator"}
    DIALYSIS = {"healthcare": "dialysis"}
    DOCTOR_GP = {"amenity": "doctors", "healthcare": "doctor", "healthcare:speciality": "community"}
    EMERGENCY_WARD = {"emergency": "emergency_ward_entrance"}
    FAST_FOOD = {"amenity": "fast_food"}
    FIRE_STATION = {"amenity": "fire_station"}
    FUEL_STATION = {"amenity": "fuel"}
    HOSPITAL = {"amenity": "hospital", "healthcare": "hospital"}
    HOSPICE = {"healthcare": "hospice"}
    HOTEL = {"tourism": "hotel"}
    KINDERGARTEN = {"amenity": "kindergarten"}
    LIBRARY = {"amenity": "library"}
    MEDICAL_LABORATORY = {"healthcare": "laboratory"}
    MONEY_TRANSFER = {"amenity": "money_transfer"}
    MOTEL = {"tourism": "motel"}
    MUSEUM = {"tourism": "museum"}
    NIGHTCLUB = {"amenity": "nightclub"}
    NURSING_HOME = {"amenity": "social_facility", "social_facility": "nursing_home", "social_facility:for": "senior"}
    NUTRITIONIST = {"healthcare": "nutrition_counselling"}
    OPTOMETRIST = {"healthcare": "optometrist"}
    PHARMACY = {"amenity": "pharmacy", "healthcare": "pharmacy"}
    PARCEL_LOCKER = {"amenity": "parcel_locker"}
    PHYSIOTHERAPIST = {"healthcare": "physiotherapist"}
    PODIATRIST = {"healthcare": "podiatrist"}
    POST_BOX = {"amenity": "post_box"}
    POST_DEPOT = {"amenity": "post_depot"}
    POST_OFFICE = {"amenity": "post_office"}
    PREP_SCHOOL = {"amenity": "prep_school"}
    PRODUCT_PICKUP = {"amenity": "product_pickup"}
    PSYCHOTHERAPIST = {"healthcare": "psychotherapist"}
    PUB = {"amenity": "pub"}
    PUBLIC_BOOKCASE = {"amenity": "public_bookcase"}
    REHABILITATION = {"healthcare": "rehabilitation"}
    RESCUE_BUOY = {"emergency": "rescue_buoy"}
    SAMPLE_COLLECTION = {"healthcare": "sample_collection"}
    SPEECH_THERAPIST = {"healthcare": "speech_therapist"}
    TELEPHONE = {"amenity": "telephone"}
    RESTAURANT = {"amenity": "restaurant"}
    VACCINATION_CENTRE = {"healthcare": "vaccination_centre"}
    VETERINARY = {"amenity": "veterinary"}
    WATER_RESCUE = {"emergency": "water_rescue"}
    ANIMAL_BOARDING = {"amenity": "animal_boarding"}

    DATA_CENTRE = {"telecom": "data_center"}

    VENDING_MACHINE_BICYCLE_TUBE = {"amenity": "vending_machine", "vending": "bicycle_tube"}
    VENDING_MACHINE_COFFEE = {"amenity": "vending_machine", "vending": "coffee"}
    VENDING_MACHINE_FOOD = {"amenity": "vending_machine", "vending": "food"}

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

    ANTENNA = {"man_made": "antenna"}

    SURVEILLANCE_CAMERA = {"man_made": "surveillance", "surveillance:type": "camera"}


def apply_category(category, item: Feature):
    """
    Apply categories to a Feature, where categories can be supplied
    as a single Enum, or dictionary of key-value strings. If a
    value for the category key is already defined, the new value for
    the category key is appended rather than overwritten. When
    appending the new value, the list of values is sorted and each
    value is separated with a semi-colon.
    :param category: Either an Enum member representing a single
                     category to add, or a dictionary of key-value
                     strings representing multiple categories to add.
    :param item: Feature to which categories should be added to.
    """
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
    "dark_store",
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
    "telecom",
]


def get_category_tags(source: Feature | Enum | dict) -> dict:
    """
    Retreive OpenStreetMap top level tags from a Feature, Enum or
    dict. All top level tags can exist on their own and do not
    require the presence of other tags. If the Feature, Enum or dict
    supplied contains other tags, these are ignored.
    :param source: Either a Feature, Enum or dictionary which
                   contains categories (such as "amenity": "pub").
    :return: dictionary of OpenStreetMap top level tags, if any
             exist within the supplied source object. Other tags
             which are not top-level are ignored.
    """
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


class Fuel(Enum):
    """
    Fuel categories per https://wiki.openstreetmap.org/wiki/Key:fuel
    """

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
    OCTANE_88 = "fuel:octane_88"
    OCTANE_89 = "fuel:octane_89"
    OCTANE_90 = "fuel:octane_90"
    OCTANE_91 = "fuel:octane_91"
    OCTANE_92 = "fuel:octane_92"
    OCTANE_93 = "fuel:octane_93"
    OCTANE_94 = "fuel:octane_94"
    OCTANE_95 = "fuel:octane_95"
    OCTANE_96 = "fuel:octane_96"
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
    E88 = "fuel:e88"
    ETHANOL_FREE = "fuel:ethanol_free"
    METHANOL = "fuel:methanol"
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

    ALKYLATE = "fuel:alkylate"  # https://de.wikipedia.org/wiki/Alkylatbenzin

    HEATING_OIL = "fuel:heating_oil"
    KEROSENE = "fuel:kerosene"

    ELECTRIC = "fuel:electric"  # Electric vehicle charger


class Extras(Enum):
    AIR_CONDITIONING = "air_conditioning"
    ATM = "atm"
    BABY_CHANGING_TABLE = "changing_table"
    BACKUP_GENERATOR = "backup_generator"
    BARBEQUES = "bbq"
    BREAKFAST = "breakfast"
    CALLING = "service:phone"
    CAR_WASH = "car_wash"
    CARAVAN_SITES = "caravans"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    COMPRESSED_AIR = "compressed_air"
    COMPUTING = "service:computer"
    COPYING = "service:copy"
    DELIVERY = "delivery"
    DRINKING_WATER = "drinking_water"
    DRIVE_THROUGH = "drive_through"
    FAST_FOOD = "fast_food"
    FAXING = "service:fax"
    FEE = "fee"
    HALAL = "diet:halal"
    ICE_CREAM = "ice_cream"
    INDOOR_SEATING = "indoor_seating"
    KOSHER = "diet:kosher"
    MOTOR_VEHICLES = "motor_vehicle"
    OIL_CHANGE = "service:vehicle:oil_change"
    OUTDOOR_SEATING = "outdoor_seating"
    PARCEL_PICKUP = "parcel_pickup"
    PARKING_PARENT = "capacity:parent"
    PARKING_WHEELCHAIR = "capacity:disabled"
    PETS_ALLOWED = "pets_allowed"
    PICNIC_TABLES = "picnic_table"
    PRINTING = "service:print"
    SELF_CHECKOUT = "self_checkout"
    SCANING = "service:scan"
    SHOWERS = "shower"
    SMOKING_AREA = "smoking=isolated"
    SWIMMING_POOL = "swimming_pool"
    TAKEAWAY = "takeaway"
    TENT_SITES = "tents"
    TOILETS = "toilets"
    TOILETS_WHEELCHAIR = "toilets:wheelchair"
    TRUCK_WASH = "truck_wash"
    VACUUM_CLEANER = "vacuum_cleaner"
    WHEELCHAIR = "wheelchair"
    WIFI = "internet_access=wlan"


class PaymentMethods(Enum):
    """
    Payment method categories per https://wiki.openstreetmap.org/wiki/Key:payment:*
    """

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
    MIR = "payment:mir"
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
    """
    Fuel card categories per https://wiki.openstreetmap.org/wiki/Key:payment:*#Fuel_cards
    """

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
    """
    Access categories per https://wiki.openstreetmap.org/wiki/Key:access
    """

    HGV = "hgv"
    MOTOR_CAR = "motorcar"


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
    """
    Clothing categories per https://wiki.openstreetmap.org/wiki/Key:clothes
    """

    BABY = "babies"
    CHILDREN = "children"
    MATERNITY = "maternity"
    MEN = "men"
    UNDERWEAR = "underwear"
    WOMEN = "women"


def apply_clothes(clothes: [Clothes], item: Feature):
    """
    Apply clothing categories to a Feature. If the Feature
    already has clothing categories defined, this function will
    append to the list of clothing categories rather than
    overwriting existing clothing categories. When appending,
    the list of clothing categories is sorted and then each value
    is separated with a semi-colon.
    :param clothes: array of Clothes Enum members
    :param item: Feature which should have clothing categories applied.
    """
    for c in clothes:
        apply_yes_no(f"clothes:{c.value}", item, True)
        apply_category({"clothes": c.value}, item)


class HealthcareSpecialities(Enum):
    """
    Healthcare speciality categories per https://wiki.openstreetmap.org/wiki/Key:healthcare:speciality
    """

    ABORTION = "abortion"
    ACUPUNCTURE = "acupuncture"
    ALLERGOLOGY = "allergoloy"
    ANAESTHETICS = "anaesthetics"
    ANTRHOPOSOPHICAL = "anthroposophical"
    APPLIED_KINESIOLOGY = "applied_kinesiology"
    AROMATHERAPY = "aromatherapy"
    AYUREVDA = "ayurveda"
    BARIATRIC_SURGERY = "bariatric_surgery"
    BIOLOGY = "biology"
    BIOCHEMISTRY = "biochemistry"
    BLOOD_CHECK = "blood_check"
    CARDIOLOGY = "cardiology"
    CARDIOTHORACIC_SURGERY = "cardiothoracic_surgery"
    CHILD_PSYCHIATRY = "child_psychiatry"
    CHIROPRATIC = "chiropractic"
    CLINICAL_PATHOLOGY = "clinical_pathology"
    COMMUNITY = "community"
    DERMATOLOGY = "dermatology"
    DERMATOVENEREOLOGY = "dermatovenereology"
    DIAGNOSTIC_RADIOLOGY = "diagnostic_radiology"
    EMERGENCY = "emergency"
    ENDOCRINOLOGY = "endocrinology"
    ENDODONTICS = "endodontics"
    FERTILITY = "fertility"
    GASTROENTEROLOGY = "gastroenterology"
    GENERAL = "general"
    GERIATRICS = "geriatrics"
    GYNAECOLOGY = "gynaecology"
    HAEMATOLOGY = "haematology"
    HEPATOLOGY = "hepatology"
    HERBALISM = "herbalism"
    HOMEOPATHY = "homeopathy"
    HYDROTHERAPY = "hydrotherapy"
    HYPNOSIS = "hypnosis"
    IMPLANTOLOGY = "implantology"
    INFECTIOUS_DISEASES = "infectious_diseases"
    INTENSIVE = "intensive"
    INTERNAL = "internal"
    MAXILLOFACIAL = "dental_oral_maxillo_facial_surgery"
    NATUROPATHY = "naturopathy"
    NEONATOLOGY = "neonatology"
    NEPHROLOGY = "nephrology"
    NEUROLOGY = "neurology"
    NEUROPSYCHIATRY = "neuropsychiatry"
    NEUROSURGERY = "neurosurgery"
    NUCLEAR = "nuclear"
    OBSTRETIC_ULTRASONOGRAPHY = "obstetric_ultrasonography"
    OCCUPATIONAL = "occupational"
    ONCOLOGY = "oncology"
    OPHTHALMOLOGY = "ophthalmology"
    ORTHODONTICS = "orthodontics"
    ORTHOPAEDICS = "orthopaedics"
    OSTEOPATHY = "osteopathy"
    OTOLARYNGOLOGY = "otolaryngology"
    PAEDIATRIC_DENTISTRY = "paediatric_dentistry"
    PAEDIATRIC_SURGERY = "paediatric_surgery"
    PAEDIATRICS = "paediatrics"
    PAIN_MEDICINE = "pain_control"
    PALLIATIVE = "palliative"
    PATHOLOGY = "pathology"
    PERIODONTICS = "periodontics"
    PHYSIATRY = "physiatry"
    PLASTIC_SURGERY = "plastic_surgery"
    PODIATRY = "podiatry"
    PROCTOLOGY = "proctology"
    PSYCHIATRY = "psychiatry"
    PSYCHOTHERAPHY_BEHAVIOR = "behavior"
    PSYCHOTHERAPHY_BODY = "body"
    PSYCHOTHERAPHY_DEPTH = "depth"
    PSYCHOTHERAPHY_HUMANISTIC = "humanistic"
    PSYCHOTHERAPHY_SYSTEMIC = "systemic"
    PULMONOLOGY = "pulmonology"
    RADIOLOGY = "radiology"
    RADIOTHERAPY = "radiotherapy"
    REFLEXOLOGY = "reflexology"
    REHABILITATION = "rehabilitation"
    REIKI = "reiki"
    RHEUMATOLOGY = "rheumatology"
    SHIATSU = "shiatsu"
    SLEEP_MEDICINE = "sleep"
    STOMATOLOGY = "stomatology"
    SURGERY = "surgery"
    TRADITIONAL_CHINESE_MEDICINE = "traditional_chinese_medicine"
    TRANSPLANT = "transplant"
    TRAUMA = "trauma"
    TROPICAL = "tropical"
    TUINA = "tuina"
    UNANI = "unani"
    UROLOGY = "urology"
    VACCINATION = "vaccination"
    VASCULAR_SURGERY = "vascular_surgery"
    VENEREOLOGY = "venereology"
    WOUND_TREATMENT = "wound_treatment"


def apply_healthcare_specialities(specialities: [HealthcareSpecialities], item: Feature):
    """
    Apply healthcare specialities to a Feature. If the Feature
    already has healthcare specialities defined, this function will
    append to the list of healthcare specialities rather than
    overwriting existing healthcare specialities. When appending,
    the list of healthcare specialities is sorted and then each
    value is separated with a semi-colon.
    :param clothes: array of HealthcareSpecialities Enum members
    :param item: Feature which should have healthcare specialities applied.
    """
    for s in specialities:
        apply_category({"healthcare:speciality": s.value}, item)


# TODO: something similar for fuel types
def map_payment(item: Feature, payment_method: str, enum: PaymentMethods | FuelCards):
    """Apply appropriate payment method tag to an item if given string is found in an enum."""
    if not payment_method:
        return
    map = {}
    for payment in enum:
        variations = DictParser.get_variations(payment.name.replace("_", "-"))
        variations.add(payment.name.replace("_", " ").lower())
        variations.add(payment.name.replace("_", " ").title())
        variations.add(payment.name.replace("_", " ").upper())
        for variation in variations:
            map[variation] = payment.name

    if payment := map.get(payment_method):
        apply_yes_no(enum[payment], item, True)
        return True
