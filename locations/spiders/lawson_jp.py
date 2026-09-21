from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, Fuel, PaymentMethods, Sells, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.area_marker import AreaMarkerSpider

BRANDS = {
    "1": ("LAWSON", "Q1557223"),
    "2": ("NATURAL LAWSON", "Q11323850"),
    "4": ("LAWSON STORE 100", "Q11350960"),
}


class LawsonJPSpider(AreaMarkerSpider):
    name = "lawson_jp"
    item_attributes = {"brand": "LAWSON", "brand_wikidata": "Q1557223"}
    corp_id = "lawson"
    fields = {
        "ref": "kyo_id",  # store id
        "branch": "name",  # branch name, without the brand prefix
        "lat": "lat_en",  # latitude (WGS84. API also exposes lat_jp/lon_jp in the Tokyo datum)
        "lon": "lon_en",  # longitude (WGS84)
        "pre_code": "pre_code",  # prefecture (JIS) code
        "city_code": "city_code",  # municipality (JIS) code
        "addr": "addr_1",  # full street address
        "city": "col_3",  # municipality
        "street_address": "col_4",  # address (from neighborhood)
        "phone_col": "col_5",  # phone (duplicate of tel_1)
        "brand": "col_6",  # brand, defined in BRANDS
        "24h": "col_7",  # open 24/7
        "open_time": "col_8",  # opening time
        "close_time": "col_9",  # closing time
        "atm": "col_10",  # ATM
        "phone": "tel_1",  # phone number
        "alcohol": "col_11",  # alcohol
        "tobacco": "col_12",  # tobacco
        "fax_flag": "col_13",  # has fax
        "medicine": "col_15",  # medicine
        "suica": "col_16",  # Suica payment
        "kitaca": "col_17",  # Kitaca payment
        "icoca": "col_18",  # icoca payment
        "branch_hira": "col_29",  # branch name (hiragana)
        "car_charging": "col_33",  # electric car charger
        "photo_print": "col_36",  # digital photo printing
        "dry_cleaning": "col_48",  # dry cleaning pickup
        "wifi": "col_49",  # has wifi
        "fruit_veg": "col_51",  # fruits and vegetables
        "copier": "col_52",  # has printer
        "parking": "col_53",  # has parking
        "manaca": "col_54",  # manaca payment
        "books": "col_56",  # sells books
        "self_service": "col_61",  # smartphone checkout
        "indoor_seating": "col_57",  # eating space
        "wheelchair_toilet": "col_58",  # accessible toilet
        "halal": "col_75",  # halal food
        "tax_free": "col_76",  # duty free
        "soft_serve": "col_77",  # soft-serve ice cream
        "parcel_from": "col_78",  # send parcels with Smari
        "uber_eats": "col_79",  # Uber Eats delivery
    }

    def post_process_item(
        self, item: Feature, response: TextResponse, store: dict, raw_record: dict, **kwargs
    ) -> Iterable[Feature]:
        item["brand"], item["brand_wikidata"] = BRANDS.get(store["brand"], (None, None))
        item["branch"] = store["branch"]
        item.set_tag("branch:ja-Hira", store["branch_hira"])
        item["name"] = None
        item["website"] = f"https://www.areamarker.com/{self.corp_id}/info/{store['ref']}"
        item["addr_full"] = store["addr"]

        apply_category(Categories.SHOP_CONVENIENCE, item)

        apply_yes_no(Sells.TOBACCO, item, store["tobacco"] == "1")
        apply_yes_no(Sells.ALCOHOL, item, store["alcohol"] == "1")
        apply_yes_no(Sells.BOOKS, item, store["books"] == "1")

        apply_yes_no(PaymentMethods.SUICA, item, store["suica"] == "1")
        apply_yes_no(PaymentMethods.KITACA, item, store["kitaca"] == "1")
        apply_yes_no(PaymentMethods.ICOCA, item, store["icoca"] == "1")
        apply_yes_no(PaymentMethods.MANACA, item, store["manaca"] == "1")

        apply_yes_no(Extras.ATM, item, store["atm"] == "1")
        apply_yes_no(Extras.COPYING, item, store["copier"] == "1")
        apply_yes_no(Extras.DELIVERY, item, store["uber_eats"] == "1")
        apply_yes_no(Extras.DUTY_FREE, item, store["tax_free"] == "1")
        apply_yes_no("self_service", item, store["self_service"] == "1")
        apply_yes_no(Extras.INDOOR_SEATING, item, store["indoor_seating"] == "1")
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, store["wheelchair_toilet"] == "1")
        apply_yes_no(Extras.HALAL, item, store["halal"] == "1")
        apply_yes_no(Extras.PARKING, item, store["parking"] == "1")
        apply_yes_no(Extras.WIFI, item, store["wifi"] == "1")
        apply_yes_no(Fuel.ELECTRIC, item, store["car_charging"] == "1")
        apply_yes_no("dry_cleaning", item, store["dry_cleaning"] == "1")
        if store["parcel_from"] == "1":
            item.set_tag("post_office", "post_partner")
            item.set_tag("post_office:parcel_from", "yes")
            item.set_tag("post_office:service_provider", "Smari")

        if store["24h"] == "1":
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, store["open_time"], store["close_time"])

        yield item
