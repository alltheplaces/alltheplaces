from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from scrapy.http import TextResponse

from locations.categories import Categories, Drink, Extras, Sells, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.areamarker import AreamarkerSpider

CORP = "711map"
API_URL = "https://seven-eleven-ss-api.areamarker.com/v1/search-by-condition"

# descriptive label -> API column name. meanings from the map page's
# https://seven-eleven.areamarker.com/711map/data/serviceCol.json and sample data.
FIELDS = {
    "ref": "kyo_id",  # store id
    "branch": "name",  # branch name, without the brand prefix
    "period_start": "new_s_date",  # service period start (equals opening_date)
    "period_end": "new_e_date",  # service period end
    "lat": "lat_en",  # latitude (WGS84. API also exposes lat_jp/lon_jp in the Tokyo datum)
    "lon": "lon_en",  # longitude (WGS84)
    "pre_code": "pre_code",  # prefecture (JIS) code
    "city_code": "city_code",  # municipality (JIS) code
    "addr": "addr_1",  # full street address
    "postcode": "zip_code",  # postal code
    "status_flag": "col_1",  # undocumented status flag (observed always "0")
    "opening_date": "col_2",  # store opening date, YYYYMMDDHH (drives the search filter)
    "phone": "col_5",  # phone number
    "tobacco": "col_18",  # tobacco
    "alcohol": "col_19",  # alcohol
    "medicine": "col_52",  # medicine
    "fried_food": "col_21",  # fried foods
    "seven_cafe": "col_26",  # Seven Cafe coffee
    "seven_cafe_smoothie": "col_72",  # Seven Cafe smoothie
    "seven_now_delivery": "col_35",  # 7NOW delivery
    "seven_meal": "col_38",  # Seven Meal
    "seven_delivery": "col_54",  # Seven delivery service
    "atm": "col_17",  # ATM
    "copier": "col_20",  # multi-function copier
    "battery_rental": "col_57",  # mobile battery rental
    "store_hold": "col_53",  # store hold service
    "self_checkout": "col_56",  # self-checkout
    "tax_free": "col_32",  # tax free
    "pet_recycle": "col_55",  # PET bottle recycling machine
}

# The active-store + opening-date conditions are copied from the map page's own query.
# opening_date (col_2) uses the YYYYMMDDHH format (UTC+9), so it returns stores opened up to now.
SEARCH_CONDITIONS = [
    {"field": "col_10", "value": "1", "comparison_operator": "="},
    {"field": "col_2", "value": datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d%H"), "comparison_operator": "<="},
    {
        "conditions": [
            {"field": "col_2", "value": "1", "comparison_operator": "prefix"},
            {"field": "col_2", "value": "2", "comparison_operator": "prefix", "logical_operator": "OR"},
        ]
    },
]


class SevenElevenJPSpider(AreamarkerSpider):
    name = "seven_eleven_jp"
    item_attributes = {
        "brand": "7-ELEVEN",
        "brand_wikidata": "Q259340",
    }

    api_url = API_URL
    corp_id = CORP
    referer = "https://seven-eleven.areamarker.com/711map/"
    fields = list(FIELDS.values())
    search_conditions = SEARCH_CONDITIONS
    # A nationwide query pages through all ~21K stores. Keep the page small enough
    # that a single response stays under the API's ~6MB size cap.
    page_size = 1000

    def post_process_item(self, record: dict, response: TextResponse) -> Iterable[Feature]:
        store = {label: record["fields"][column] for label, column in FIELDS.items()}

        item = Feature()
        item["ref"] = store["ref"]
        item["lat"] = store["lat"]
        item["lon"] = store["lon"]
        item["branch"] = store["branch"]
        item["name"] = None
        item["phone"] = store["phone"]
        item["website"] = f"https://seven-eleven.areamarker.com/711map/info/{store['ref']}"
        item["addr_full"] = store["addr"]
        item["postcode"] = store["postcode"]

        apply_category(Categories.SHOP_CONVENIENCE, item)

        apply_yes_no(Extras.ATM, item, store["atm"] == "1")
        apply_yes_no(Sells.TOBACCO, item, store["tobacco"] == "1")
        apply_yes_no(Sells.ALCOHOL, item, store["alcohol"] == "1")
        apply_yes_no(Extras.COPYING, item, store["copier"] == "1")
        apply_yes_no(Extras.DELIVERY, item, store["seven_now_delivery"] == "1")
        apply_yes_no(Extras.DUTY_FREE, item, store["tax_free"] == "1")
        apply_yes_no(Extras.SELF_CHECKOUT, item, store["self_checkout"] == "1")
        apply_yes_no(Drink.COFFEE, item, store["seven_cafe"] == "1")
        if store["pet_recycle"] == "1":
            item["extras"]["recycling:pet_drink_bottles"] = "yes"

        # Skipped service flags (no established OSM tag):
        #   store["fried_food"] 揚げ物惣菜 (fried foods)
        #   store["seven_cafe_smoothie"] セブンカフェスムージー (Seven Cafe smoothie)
        #   store["seven_meal"] セブンミール (Seven Meal)
        #   store["medicine"] 薬 (medicine)
        #   store["store_hold"] 店舗留置サービス (store hold service)
        #   store["seven_delivery"] セブンあんしんお届け便 (mobile sales for remote areas)
        #   store["battery_rental"] モバイルバッテリーサービス (mobile battery rental)

        yield item
