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
                item["street_address"] = None
                item["street"] = location.get("address1")
                item["housenumber"] = location.get("address2")
                if img := location.get("image"):
                    if img not in (
                        "https://www.welkoop.nl/on/demandware.static/-/Sites/default/dw1fb3abe8/Winkel_Algemeen.jpg"
                    ):
                        item["image"] = img

                oh = OpeningHours()
                for hours_data in json.loads(location.get("store_hours")):
                    day = sanitise_day(list(hours_data.get("day").values())[0], DAYS_NL)
                    open_close_time_data = hours_data.get("hours")
                    if open_close_time_data == "Gesloten":
                        oh.set_closed(day)
                    else:
                        for open_close_time in open_close_time_data:
                            open_time = open_close_time.get("open")
                            close_time = open_close_time.get("close")
                            oh.add_range(day=day, open_time=open_time, close_time=close_time)
                item["opening_hours"] = oh

                yield item
