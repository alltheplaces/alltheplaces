from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class LadbrokesGBSpider(Spider):
    name = "ladbrokes_gb"
    item_attributes = {"brand": "Ladbrokes", "brand_wikidata": "Q1799875"}
    start_urls = ["https://viewer.blipstar.com/searchdbnew?uid=2470030&lat=53.79&lng=-1.54&type=nearest&value=2000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield from self.parse_response(response)

    @staticmethod
    def parse_response(response):
        for store in response.json():
            if store.get("ad"):
                item = Feature()
                # item["name"] = store["n"]
                item["lat"] = store["lat"]
                item["lon"] = store["lng"]
                item["website"] = store["w"]
                item["ref"] = store["bpid"]
                item["addr_full"] = store["ad"]
                item["postcode"] = store["pc"]
                item["phone"] = store["p"]
                if store["c"] == "ROI":
                    item["country"] = "IE"
                else:
                    item["country"] = "GB"
                try:
                    oh = OpeningHours()
                    for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                        if times := store.get(day):
                            if "-" not in times:
                                continue
                            start_time, end_time = times.split("-")
                            if start_time != "CLOSED":
                                oh.add_range(day, start_time, end_time)
                    item["opening_hours"] = oh
                except:
                    pass

                yield item
