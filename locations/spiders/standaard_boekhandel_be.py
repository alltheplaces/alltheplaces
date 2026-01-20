from typing import Iterable
from urllib.parse import urljoin

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

STANDAARD_BOEKHANDEL = {"brand": "Standaard Boekhandel", "brand_wikidata": "Q3496554"}
CLUB = {"name": "Club", "brand": "Club"}


class StandaardBoekhandelBESpider(JSONBlobSpider):
    name = "standaard_boekhandel_be"
    start_urls = ["https://www.standaardboekhandel.be/winkels"]

    def extract_json(self, response: Response) -> list[dict]:
        data_parm = response.xpath('//div[@data-component-class="SB.Ecom.ShopLister.Init"]/@data-component-parm').get()
        if data_parm:
            data = chompjs.parse_js_object(data_parm)
            return data.get("shops", [])
        return []

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        shop = feature.get("shop", {})

        shop["ref"] = shop.pop("shopNumber")
        shop["housenumber"] = shop.pop("number")

        item = DictParser.parse(shop)
        item["branch"] = item.pop("name")
        item["website"] = urljoin("https://www.standaardboekhandel.be/", feature["url"])

        item["opening_hours"] = self.parse_opening_hours(feature["openingDays"])

        if "sb" in shop["brands"]:
            item.update(STANDAARD_BOEKHANDEL)
        elif "club" in shop["brands"]:
            item.update(CLUB)

        apply_category(Categories.SHOP_BOOKS, item)

        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for day in rules:
            for rule in day["openingSlots"]:
                oh.add_range(DAYS[day["dayOfWeek"] - 1], rule["from"], rule["to"])
        return oh
