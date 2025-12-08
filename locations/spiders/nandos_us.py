import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosUSSpider(Spider):
    name = "nandos_us"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    start_urls = ["https://www.nandosperiperi.com/find/post-oak/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in (
            data["props"]["pageProps"]["location"]["restaurants"]
            + data["props"]["pageProps"]["moreLocations"]["restaurants"]
        ):
            if location["status"] == "Hatching Soon":
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = "https://www.nandosperiperi.com/find/{}/".format(location["slug"])
            item["facebook"] = location.get("facebookUrl")

            apply_yes_no(Extras.INDOOR_SEATING, item, "Dine In" in location["amenities"])
            apply_yes_no(Extras.OUTDOOR_SEATING, item, "Patio" in location["amenities"])

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"].values():
                item["opening_hours"].add_range(rule["day"], rule["to"], rule["from"], "%I:%M %p")

            yield item
