from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Drink, Extras, Sells, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

API_ENDPOINT = "https://store.seicomart.co.jp/api_shp_data_search.php"
WEBSITE_TEMPLATE = "https://store.seicomart.co.jp/detail.php?nbr={store_id}"

# API endpoint search stores from center of point up to specified limit
# a single POINT returns the full national dataset when LIMIT is high enough
# Chose the store "はせべ店" coordinates (https://store.seicomart.co.jp/detail.php?nbr=21113)
# as an arbitrary center since this is the first store used the name"Seicomart" :)
POINT = "LON141.3022117LAT43.07842875"
# As of July 2026, total store count is  1,189 (https://secoma.co.jp/aboutus/company.html)
LIMIT = "3000"

# amenity flags: ``shp_dataN`` == icon number
# where N = 1 お酒, 2 たばこ, 5 HOTCHEFベーカリー, 6 ATM, 10 セコマカフェ
# HOTCHEF (4) and 証明写真BOX (photobooth box) (7) are skipped since it has no valid OSM key.
# 8/9/11/12 are internal flag, not shown on the page
FLAG_ALCOHOL = "shp_data1"
FLAG_TOBACCO = "shp_data2"
FLAG_BAKERY = "shp_data5"
FLAG_ATM = "shp_data6"
FLAG_COFFEE = "shp_data10"


class SeicomartJPSpider(Spider):
    """Seicomart Japan convenience stores.

    The site is an old PHP store finder whose pages redirect unless reached by form
    POST. Store data comes from a single ajax POST to `api_shp_data_search.php` could return the full national chain as JSON, no pagination.
    """

    name = "seicomart_jp"
    item_attributes = {"brand": "Seicomart", "brand_wikidata": "Q11314123"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(url=API_ENDPOINT, formdata={"POINT": POINT, "LIMIT": LIMIT})

    def parse(self, response: Response) -> AsyncIterator[Feature]:
        for store in response.json()["result"]["data"]:
            # Dropped fields:
            # - `distance_km` (distance from the POINT origin)
            # - `icon_html10`/`icon_html20` (display markup)
            # - `shp_data3` (24h flag is duplicated with `opening_hours`)

            item = DictParser.parse(store)
            item["ref"] = store["shp_code"]
            item["branch"] = store["shp_name"]
            item["addr_full"] = store["shp_addr"]
            item["website"] = WEBSITE_TEMPLATE.format(store_id=store["shp_code"])

            self.apply_opening_hours(item, store["shp_eigyo_time"])

            apply_yes_no("sells:alcohol", item, store[FLAG_ALCOHOL] == "1", apply_positive_only=False)
            apply_yes_no(Sells.TOBACCO, item, store[FLAG_TOBACCO] == "1", apply_positive_only=False)
            apply_yes_no("bakery", item, store[FLAG_BAKERY] == "1", apply_positive_only=False)
            apply_yes_no(Extras.ATM, item, store[FLAG_ATM] == "1", apply_positive_only=False)
            apply_yes_no(Drink.COFFEE, item, store[FLAG_COFFEE] == "1", apply_positive_only=False)

            yield item

    @staticmethod
    def apply_opening_hours(item: Feature, value: str) -> None:
        if value == "24時間営業":
            item["opening_hours"] = "24/7"
            return

        open_time, close_time = value.split("～")
        opening_hours = OpeningHours()
        opening_hours.add_days_range(DAYS, open_time, close_time, "%H:%M")
        item["opening_hours"] = opening_hours.as_opening_hours()
