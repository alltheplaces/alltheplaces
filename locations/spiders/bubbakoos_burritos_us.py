from typing import Any, Iterable

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.react_server_components import parse_rsc


class BubbakoosBurritosUSSpider(JSONBlobSpider):
    name = "bubbakoos_burritos_us"
    item_attributes = {"brand": "Bubbakoo's Burritos", "brand_wikidata": "Q114619751"}
    start_urls = ["https://locations.bubbakoos.com/location-directory"]

    def extract_json(self, response: Response) -> list[dict]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        locations = {}
        self.find_locations(dict(parse_rsc(rsc.encode())), locations)
        return list(locations.values())

    def find_locations(self, node: Any, locations: dict) -> None:
        if isinstance(node, dict):
            if "latitude" in node and "id" in node:
                locations[node["id"]] = node
            for value in node.values():
                self.find_locations(value, locations)
        elif isinstance(node, list):
            for value in node:
                self.find_locations(value, locations)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = (
            item.pop("name")
            .removesuffix("Bubbakoo's Burritos")
            .removesuffix("Bubbakoo’s Burritos")
            .removesuffix("Bubbakoo's Burrito's")
            .strip(" -")
        )
        item["street_address"] = item.pop("addr_full")

        item["opening_hours"] = OpeningHours()
        for calendar in feature.get("calendars") or []:
            if calendar.get("type") != "business":
                continue
            for rule in calendar.get("ranges") or []:
                item["opening_hours"].add_range(rule["weekday"], rule["start"].split(" ")[1], rule["end"].split(" ")[1])

        # item["website"]  = "https://locations.bubbakoos.com/location-directory/{}/{}/{}".format("", feature["slug"], feature["location_slug"])

        apply_yes_no(Extras.DELIVERY, item, feature.get("supportsDelivery"))
        apply_category(Categories.FAST_FOOD, item)

        yield item
