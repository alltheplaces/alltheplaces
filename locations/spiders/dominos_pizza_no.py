from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DominosPizzaNOSpider(JSONBlobSpider):
    name = "dominos_pizza_no"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.no/api/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["ref"] = store.get("externalId")
        item["branch"] = item.pop("name")
        item["phone"] = store.get("localPhoneNumber")
        item["website"] = urljoin("https://www.dominos.no/no/butikker/", store.get("slug"))

        item["street_address"] = item.pop("street")
        item.pop("state")  # Remove invalid state field

        if location := (store.get("address") or {}).get("location"):
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")

        delivery = store.get("deliveryOptions", {}).get("delivery") or {}
        carryout = store.get("deliveryOptions", {}).get("carryout") or {}
        apply_yes_no(Extras.DELIVERY, item, delivery.get("active"))
        apply_yes_no(Extras.TAKEAWAY, item, carryout.get("active"))

        if carryout_hours := carryout.get("hoursOfOperation"):
            item["opening_hours"] = self.parse_hours(carryout_hours)

        if (delivery_hours := delivery.get("hoursOfOperation")) and (oh := self.parse_hours(delivery_hours)):
            item["extras"]["opening_hours:delivery"] = oh.as_opening_hours()

        yield item

    @staticmethod
    def parse_hours(hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for entry in hours:
            if day := entry.get("weekDay"):
                oh.add_range(day, entry.get("openingHours"), entry.get("closingHours"))
        return oh
