import re
from datetime import datetime

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class NettoSallingDESpider(Spider):
    name = "netto_salling_de"
    item_attributes = {"brand": "Netto", "brand_wikidata": "Q552652"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://api.sallinggroup.com/v2/stores?&country=DE&geo?&radius=100&per_page=1000"
        auth_token = "b1832498-0e22-436c-bd18-9ffa325dd846"
        yield JsonRequest(url=url, headers={"Authorization": f"Bearer {auth_token}"})

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["lon"], item["lat"] = location["coordinates"]
            item["street_address"] = item.pop("street")

            oh = OpeningHours()
            for opening_hours in location.get("hours"):
                if opening_hours["open"] and opening_hours["close"]:
                    open = re.sub(f'{opening_hours["date"]}T', "", opening_hours["open"])
                    close = re.sub(f'{opening_hours["date"]}T', "", opening_hours["close"])
                    day = DAYS[datetime.strptime(opening_hours["date"], "%Y-%m-%d").weekday()]
                    oh.add_ranges_from_string(f"{day} {open}-{close}")
                item["opening_hours"] = oh

            yield item
