import re
import unicodedata
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, Sells, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.areamarker import AreamarkerSpider

# descriptive label -> API column name. meanings from the map page's
# https://www.areamarker.com/daily-yamazaki/data/filterStore.json labels.
FIELDS = {
    "ref": "kyo_id",  # store id
    "name": "name",  # full store name, e.g. デイリ－ヤマザキ本八幡駅前店
    "lat": "lat_en",  # latitude (WGS84. API also exposes lat_jp/lon_jp in the Tokyo datum)
    "lon": "lon_en",  # longitude (WGS84)
    "addr": "addr_1",  # full street address
    "postcode": "zip_code",  # postal code
    "phone": "tel_1",  # phone number
    "hours": "b_mon",  # opening hours; every weekday shares one value, e.g. 06:00-23:00
    "alcohol": "col_6",  # お酒 (alcohol)
    "tobacco": "col_7",  # タバコ (tobacco)
    "atm": "col_8",  # ATM
    "fresh_bread": "col_9",  # 焼きたてパン (fresh-baked bread)
    "bento": "col_10",  # 手づくり弁当 (handmade lunch boxes)
    "fried_food": "col_11",  # FF惣菜 唐揚げ (fried food)
    "copier": "col_12",  # マルチコピー (multi-function copier)
    "self_checkout": "col_13",  # セルフレジ (self-checkout)
    "rakuten_check": "col_14",  # 楽天チェック (Rakuten Check)
    "online_pickup": "col_15",  # ネット商品受取 (online order pickup)
}

# The brand-family name is spelled with either ー (U+30FC) or － (U+FF0D) and
# historically as デイリーヤマザキ / ニューヤマザキデイリーストア /
# ヤマザキデイリーストア. Strip it to leave the location-specific branch name.
DASH_RE = "[ー－]"
BRAND_PREFIX_RE = re.compile(
    rf"^(?:デイリ{DASH_RE}ヤマザキ|ニューヤマザキデイリ{DASH_RE}ストアー?|ヤマザキデイリ{DASH_RE}ストアー?)"
)
OPENING_HOURS_RE = re.compile(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$")


class DailyYamazakiJPSpider(AreamarkerSpider):
    name = "daily_yamazaki_jp"
    item_attributes = {
        "brand": "Daily YAMAZAKI",
        "brand_wikidata": "Q5209392",
        "extras": {
            "brand:en": "Daily YAMAZAKI",
            "brand:ja": "デイリーヤマザキ",
        },
    }

    api_url = "https://ss-api.areamarker.com/v1/search-by-condition"
    corp_id = "daily-yamazaki"
    referer = "https://www.areamarker.com/daily-yamazaki/"
    fields = list(FIELDS.values())
    page_size = 500

    def post_process_item(self, record: dict, response: TextResponse) -> Iterable[Feature]:
        # The API omits empty fields, so use .get() and treat a missing
        # service column as absent rather than a failed scrape.
        store = {label: record["fields"].get(column) for label, column in FIELDS.items()}

        item = Feature()
        item["ref"] = store["ref"]
        item["lat"] = store["lat"]
        item["lon"] = store["lon"]

        # Normalize inconsistent store names
        if m := BRAND_PREFIX_RE.match(store["name"]):
            item["branch"] = store["name"][m.end() :]
        else:
            item["branch"] = store["name"]
        item["phone"] = store["phone"]
        item["website"] = f"https://www.areamarker.com/daily-yamazaki/info/{store['ref']}"
        item["addr_full"] = unicodedata.normalize("NFKC", store["addr"])
        item["postcode"] = store["postcode"]

        if store["hours"] == "00:00-23:59":
            item["opening_hours"] = "24/7"
        elif m := OPENING_HOURS_RE.match(store["hours"]):
            oh = OpeningHours()
            oh.add_days_range(DAYS, m.group(1), m.group(2))
            item["opening_hours"] = oh

        apply_yes_no(Sells.ALCOHOL, item, store["alcohol"] == "1")
        apply_yes_no(Sells.TOBACCO, item, store["tobacco"] == "1")
        apply_yes_no(Extras.ATM, item, store["atm"] == "1")
        apply_yes_no(Extras.COPYING, item, store["copier"] == "1")
        apply_yes_no(Extras.SELF_CHECKOUT, item, store["self_checkout"] == "1")

        # Skipped service flags (no established OSM tag):
        #   store["fresh_bread"] 焼きたてパン (fresh-baked bread)
        #   store["bento"] 手づくり弁当 (handmade lunch boxes)
        #   store["fried_food"] FF惣菜 唐揚げ (fried food)
        #   store["rakuten_check"] 楽天チェック (Rakuten Check - unknown Rakuten service)
        #   store["online_pickup"] ネット商品受取 (online order pickup)

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
