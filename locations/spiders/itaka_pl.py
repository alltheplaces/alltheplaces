from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class ItakaPLSpider(Spider):
    name = "itaka_pl"
    item_attributes = {"brand": "Itaka", "brand_wikidata": "Q16560452"}
    start_urls = ["https://www.itaka.pl/biura/ajax/get/all/?q=data"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for items in response.json()["data"]:
            # ignoring "agent-prestizowy" and "agent-zwykly"
            # which are travel agencies cooperating but not branded by Itaka
            offices = []

            if "salon-firmowy" in items:
                offices.extend(items["salon-firmowy"])

            if "agent-franchising" in items:
                offices.extend(items["agent-franchising"])

            for office in offices:
                details = office["showroom"]["library"]
                item = DictParser.parse(details)
                item["street_address"] = item.pop("street", None)
                item["ref"] = office["showroom"]["id"]
                if "fotos" in details:
                    item["image"] = ";".join([f"https://www.itaka.pl{url}" for url in details["fotos"]])
                item["website"] = f"https://www.itaka.pl/{details['www']}"

                if opening_hours_day_array := details.get("opening_hours"):
                    opening_hours = OpeningHours()
                    for hours in opening_hours_day_array:
                        if len(hours) != 2:
                            continue

                        days, hours_range = hours
                        hours_range = hours_range.removesuffix("*")
                        opening_hours.add_ranges_from_string(ranges_string=f"{days} {hours_range}", days=DAYS_PL)
                    item["opening_hours"] = opening_hours

                item.pop("name", None)

                yield item
