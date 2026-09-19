import re
import unicodedata
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.areamarker import AreamarkerSpider

# descriptive label -> API column name. meanings from the map page's
# https://shop.seria-group.com/seria/data/filterStore.json labels.
FIELDS = {
    "ref": "kyo_id",  # store id
    "name": "name",  # full store name, e.g. Seria サッポロファクトリー店
    "lat": "lat_en",  # latitude (WGS84)
    "lon": "lon_en",  # longitude (WGS84)
    "addr": "addr_1",  # full street address
    "postcode": "zip_code",  # postal code
    "phone": "tel_1",  # phone number
    "hours": "b_mon",  # opening hours start; every weekday shares one value
    "large": "col_1",  # 大型店 (large store)
    "new": "col_2",  # 新店 (new store)
    "credit_cards": "col_4",  # 各種クレジットカード (credit cards)
    "ic": "col_5",  # 交通系IC (transport IC stored-fare cards)
    "id": "col_6",  # iD
    "quicpay": "col_7",  # QUIC Pay
    "waon": "col_8",  # WAON
    "nanaco": "col_9",  # nanaco
    "edy": "col_10",  # 楽天Edy (Rakuten Edy)
    "rakuten_pay": "col_11",  # 楽天ペイ (Rakuten Pay)
    "d_barai": "col_12",  # d払い (d Payment)
    "au_pay": "col_13",  # au Pay
    "paypay": "col_14",  # PayPay
    "aeon_pay": "col_15",  # AEON Pay
    "smart_code": "col_16",  # Smart Code
}

# The fascia is spelled with either the plain セリア (Seria) or the
# 生活良品 (Seikatsu Ryohin) sub-brand. Strip either prefix to leave the
# location-specific branch name.
BRANCH_RE = re.compile(r"^(?:Seria生活良品|Seria)\s*")
OPENING_HOURS_RE = re.compile(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$")

HOUR_DAY_FIELDS = ["b_mon", "b_tue", "b_wed", "b_thu", "b_fri", "b_sat", "b_sun"]


class SeriaJPSpider(AreamarkerSpider):
    name = "seria_jp"
    item_attributes = {
        "brand": "セリア",
        "brand_wikidata": "Q11314509",
        "extras": {
            "brand:en": "Seria",
            "brand:ja": "セリア",
        },
    }

    api_url = "https://ss-api.areamarker.com/v1/search-by-condition"
    corp_id = "seria"
    referer = "https://shop.seria-group.com/seria/"
    fields = list(FIELDS.values()) + HOUR_DAY_FIELDS[1:]
    page_size = 500

    def post_process_item(self, record: dict, response: TextResponse) -> Iterable[Feature]:
        # The API omits empty fields, so use .get() and treat a missing value
        # as absent rather than a failed scrape.
        store = {label: record["fields"].get(column) for label, column in FIELDS.items()}

        item = DictParser.parse(store)
        item["name"] = None
        item["branch"] = BRANCH_RE.sub("", store["name"])
        item["website"] = f"https://shop.seria-group.com/seria/info/{item['ref']}"
        item["addr_full"] = unicodedata.normalize("NFKC", item["addr_full"])

        self.add_opening_hours(item, record)

        # Payment methods offered in-store.
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, store["credit_cards"] == "1", False)
        apply_yes_no(PaymentMethods.ICSF, item, store["ic"] == "1", False)
        apply_yes_no(PaymentMethods.ID, item, store["id"] == "1", False)
        apply_yes_no(PaymentMethods.QUICPAY, item, store["quicpay"] == "1", False)
        apply_yes_no(PaymentMethods.WAON, item, store["waon"] == "1", False)
        apply_yes_no(PaymentMethods.NANACO, item, store["nanaco"] == "1", False)
        apply_yes_no(PaymentMethods.EDY, item, store["edy"] == "1", False)
        apply_yes_no(PaymentMethods.RAKUTEN_PAY, item, store["rakuten_pay"] == "1", False)
        apply_yes_no(PaymentMethods.D_BARAI, item, store["d_barai"] == "1", False)
        apply_yes_no(PaymentMethods.AU_PAY, item, store["au_pay"] == "1", False)
        apply_yes_no(PaymentMethods.PAYPAY, item, store["paypay"] == "1", False)
        apply_yes_no(PaymentMethods.AEON_PAY, item, store["aeon_pay"] == "1", False)
        apply_yes_no(PaymentMethods.SMART_CODE, item, store["smart_code"] == "1", False)

        # Skipped store flags (no established OSM tag):
        #   store["large"] 大型店 (large store)
        #   store["new"] 新店 (new store)

        apply_category(Categories.SHOP_VARIETY_STORE, item)

        yield item

    @staticmethod
    def add_opening_hours(item: Feature, record: dict) -> None:
        hours_by_day = {}
        for day, field in zip(DAYS, HOUR_DAY_FIELDS, strict=True):
            if value := record["fields"].get(field):
                if match := OPENING_HOURS_RE.match(value):
                    hours_by_day[day] = (match.group(1), match.group(2))

        days_by_hours = {}
        for day, hours in hours_by_day.items():
            days_by_hours.setdefault(hours, []).append(day)

        oh = OpeningHours()
        for hours, days in days_by_hours.items():
            oh.add_days_range(days, hours[0], hours[1])

        item["opening_hours"] = oh
