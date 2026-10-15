import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BrakeMastersUSSpider(Spider):
    name = "brake_masters_us"
    item_attributes = {"brand": "Brake Masters", "brand_wikidata": "Q4956024"}
    start_urls = ["https://www.stoponadime.com/locations/find-a-location-near-you/"]

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        nonce = re.search(r"\"nonce\":\s*\"(.+)\"", response.text).group(1)
        yield JsonRequest(
            url=f"https://www.stoponadime.com/wp-admin/admin-ajax.php?action=asl_load_stores&nonce={nonce}&load_all=1&layout=1",
            callback=self.parse_details,
        )

    def parse_details(self, response: Response) -> Iterable[JsonRequest]:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(location.get("open_hours"))
                item["opening_hours"] = oh
            except:
                pass
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
