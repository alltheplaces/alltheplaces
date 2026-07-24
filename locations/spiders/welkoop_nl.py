import json

from requests import Response
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class WelkoopNLSpider(Spider):
    name = "welkoop_nl"
    item_attributes = {"brand": "Welkoop", "brand_wikidata": "Q72799253"}
    start_urls = ["https://www.welkoop.nl/winkels"]

    def parse(self, response: Response, **kwargs):
        queries = json.loads(
            response.xpath('//script[@type="application/json"][contains(text(), "__PRELOADED_STATE__")]/text()').get()
        )["__PRELOADED_STATE__"]["__reactQuery"]["queries"]
        for query in queries:
            if not query["queryKey"][0].startswith("stores?"):
                continue
            for location in query["state"]["data"]["data"]:
                if location["_type"] != "store":
                    continue

                item = DictParser.parse(location)
                item["branch"] = item.pop("name").removeprefix("Welkoop ").removeprefix("WELKOOP ")
                item["street_address"] = item["state"] = None
                item["street"] = location["address1"]
                item["housenumber"] = location["address2"]
                if location.get("image") not in (
                    None,
                    "https://www.welkoop.nl/on/demandware.static/-/Sites/default/dw1fb3abe8/Winkel_Algemeen.jpg",
                ):
                    item["image"] = location["image"]

                try:
                    item["opening_hours"] = self.parse_opening_hours(location["store_hours"])
                except Exception:
                    pass

                yield item

    def parse_opening_hours(self, store_hours: str) -> OpeningHours:
        oh = OpeningHours()
        for rule in json.loads(store_hours):
            day = sanitise_day(rule["day"]["nl-NL"], DAYS_NL)
            if rule["hours"] == "Gesloten":
                oh.set_closed(day)
            else:
                for period in rule["hours"]:
                    oh.add_range(day, period["open"], period["close"])
        return oh
