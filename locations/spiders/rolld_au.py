import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class RolldAUSpider(Spider):
    name = "rolld_au"
    item_attributes = {"brand": "Roll'd", "brand_wikidata": "Q113114631"}
    start_urls = ["https://sl-front.proguscommerce.com/api/locations?shopId=10052"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)
            if match := re.compile(r"Roll\S{1,3}d (?:Vietnamese )?(.+)").fullmatch(item.pop("name")):
                item["branch"] = match.group(1)
            item["street_address"] = item.pop("addr_full")
            # The feed uses state codes everywhere except one store, which spells the state out.
            item["state"] = {"Northern Territory": "NT"}.get(item["state"], item["state"])

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"].splitlines():
                day, _, times = rule.partition(": ")
                if times == "CLOSED":
                    item["opening_hours"].set_closed(day)
                elif match := re.match(r"(\d{1,2}:\d{2})(?::\d{2})?-(\d{1,2}:\d{2})", times):
                    item["opening_hours"].add_range(day, *match.groups())

            apply_category(Categories.FAST_FOOD, item)
            yield item
