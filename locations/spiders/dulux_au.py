from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

BRANDS = {
    "dulux": {"brand": "DuluxTRADE", "brand_wikidata": "Q140574318"},
    "paintspot": {"brand": "Paint Spot", "brand_wikidata": "Q117852598"},
}

class DuluxAUSpider(JSONBlobSpider):
    name = "dulux_au"
    allowed_domains = ["www.duluxtrade.com.au"]
    start_urls = ["https://www.duluxtrade.com.au/api/stores.json"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if phone := feature.get("ctaTelephone"):
            item["phone"] = phone
        if slug := feature.get("ctaLink"):
            item["website"] = f"https://www.duluxtrade.com.au{slug}"

        if feature["storeType"] in BRANDS.keys():
            item["brand"] = BRANDS[feature["storeType"]]["brand"]
            item["brand_wikidata"] = BRANDS[feature["storeType"]]["brand_wikidata"]
        elif feature["storeType"] == "inspirations":
            # Separate franchise/retail chain which is a stockist -- ignore.
            return
        elif feature["storeType"] == "sunrise":
            # Stockists such as Mitre 10 and Home Timber and Hardware -- ignore.
            return
        else:
            self.logger.error("Unknown brand: {}".format(feature["storeType"]))
            return

        item["opening_hours"] = OpeningHours()
        for day_hours in feature.get("weeklyOpeningHours", []):
            if day_hours["closed"]:
                item["opening_hours"].set_closed(day_hours["weekDay"])
                continue
            item["opening_hours"].add_range(day_hours["weekDay"], day_hours["openingTime"]["formattedHour"], day_hours["closingTime"]["formattedHour"], "%I:%M %p")

        apply_category(Categories.SHOP_PAINT, item)

        yield item
