from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GeorgJensenSpider(JSONBlobSpider):
    name = "georg_jensen"
    item_attributes = {"brand": "Georg Jensen", "brand_wikidata": "Q12313702"}
    start_urls = [
        "https://www.georgjensen.com/on/demandware.store/Sites-GeorgJensen_US-Site/en_US/Stores-GetAllStoresInCountry"
    ]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["GeorgJensenStore"]:
            item["addr_full"] = feature["Address"]
            item["opening_hours"] = OpeningHours()
            item["branch"] = item.pop("name")
            for timings in feature["OpeningHours"]:
                try:
                    item["opening_hours"].add_range(
                        DAYS_EN[timings["Day"]],
                        timings["TimeFrom"].strip(),
                        timings["TimeTo"].strip(),
                        "%I:%M %p",
                    )
                except:
                    pass
            apply_category(Categories.SHOP_JEWELRY, item)
            yield item
