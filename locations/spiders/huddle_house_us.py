from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class HuddleHouseUSSpider(Spider):
    name = "huddle_house_us"
    item_attributes = {"brand": "Huddle House", "brand_wikidata": "Q5928324"}
    allowed_domains = ["www.huddlehouse.com"]
    start_urls = ["https://www.huddlehouse.com/api"]
    download_delay = 0.2

    def start_requests(self):
        for url in self.start_urls:
            for lat, lon in point_locations("us_centroids_iseadgg_48km_radius.csv"):
                yield JsonRequest(
                    url=f"{url}?lat={lat}&lng={lon}&radius=50",
                    headers={"path": "locations/search", "client_type": "web"},
                )

    def parse(self, response):
        if not response.json().get("locations"):
            return
        # A maximum of 25 locations are returned at once. The search radius is
        # set to avoid receiving 25 locations in a single response. If 25
        # locations were to be returned, it is a sign that some locations have
        # most likely been truncated.
        for location in response.json()["locations"]:
            if not location.get("available"):
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            if location.get("path"):
                item["website"] = "https://www.huddlehouse.com/locations/" + location["path"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["hours"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(day_hours["day"].title(), day_hours["open"], day_hours["close"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["services"].get("drivethru"), False)
            apply_yes_no(Extras.DELIVERY, item, location["services"].get("delivery"), False)
            apply_yes_no(
                PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in location["payments"]["cardtypes"], False
            )
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in location["payments"]["cardtypes"], False)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in location["payments"]["cardtypes"], False)
            apply_yes_no(PaymentMethods.VISA, item, "Visa" in location["payments"]["cardtypes"], False)
            yield item
