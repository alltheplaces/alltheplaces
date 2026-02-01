from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class RollerDESpider(JSONBlobSpider):
    name = "roller_de"
    item_attributes = {"brand": "Roller", "brand_wikidata": "Q1621286"}
    start_urls = [
        "https://www.roller.de/api/retail-stores?currentPage=0&latitude=52.51737&longitude=13.403289&pageSize=500"
    ]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["address"].get("line1"), feature["address"].get("line2")])
        item["branch"] = item.pop("name").removeprefix("ROLLER - ")
        item["website"] = response.urljoin(feature["url"].split("?")[0]) if feature.get("url") else None

        images = feature.get("images") or []
        for image in images:
            if image.get("format") == "store":
                item["image"] = response.urljoin(image.get("url"))
                break

        if "geschlossen" in feature.get("hintText", ""):
            set_closed(item)

        item["opening_hours"] = OpeningHours()
        opening_hours = feature.get("openingHours", {}).get("weekDayOpenings") or []
        for rule in opening_hours:
            if day := sanitise_day(rule.get("weekDay"), DAYS_DE):
                if rule.get("isClosed"):
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, rule.get("openingTime"), rule.get("closingTime"))
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
