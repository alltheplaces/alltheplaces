from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class Tele2SESpider(Spider):
    name = "tele2_se"
    item_attributes = {"brand": "Tele2", "brand_wikidata": "Q309865"}
    allowed_domains = [""]
    start_urls = ["https://api-web.tele2.se/content/store/collection"]

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item.pop("phone", None)
            item["website"] = "https://www.tele2.se/butiker/" + location["slug"]
            hours_string = (
                "Mo-Fr: "
                + location.get("weekdayOpenTimes", "")
                + " Sa: "
                + location.get("saturdayOpenTimes", "")
                + " Su: "
                + location.get("sundayOpenTimes", "")
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
