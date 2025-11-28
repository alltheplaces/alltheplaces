import scrapy

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class HungryJacksSpider(scrapy.Spider):
    name = "hungry_jacks"
    item_attributes = {"brand": "Hungry Jack's", "brand_wikidata": "Q3036373"}
    allowed_domains = ["hungryjacks.com.au"]
    start_urls = ["https://www.hungryjacks.com.au/api/storelist"]

    def parse(self, response):
        data = response.json()

        for i in data:
            properties = {
                "ref": i["store_id"],
                "branch": i["name"],
                "street_address": i["location"]["address"],
                "city": i["location"]["suburb"],
                "state": i["location"]["state"],
                "postcode": i["location"]["postcode"],
                "country": "AU",
                "phone": i["location"]["phone"],
                "lat": i["location"]["lat"],
                "lon": i["location"]["long"],
                "website": response.urljoin(i["storeUrl"]),
                "opening_hours": self.parse_hours(i["hours"]["dine_in"]),
                "extras": {
                    "opening_hours:drive_through": self.parse_hours(i["hours"]["drive_thru"]).as_opening_hours()
                },
            }

            apply_yes_no(Extras.DRIVE_THROUGH, properties, i["facilities"]["drivethru"])

            yield Feature(**properties)

    def parse_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule["is_open"] is False:
                oh.set_closed(rule["day_name"])
            else:
                oh.add_range(rule["day_name"], rule["open"], rule["close"])

        return oh
