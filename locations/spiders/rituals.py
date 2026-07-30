import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RitualsSpider(Spider):
    name = "rituals"

    item_attributes = {
        "brand": "Rituals",
        "brand_wikidata": "Q62874140",
    }

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

        for location in json_data.get(
            "data",
        ):
            item = DictParser.parse(location)
            try:
                oh = OpeningHours()
                for day_time in location.get("openingHours"):
                    day = day_time.get("name")
                    open_time = day_time.get("openingTime")
                    close_time = day_time.get("closingTime")
                    if open_time is None and close_time is None:
                        oh.set_closed(day)
                    else:
                        oh.add_range(
                            day=day,
                            open_time=open_time,
                            close_time=close_time.replace("59.9999999", "59"),
                            time_format="%H:%M:%S",
                        )
                item["opening_hours"] = oh
            except:
                pass
            yield item

        next_offset = json_data.get("meta").get("pagination").get("nextOffset")

        if next_offset:
            yield self.make_request(
                response.meta["api_key"],
                next_offset,
            )
