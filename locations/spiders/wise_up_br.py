from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.dict_parser import DictParser


class WiseUpBRSpider(Spider):
    name = "wise_up_br"
    item_attributes = {"brand": "Wise Up", "brand_wikidata": "Q123166153"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://api.wiseup.com/v1/franchises/regions?brand=Wise%20Up&country=BR")

    def parse(self, response, **kwargs):
        for region in response.json():
            code = region.get("region")
            yield JsonRequest(
                url=f"https://api.wiseup.com/v1/franchises/units?country=BR&brand=Wise%20Up&region={code}",
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        for school in response.json():
            item = DictParser.parse(school)
            item["branch"] = item.pop("name")
            item["street_address"] = school.get("addressLine")
            item["housenumber"] = school.get("addressNumber")
            apply_category({"amenity": "language_school"}, item)
            yield item
