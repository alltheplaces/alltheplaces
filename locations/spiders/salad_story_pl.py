from scrapy import Request, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class SaladStoryPLSpider(Spider):
    name = "salad_story_pl"
    item_attributes = {
        "brand": "Salad Story",
        "extras": {
            **Categories.FAST_FOOD.value,
            "cuisine": "salad;soup",
            "diet:vegetarian": "yes",
        },
    }
    start_urls = ["https://www.saladstory.com/lokale"]
    locals_url_base = "https://www.saladstory.com/restapi/restaurants/"
    allowed_domains = ["www.saladstory.com"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse_token,
            )

    def parse_token(self, response):
        # token is stored in line: "com.upmenu.siteId = '56dd4e07-6f04-11e8-8513-525400841de1';"
        token = response.text.split("com.upmenu.siteId = '")[1].split("';")[0]
        yield Request(
            url=self.locals_url_base + token,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            method="POST",
            callback=self.parse_locals,
        )

    def parse_locals(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item = self.fix_streets(item)
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                day = day.lower()
                open_time = location["openingHours"].get(day + "Open")
                close_time = location["openingHours"].get(day + "Close")
                if open_time and close_time:
                    item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item

    def fix_streets(self, item) -> Feature:
        # split street like: "Al.. Jerozolimskie 54" to street and housenumber
        house_number = item["street"].split(" ")[-1]
        street_cutoff = -len(house_number) - 1
        item["housenumber"] = house_number
        item["street"] = item["street"][:street_cutoff]
        if item["street"].lower().startswith("ul. "):
            item["street"] = item["street"][4:]
        return item
