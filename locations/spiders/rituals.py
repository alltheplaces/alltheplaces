import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RitualsSpider(Spider):
    name = "rituals"
    item_attributes = {"brand": "Rituals", "brand_wikidata": "Q62874140"}

    start_urls = ["https://www.rituals.com/en-nl/stores"]

    def parse(self, response):
        api_key = re.search(
            r'dhora\.rituals\.com","API_KEY":"([^"]+)"',
            response.text,
        ).group(1)
        yield self.make_request(api_key)

    def make_request(self, api_key, offset=0):

        return JsonRequest(
            url=f"https://dhora.rituals.com/retail/stores?locale=en-nl&limit=100&offset={offset}",
            headers={"x-api-key": api_key},
            callback=self.parse_locations,
            meta={"api_key": api_key},
        )

    def parse_locations(self, response):
        json_data = response.json()

        for location in json_data.get("data"):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            try:
                oh = OpeningHours()
                for rule in location.get("openingHours"):
                    open_time = rule.get("openingTime")
                    close_time = rule.get("closingTime")
                    if open_time is None and close_time is None:
                        oh.set_closed(rule.get("name"))
                    else:
                        oh.add_range(rule.get("name"), open_time, close_time.replace("59.9999999", "59"), "%H:%M:%S")
                item["opening_hours"] = oh
            except:
                pass
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item

        next_offset = json_data.get("meta").get("pagination").get("nextOffset")

        if next_offset:
            yield self.make_request(
                response.meta["api_key"],
                next_offset,
            )
