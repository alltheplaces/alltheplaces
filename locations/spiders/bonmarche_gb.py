from json import loads
import re
from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BonmarcheGBSpider(JSONBlobSpider):
    name = "bonmarche_gb"
    item_attributes = {"brand": "Bonmarché", "brand_wikidata": "Q4942146"}
    allowed_domains = ["www.bonmarche.co.uk"]
    locations_key = "stores"

    def start_requests(self) -> Iterable[JsonRequest]:
        for city in city_locations("GB", 500):
            lat, lon = city["latitude"], city["longitude"]
            yield JsonRequest(url=f"https://www.bonmarche.co.uk/on/demandware.store/Sites-BONMARCHE-GB-Site/en_GB/Stores-FindStores?lat={lat}&long={lon}")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["name"]
        item.pop("name", None)
        item["addr_full"] = feature["address2"]
        item.pop("street_address", None)
        item.pop("website", None)

        item["opening_hours"] = OpeningHours()
        hours = loads(re.sub(r"\s+", "", feature["storeHours"]).replace(".", ":"))
        for day_name, day_hours in hours.items():
            item["opening_hours"].add_range(day_name.title(), *day_hours.split("-", 1), "%I:%M%p")

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
