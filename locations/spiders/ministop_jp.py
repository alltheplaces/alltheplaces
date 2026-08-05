from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MinistopJPSpider(JSONBlobSpider):
    name = "ministop_jp"
    locations_key = "shops"
    start_urls = [
        f"https://api.site.can-ly.com/v2/directories/94/shops/search?location_filter=true&sort=off&map_view_geohash={geohash}"
        for geohash in ("w", "x")
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        if feature["openStatus"] != "IS_ALREADY_OPEN":
            return

        name = feature["nameKanji"]
        if name.startswith("ミニストップ"):
            item["branch"] = name.removeprefix("ミニストップ").strip()
            item["brand"] = "Ministop"
            item["brand_wikidata"] = "Q1038929"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif name.startswith("MINI SOF"):
            item["branch"] = name.removeprefix("MINI SOF").strip()
            item["brand"] = "MINISOF"
            item["brand_wikidata"] = "Q134958024"
            apply_category(Categories.ICE_CREAM, item)
        elif name.startswith("cisca"):
            item["branch"] = name.removeprefix("cisca").strip()
            item["brand"] = "cisca"
            item["brand_wikidata"] = "Q134958099"
            apply_category(Categories.CAFE, item)
        else:
            self.logger.warning(f"Unknown brand name as prefix to location name: {name}")

        item["ref"] = str(feature["storeCode"])
        item["extras"]["alt_ref"] = str(feature["storeId"])
        item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["businessHours"]:
            if day_hours["hourType"] == 2:
                item["opening_hours"].add_range(day_hours["name"], "00:00", "24:00")
            else:
                item["opening_hours"].add_range(
                    day_hours["name"], day_hours["openTime"], day_hours["closeTime"], "%H:%M:%S"
                )

        yield item
