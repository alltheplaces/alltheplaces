from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HTPawnbrokersGBSpider(JSONBlobSpider):
    name = "h_t_pawnbrokers_gb"
    item_attributes = {"brand": "H&T Pawnbrokers", "brand_wikidata": "Q105672451"}
    start_urls = ["https://as-handt-store-address-service.azurewebsites.net/api/AllStoreData"]

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["name"] = "H&T Pawnbrokers"
        item["phone"] = location["storeTelephone1"]
        item["image"] = location["storeImage"]
        item["website"] = urljoin("https://handt.co.uk/pages/", item["branch"].replace(" ", "-"))

        oh = OpeningHours()
        for day in DAYS_FULL:
            if not (hours := location.get(day.lower(), "").replace(".", ":").replace(";", ":").strip()):
                continue
            if hours.lower() == "closed":
                oh.set_closed(day)
            else:
                oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh

        if item["lat"]:
            yield item
