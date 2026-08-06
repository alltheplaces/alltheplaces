from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MinistopJPSpider(JSONBlobSpider):
    name = "ministop_jp"
    start_urls = ["https://api.site.can-ly.com/v2/directories/94/shops/search"]
    locations_key = "shops"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        if feature["nameKanji"].startswith("ミニストップ"):
            item["branch"] = feature["nameKanji"].removeprefix("ミニストップ").strip()  # "Ministop"
            item["brand"] = "Ministop"
            item["brand_wikidata"] = "Q1038929"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif feature["nameKanji"].startswith("MINI SOF"):
            item["branch"] = feature["nameKanji"].removeprefix("MINI SOF").strip()
            item["brand"] = "MINISOF"
            item["brand_wikidata"] = "Q134958024"
            apply_category(Categories.ICE_CREAM, item)
        elif feature["nameKanji"].startswith("cisca"):
            item["branch"] = feature["nameKanji"].removeprefix("cisca").strip()
            item["brand"] = "cisca"
            item["brand_wikidata"] = "Q134958099"
            apply_category(Categories.CAFE, item)
        else:
            self.logger.warning("Unknown brand name as prefix to location name: {}".format(feature["nameKanji"]))

        item["ref"] = str(feature["storeCode"])
        item["extras"]["alt_ref"] = str(feature["storeId"])
        item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["businessHours"]:
            item["opening_hours"].add_range(
                day_hours["name"], day_hours["openTime"], day_hours["closeTime"], "%H:%M:%S"
            )

        yield item
