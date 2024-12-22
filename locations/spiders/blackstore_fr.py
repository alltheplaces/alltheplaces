import re

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.user_agents import BROWSER_DEFAULT


class BlackstoreFRSpider(Spider):
    name = "blackstore_fr"
    item_attributes = {"brand": "Blackstore", "brand_wikidata": "Q125446765", "extras": Categories.SHOP_CLOTHES.value}
    start_urls = ["https://www.blackstore.fr/store-finder/"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        js_blob = response.xpath('//script/text()[contains(., "var locationsMap")]').get()
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location)
            item["name"] = location["title"].strip().title()
            if item["name"].startswith("Blackstore - "):
                item["branch"] = item["name"].removeprefix("Blackstore - ")
                item["name"] = "Blackstore"
            item["addr_full"] = re.sub(r"\s*\n", ", ", item["addr_full"])
            if not re.search("[a-z]", item["addr_full"]):
                item["addr_full"] = item["addr_full"].title()
            item["opening_hours"] = self.format_opening_hours(location["weekOpeningHours"])
            yield item

    def format_opening_hours(self, opening_hours):
        hours = OpeningHours()
        for day_definition in opening_hours:
            if day_definition["closed"] == "false":
                day = sanitise_day(day_definition["weekDay"], DAYS_FR)
                for time_slot in (1, 2):
                    if day_definition[f"openingTime{time_slot}"] and day_definition[f"closingTime{time_slot}"]:
                        hours.add_range(
                            day,
                            day_definition[f"openingTime{time_slot}"],
                            day_definition[f"closingTime{time_slot}"],
                            "%H%M",
                        )
        return hours
